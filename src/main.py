"""Main CLI application for Amazon Affiliate Automation."""

import json
import logging
import sys

import click
from rich.console import Console
from rich.table import Table

from src.content_generator import ContentGenerator
from src.database import Database
from src.models import Campaign, Product, init_db
from src.scheduler import AutomationScheduler
from src.scraper import AmazonScraper, scrape_products
from src.social.telegram import TelegramPoster
from src.social.twitter import TwitterPoster
from src.utils import get_env_var

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@click.group()
@click.option("--db", default="sqlite:///affiliate.db", help="Database URL")
@click.pass_context
def cli(ctx, db):
    """Amazon Affiliate Automation - Full automation tool."""
    ctx.ensure_object(dict)
    ctx.obj["db_url"] = db
    init_db(db)


# ─── SCRAPE COMMANDS ────────────────────────────────────────────


@cli.command()
@click.argument("keyword")
@click.option("--max-results", "-n", default=10, help="Max number of results")
@click.option("--category", "-c", default="", help="Product category")
@click.option("--min-price", default=0.0, help="Minimum price filter")
@click.option("--max-price", default=0.0, help="Maximum price filter")
@click.option("--min-rating", default=0.0, help="Minimum rating filter")
@click.option("--save/--no-save", default=True, help="Save to database")
@click.option("--output", "-o", default="", help="Save results to JSON file")
@click.pass_context
def scrape(ctx, keyword, max_results, category, min_price, max_price, min_rating, save, output):
    """Scrape Amazon products by keyword."""
    console.print(f"[bold blue]Searching Amazon for:[/] {keyword}")

    products = scrape_products(
        keyword=keyword,
        category=category,
        max_results=max_results,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
    )

    if not products:
        console.print("[yellow]No products found.[/]")
        return

    table = Table(title=f"Found {len(products)} Products")
    table.add_column("ASIN", style="cyan")
    table.add_column("Name", style="white", max_width=50)
    table.add_column("Price", style="green")
    table.add_column("Rating", style="yellow")
    table.add_column("Discount", style="red")

    for p in products:
        table.add_row(
            p.asin or "N/A",
            p.name[:50],
            f"${p.price:.2f}" if p.price else "N/A",
            f"{p.rating}" if p.rating else "N/A",
            f"{p.discount:.0f}%" if p.discount else "-",
        )

    console.print(table)

    if save:
        db = Database(ctx.obj["db_url"])
        ids = db.save_products(products)
        console.print(f"[green]Saved {len(ids)} products to database[/]")

    if output:
        data = [p.to_dict() for p in products]
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"[green]Results saved to {output}[/]")


# ─── GENERATE COMMANDS ──────────────────────────────────────────


@cli.command()
@click.option("--products", "-p", default="", help="Products JSON file")
@click.option("--keyword", "-k", default="", help="Scrape products by keyword")
@click.option("--platform", default="twitter", type=click.Choice(["twitter", "telegram"]))
@click.option("--language", "-l", default="en", type=click.Choice(["en", "ar"]))
@click.option("--scenario", "-s", default="product_review",
              type=click.Choice(["product_review", "deal_alert", "comparison", "recommendation", "rotate"]))
@click.option("--output", "-o", default="", help="Output JSON file")
@click.option("--max-products", "-n", default=5, help="Max products to use")
@click.pass_context
def generate(ctx, products, keyword, platform, language, scenario, output, max_products):
    """Generate social media posts."""
    product_list = []

    if products:
        product_list = _load_products_file(products)
    elif keyword:
        console.print(f"[blue]Scraping products for: {keyword}[/]")
        product_list = scrape_products(keyword=keyword, max_results=max_products)
    else:
        db = Database(ctx.obj["db_url"])
        db_products = db.get_all_products()
        for dbp in db_products[:max_products]:
            product_list.append(Product(
                name=dbp.name, url=dbp.url, price=dbp.price,
                category=dbp.category, description=dbp.description,
                discount=dbp.discount, image_url=dbp.image_url or "",
                asin=dbp.asin or "",
                affiliate_tag=get_env_var("AFFILIATE_TAG"),
            ))

    if not product_list:
        console.print("[yellow]No products found. Use --products, --keyword, or scrape first.[/]")
        return

    generator = ContentGenerator(language=language)
    posts = generator.generate_batch(product_list, platform=platform, scenario=scenario)

    console.print(f"\n[bold green]Generated {len(posts)} posts for {platform}[/]\n")

    output_data = []
    for i, post in enumerate(posts, 1):
        console.print(f"[bold]--- Post {i} ---[/]")
        console.print(post.full_text)
        console.print()
        output_data.append({
            "post_number": i,
            "content": post.full_text,
            "product": post.product.to_dict(),
            "platform": post.platform,
            "language": post.language,
        })

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        console.print(f"[green]Posts saved to {output}[/]")


