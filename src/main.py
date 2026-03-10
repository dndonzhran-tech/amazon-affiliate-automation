"""التطبيق الرئيسي - نقطة الدخول."""

import argparse
import logging
import sys

from src.config import DEFAULT_LANGUAGE
from src.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_server(args):
    """تشغيل API Server."""
    from src.api_server import run_server
    run_server(host=args.host, port=args.port, debug=args.debug)


def cmd_scheduler(args):
    """تشغيل المجدول المستقل."""
    from src.scheduler.scheduler import start_scheduler
    start_scheduler()


def cmd_generate(args):
    """توليد محتوى لمنتج."""
    from src.content.ai_generator import generate_content

    product = {
        "asin": args.asin or "MANUAL",
        "name": args.name,
        "price": args.price or 0,
        "currency": "USD",
        "description": args.description or "",
        "affiliate_link": args.url or "",
        "rating": args.rating or 0,
        "review_count": 0,
        "discount": args.discount,
        "features": [],
        "category": args.category or "",
        "use_case": args.use_case or "",
    }

    posts = generate_content(
        product,
        language=args.lang,
        content_types=args.types.split(",") if args.types else None,
    )

    for i, post in enumerate(posts, 1):
        print(f"\n{'='*50}")
        print(f"📝 منشور {i} [{post['content_type']}]")
        print(f"{'='*50}")
        content = post["content"]
        tags = " ".join(post.get("hashtags", []))
        if tags:
            print(f"{content}\n\n{tags}")
        else:
            print(content)

    if args.save:
        from src.database import save_post
        for post in posts:
            post_id = save_post(post)
            print(f"\n✅ تم حفظ المنشور #{post_id}")


def cmd_publish(args):
    """نشر المنشورات المعلقة."""
    from src.database import get_pending_posts
    from src.social.publisher import publish_post

    posts = get_pending_posts(limit=args.count)
    if not posts:
        print("لا توجد منشورات معلقة للنشر")
        return

    platforms = args.platforms.split(",") if args.platforms else None

    for post in posts:
        print(f"\nنشر المنشور #{post['id']}...")
        result = publish_post(post, platforms)
        for platform, res in result.get("results", {}).items():
            status = "✅" if res.get("success") else "❌"
            print(f"  {status} {platform}: {res}")


def cmd_status(args):
    """حالة النظام."""
    from src.database import get_daily_stats
    from src.social.publisher import get_platform_status

    platforms = get_platform_status()
    stats = get_daily_stats()

    print("\n📊 حالة النظام")
    print("=" * 40)
    print(f"\n🔗 المنصات:")
    for name, configured in platforms.items():
        status = "✅ مُعد" if configured else "❌ غير مُعد"
        print(f"  {name}: {status}")

    print(f"\n📈 إحصائيات اليوم ({stats['date']}):")
    print(f"  منشورات: {stats['posts_today']}")
    print(f"  مشاهدات: {stats['impressions']}")
    print(f"  نقرات: {stats['clicks']}")
    print(f"  أرباح مقدرة: ${stats['estimated_revenue']}")


def cmd_init(args):
    """تهيئة المشروع."""
    init_db()
    print("✅ تم تهيئة قاعدة البيانات")

    from src.social.publisher import get_platform_status
    platforms = get_platform_status()
    unconfigured = [k for k, v in platforms.items() if not v]
    if unconfigured:
        print(f"\n⚠️ المنصات التالية تحتاج إعداد في .env:")
        for p in unconfigured:
            print(f"  - {p}")
    print("\n🚀 المشروع جاهز! شغّل الخادم بـ: python -m src.main server")


def main():
    parser = argparse.ArgumentParser(
        description="🚀 نظام أتمتة التسويق بالعمولة على أمازون",
    )
    subparsers = parser.add_subparsers(dest="command", help="الأوامر المتاحة")

    # أمر server
    sp_server = subparsers.add_parser("server", help="تشغيل API Server")
    sp_server.add_argument("--host", default="0.0.0.0")
    sp_server.add_argument("--port", type=int, default=8000)
    sp_server.add_argument("--debug", action="store_true")
    sp_server.set_defaults(func=cmd_server)

    # أمر scheduler
    sp_sched = subparsers.add_parser("scheduler", help="تشغيل المجدول")
    sp_sched.set_defaults(func=cmd_scheduler)

    # أمر generate
    sp_gen = subparsers.add_parser("generate", help="توليد محتوى")
    sp_gen.add_argument("--name", required=True, help="اسم المنتج")
    sp_gen.add_argument("--url", help="رابط أمازون")
    sp_gen.add_argument("--asin", help="ASIN المنتج")
    sp_gen.add_argument("--description", help="وصف المنتج")
    sp_gen.add_argument("--category", help="الفئة")
    sp_gen.add_argument("--price", type=float, help="السعر")
    sp_gen.add_argument("--rating", type=float, help="التقييم")
    sp_gen.add_argument("--discount", type=int, help="الخصم %")
    sp_gen.add_argument("--use-case", help="حالة الاستخدام")
    sp_gen.add_argument("--lang", default=DEFAULT_LANGUAGE, choices=["ar", "en"])
    sp_gen.add_argument("--types", help="أنواع المحتوى (مفصولة بفاصلة)")
    sp_gen.add_argument("--save", action="store_true", help="حفظ في قاعدة البيانات")
    sp_gen.set_defaults(func=cmd_generate)

    # أمر publish
    sp_pub = subparsers.add_parser("publish", help="نشر المنشورات المعلقة")
    sp_pub.add_argument("--count", type=int, default=1, help="عدد المنشورات")
    sp_pub.add_argument("--platforms", help="المنصات (مفصولة بفاصلة)")
    sp_pub.set_defaults(func=cmd_publish)

    # أمر status
    sp_status = subparsers.add_parser("status", help="حالة النظام")
    sp_status.set_defaults(func=cmd_status)

    # أمر init
    sp_init = subparsers.add_parser("init", help="تهيئة المشروع")
    sp_init.set_defaults(func=cmd_init)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
