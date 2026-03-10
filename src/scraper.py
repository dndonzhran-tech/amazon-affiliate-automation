"""Amazon product scraper module."""

import json
import logging
import re
import time
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from src.models import Product
from src.utils import get_env_var

logger = logging.getLogger(__name__)


class AmazonScraper:
    """Scrapes product information from Amazon."""

    BASE_URL = "https://www.amazon.com"
    SEARCH_URL = "https://www.amazon.com/s"

    def __init__(self, affiliate_tag: str = ""):
        self.affiliate_tag = affiliate_tag or get_env_var("AFFILIATE_TAG")
        self.session = requests.Session()
        try:
            ua = UserAgent()
            self.user_agent = ua.random
        except Exception:
            self.user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def search_products(
        self,
        keyword: str,
        category: str = "",
        max_results: int = 10,
        min_price: float = 0,
        max_price: float = 0,
        min_rating: float = 0,
    ) -> list[Product]:
        """Search Amazon for products matching the keyword."""
        params = {"k": keyword}
        if min_price > 0 and max_price > 0:
            params["rh"] = f"p_36:{int(min_price * 100)}-{int(max_price * 100)}"

        products = []
        try:
            response = self.session.get(self.SEARCH_URL, params=params, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            items = soup.select('[data-component-type="s-search-result"]')
            for item in items[:max_results]:
                product = self._parse_search_result(item, category)
                if product:
                    if min_rating > 0 and product.rating and product.rating < min_rating:
                        continue
                    products.append(product)

            logger.info(f"Found {len(products)} products for '{keyword}'")
        except requests.RequestException as e:
            logger.error(f"Error searching products: {e}")

        return products

    def get_product_details(self, asin: str) -> Optional[Product]:
        """Get detailed product information by ASIN."""
        url = f"{self.BASE_URL}/dp/{asin}"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            return self._parse_product_page(soup, asin, url)
        except requests.RequestException as e:
            logger.error(f"Error fetching product {asin}: {e}")
            return None

    def get_bestsellers(self, category_url: str = "", max_results: int = 10) -> list[Product]:
        """Get bestseller products from Amazon."""
        url = category_url or f"{self.BASE_URL}/bestsellers"
        products = []
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            items = soup.select(".zg-item-immersion, .p13n-sc-uncoverable-faceout")
            for item in items[:max_results]:
                product = self._parse_bestseller_item(item)
                if product:
                    products.append(product)

            logger.info(f"Found {len(products)} bestseller products")
        except requests.RequestException as e:
            logger.error(f"Error fetching bestsellers: {e}")

        return products

    def get_deals(self, max_results: int = 10) -> list[Product]:
        """Get current deal products from Amazon."""
        url = f"{self.BASE_URL}/deals"
        products = []
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            items = soup.select('[data-testid="deal-card"],.dealCard')
            for item in items[:max_results]:
                product = self._parse_deal_item(item)
                if product:
                    products.append(product)

            logger.info(f"Found {len(products)} deal products")
        except requests.RequestException as e:
            logger.error(f"Error fetching deals: {e}")

        return products

    def _parse_search_result(self, item, category: str = "") -> Optional[Product]:
        """Parse a search result item into a Product."""
        try:
            # Name
            name_el = item.select_one("h2 a span, .a-text-normal")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                return None

            # URL and ASIN
            link_el = item.select_one("h2 a")
            href = link_el.get("href", "") if link_el else ""
            url = urljoin(self.BASE_URL, href) if href else ""
            asin = item.get("data-asin", "")

            # Price
            price = self._extract_price(item)

            # Rating
            rating_el = item.select_one(".a-icon-star-small .a-icon-alt, [aria-label*='stars']")
            rating = None
            if rating_el:
                rating_text = rating_el.get_text("") or rating_el.get("aria-label", "")
                rating_match = re.search(r"([\d.]+)\s*out", rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))

            # Review count
            review_el = item.select_one('[aria-label*="stars"] + span, .a-size-small .a-link-normal')
            review_count = 0
            if review_el:
                review_text = review_el.get_text(strip=True).replace(",", "")
                review_match = re.search(r"(\d+)", review_text)
                if review_match:
                    review_count = int(review_match.group(1))

            # Image
            img_el = item.select_one("img.s-image")
            image_url = img_el.get("src", "") if img_el else ""

            # Discount
            discount = self._extract_discount(item)

            return Product(
                name=name,
                url=url,
                price=price,
                category=category,
                description=name,
                discount=discount,
                affiliate_tag=self.affiliate_tag,
                image_url=image_url,
                asin=asin,
                rating=rating,
                review_count=review_count,
            )
        except Exception as e:
            logger.debug(f"Error parsing search result: {e}")
            return None

    def _parse_product_page(self, soup, asin: str, url: str) -> Optional[Product]:
        """Parse a product detail page."""
        try:
            name_el = soup.select_one("#productTitle")
            name = name_el.get_text(strip=True) if name_el else ""

            price = 0.0
            price_el = soup.select_one(".a-price .a-offscreen, #priceblock_ourprice, #priceblock_dealprice")
            if price_el:
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"[\d,.]+", price_text.replace(",", ""))
                if price_match:
                    price = float(price_match.group())

            desc_el = soup.select_one("#feature-bullets, #productDescription")
            description = ""
            if desc_el:
                bullets = desc_el.select("li span")
                if bullets:
                    description = ". ".join(b.get_text(strip=True) for b in bullets[:3])
                else:
                    description = desc_el.get_text(strip=True)[:300]

            rating = None
            rating_el = soup.select_one("#acrPopover, .a-icon-star")
            if rating_el:
                rating_text = rating_el.get("title", "") or rating_el.get_text("")
                rating_match = re.search(r"([\d.]+)", rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))

            review_el = soup.select_one("#acrCustomerReviewText")
            review_count = 0
            if review_el:
                review_text = review_el.get_text(strip=True).replace(",", "")
                review_match = re.search(r"(\d+)", review_text)
                if review_match:
                    review_count = int(review_match.group(1))

            img_el = soup.select_one("#landingImage, #imgBlkFront")
            image_url = img_el.get("src", "") if img_el else ""

            cat_el = soup.select_one("#wayfinding-breadcrumbs_container a, .a-breadcrumb a")
            category = cat_el.get_text(strip=True) if cat_el else ""

            return Product(
                name=name,
                url=url,
                price=price,
                category=category,
                description=description,
                affiliate_tag=self.affiliate_tag,
                image_url=image_url,
                asin=asin,
                rating=rating,
                review_count=review_count,
            )
        except Exception as e:
            logger.error(f"Error parsing product page: {e}")
            return None

    def _parse_bestseller_item(self, item) -> Optional[Product]:
        """Parse a bestseller item."""
        try:
            name_el = item.select_one(".p13n-sc-truncate, ._cDEzb_p13n-sc-css-line-clamp-1_1Fn1y")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                return None

            link_el = item.select_one("a.a-link-normal")
            href = link_el.get("href", "") if link_el else ""
            url = urljoin(self.BASE_URL, href) if href else ""
            asin_match = re.search(r"/dp/([A-Z0-9]{10})", href)
            asin = asin_match.group(1) if asin_match else ""

            price = self._extract_price(item)

            img_el = item.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""

            return Product(
                name=name,
                url=url,
                price=price,
                category="Bestseller",
                description=name,
                affiliate_tag=self.affiliate_tag,
                image_url=image_url,
                asin=asin,
            )
        except Exception as e:
            logger.debug(f"Error parsing bestseller item: {e}")
            return None

    def _parse_deal_item(self, item) -> Optional[Product]:
        """Parse a deal item."""
        try:
            name_el = item.select_one(".a-truncate-full, [data-testid='deal-title']")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                return None

            link_el = item.select_one("a")
            href = link_el.get("href", "") if link_el else ""
            url = urljoin(self.BASE_URL, href) if href else ""

            price = self._extract_price(item)
            discount = self._extract_discount(item)

            img_el = item.select_one("img")
            image_url = img_el.get("src", "") if img_el else ""

            return Product(
                name=name,
                url=url,
                price=price,
                category="Deals",
                description=name,
                discount=discount,
                affiliate_tag=self.affiliate_tag,
                image_url=image_url,
            )
        except Exception as e:
            logger.debug(f"Error parsing deal item: {e}")
            return None

    def _extract_price(self, element) -> float:
        """Extract price from an element."""
        price_el = element.select_one(
            ".a-price .a-offscreen, .a-price span[aria-hidden='true'], .a-color-price"
        )
        if price_el:
            price_text = price_el.get_text(strip=True)
            price_match = re.search(r"[\d,.]+", price_text.replace(",", ""))
            if price_match:
                return float(price_match.group())
        return 0.0

    def _extract_discount(self, element) -> Optional[float]:
        """Extract discount percentage from an element."""
        discount_el = element.select_one(".a-text-price + span, .savingsPercentage")
        if discount_el:
            discount_text = discount_el.get_text(strip=True)
            discount_match = re.search(r"(\d+)\s*%", discount_text)
            if discount_match:
                return float(discount_match.group(1))
        return None


def scrape_products(
    keyword: str,
    category: str = "",
    max_results: int = 10,
    min_price: float = 0,
    max_price: float = 0,
    min_rating: float = 0,
) -> list[Product]:
    """Convenience function to scrape products."""
    scraper = AmazonScraper()
    return scraper.search_products(
        keyword=keyword,
        category=category,
        max_results=max_results,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
    )


def scrape_product_by_asin(asin: str) -> Optional[Product]:
    """Convenience function to get product by ASIN."""
    scraper = AmazonScraper()
    return scraper.get_product_details(asin)