# ─── POST COMMANDS ──────────────────────────────────────────────


@cli.command()
@click.option("--products", "-p", default="", help="Products JSON file")
@click.option("--keyword", "-k", default="", help="Scrape products by keyword")
@click.option("--platform", default="twitter", type=click.Choice(["twitter", "telegram"]))
@click.option("--language", "-l", default="en", type=click.Choice(["en", "ar"]))
@click.option("--scenario", "-s", default="product_review",
              type=click.Choice(["product_review", "deal_alert", "comparison", "recommendation"]))
@click.option("--max-products", "-n", default=1, help="Number of products to post")
@click.pass_context
def post(ctx, products, keyword, platform, language, scenario, max_products):
    """Generate and post content to social media."""
    product_list = []

    if products:
        product_list = _load_products_file(products)[:max_products]
    elif keyword:
        product_list = scrape_products(keyword=keyword, max_results=max_products)
    else:
        db = Database(ctx.obj["db_url"])
        db_products = db.get_all_products()
        for dbp in db_products[:max_products]:
            product_list.append(Product(
                name=dbp.name, url=dbp.url, price=dbp.price,
                category=dbp.category, description=dbp.description,
                discount=dbp.discount, image_url=dbp.image_url or "",
                asin=dbp.asin or "",
                affiliate_tag=get_env_var("AFFILIATE_TAG"),
            ))

    if not product_list:
        console.print("[yellow]No products found.[/]")
        return

    generator = ContentGenerator(language=language)
    db = Database(ctx.obj["db_url"])

    for product in product_list:
        gen_post = generator.generate_post(product, platform=platform, scenario=scenario)
        console.print(f"\n[bold]Posting to {platform}:[/]")
        console.print(gen_post.full_text)

        result = None
        if platform == "twitter":
            poster = TwitterPoster()
            if not poster.is_configured():
                console.print("[red]Twitter not configured. Set TWITTER_* env vars.[/]")
                return
            result = poster.post_tweet(gen_post.full_text)
        elif platform == "telegram":
            poster = TelegramPoster()
            if not poster.is_configured():
                console.print("[red]Telegram not configured. Set TELEGRAM_* env vars.[/]")
                return
            result = poster.send_product_post(
                product_name=product.name,
                description=product.description,
                price=product.price,
                affiliate_url=product.affiliate_url,
                image_url=product.image_url,
                discount=product.discount,
                language=language,
            )

        if result:
            console.print(f"[green]Posted successfully! ID: {result.get('id')}[/]")
            db.save_post(gen_post, posted=True)
        else:
            console.print("[red]Failed to post.[/]")
            db.save_post(gen_post, posted=False)


# ─── SCHEDULE COMMANDS ──────────────────────────────────────────


@cli.group()
def schedule_cmd():
    """Manage scheduled automation tasks."""
    pass


@schedule_cmd.command("add")
@click.argument("name")
@click.option("--interval", "-i", required=True, type=int, help="Interval in minutes")
@click.option("--platform", default="twitter", type=click.Choice(["twitter", "telegram"]))
@click.option("--language", "-l", default="en", type=click.Choice(["en", "ar"]))
@click.option("--scenario", "-s", default="product_review")
@click.option("--category", "-c", default="", help="Product category to search")
@click.pass_context
def schedule_add(ctx, name, interval, platform, language, scenario, category):
    """Add a new scheduled task."""
    scheduler = AutomationScheduler(ctx.obj["db_url"])
    scheduler.add_schedule(
        name=name,
        interval_minutes=interval,
        platform=platform,
        language=language,
        scenario=scenario,
        category=category,
    )
    console.print(f"[green]Schedule '{name}' added: every {interval} min on {platform}[/]")


@schedule_cmd.command("list")
@click.pass_context
def schedule_list(ctx):
    """List all scheduled tasks."""
    scheduler = AutomationScheduler(ctx.obj["db_url"])
    schedules = scheduler.list_schedules()

    if not schedules:
        console.print("[yellow]No schedules found.[/]")
        return

    table = Table(title="Scheduled Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Interval", style="green")
    table.add_column("Platform", style="blue")
    table.add_column("Language", style="yellow")
    table.add_column("Active", style="red")
    table.add_column("Last Run")

    for s in schedules:
        table.add_row(
            str(s["id"]),
            s["name"],
            f"{s['interval_minutes']} min",
            s["platform"],
            s["language"],
            "Yes" if s["is_active"] else "No",
            s["last_run"] or "Never",
        )

    console.print(table)


@schedule_cmd.command("remove")
@click.argument("schedule_id", type=int)
@click.pass_context
def schedule_remove(ctx, schedule_id):
    """Remove a scheduled task."""
    scheduler = AutomationScheduler(ctx.obj["db_url"])
    if scheduler.remove_schedule(schedule_id):
        console.print(f"[green]Schedule {schedule_id} removed.[/]")
    else:
        console.print(f"[red]Schedule {schedule_id} not found.[/]")


@schedule_cmd.command("run")
@click.option("--once", is_flag=True, help="Run all tasks once then exit")
@click.pass_context
def schedule_run(ctx, once):
    """Start the scheduler."""
    scheduler = AutomationScheduler(ctx.obj["db_url"])
    if once:
        console.print("[blue]Running all tasks once...[/]")
        scheduler.run_once()
    else:
        console.print("[blue]Starting scheduler...[/]")
        scheduler.run()


# ─── DATABASE COMMANDS ──────────────────────────────────────────


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    db = Database(ctx.obj["db_url"])
    s = db.get_stats()

    table = Table(title="Database Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Products", str(s["total_products"]))
    table.add_row("Active Products", str(s["active_products"]))
    table.add_row("Total Posts", str(s["total_posts"]))
    table.add_row("Posted", str(s["posted_count"]))
    table.add_row("Pending", str(s["pending_count"]))

    console.print(table)


@cli.command()
@click.option("--category", "-c", default="", help="Filter by category")
@click.option("--limit", "-n", default=20, help="Max results")
@click.pass_context
def products(ctx, category, limit):
    """List products in the database."""
    db = Database(ctx.obj["db_url"])
    if category:
        db_products = db.search_products(category=category)
    else:
        db_products = db.get_all_products()

    db_products = db_products[:limit]

    if not db_products:
        console.print("[yellow]No products found in database.[/]")
        return

    table = Table(title=f"Products ({len(db_products)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white", max_width=40)
    table.add_column("Price", style="green")
    table.add_column("Category", style="blue")
    table.add_column("ASIN", style="yellow")

    for p in db_products:
        table.add_row(
            str(p.id),
            p.name[:40] if p.name else "N/A",
            f"${p.price:.2f}",
            p.category or "N/A",
            p.asin or "N/A",
        )

    console.print(table)


@cli.command()
@click.option("--platform", "-p", default="", help="Filter by platform")
@click.option("--pending", is_flag=True, help="Show only pending posts")
@click.option("--limit", "-n", default=20, help="Max results")
@click.pass_context
def posts(ctx, platform, pending, limit):
    """List generated posts."""
    db = Database(ctx.obj["db_url"])
    posted_filter = False if pending else None
    db_posts = db.get_posts(platform=platform, posted=posted_filter, limit=limit)

    if not db_posts:
        console.print("[yellow]No posts found.[/]")
        return

    table = Table(title=f"Posts ({len(db_posts)})")
    table.add_column("ID", style="cyan")
    table.add_column("Platform", style="blue")
    table.add_column("Content", style="white", max_width=60)
    table.add_column("Posted", style="green")
    table.add_column("Created", style="yellow")

    for p in db_posts:
        table.add_row(
            str(p.id),
            p.platform,
            (p.content[:60] + "...") if len(p.content) > 60 else p.content,
            "Yes" if p.posted else "No",
            str(p.created_at)[:16] if p.created_at else "N/A",
        )

    console.print(table)


# ─── HELPERS ────────────────────────────────────────────────────


def _load_products_file(filepath: str) -> list[Product]:
    """Load products from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    affiliate_tag = get_env_var("AFFILIATE_TAG")
    products = []
    for item in data.get("products", []):
        products.append(Product(
            name=item["name"],
            url=item["url"],
            price=item["price"],
            category=item.get("category", ""),
            description=item.get("description", ""),
            discount=item.get("discount"),
            affiliate_tag=affiliate_tag,
        ))
    return products


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
