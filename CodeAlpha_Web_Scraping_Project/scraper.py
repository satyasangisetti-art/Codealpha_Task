"""
CodeAlpha Internship - Task 1: Web Scraping
Educational target: https://books.toscrape.com/
This website is specifically intended for practicing web scraping.

Usage:
    python scraper.py
    python scraper.py --max-pages 5
    python scraper.py --details --max-pages 2

Outputs:
    output/books_dataset.csv
    output/scraping_summary.txt
"""

import argparse
import csv
import logging
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://books.toscrape.com/"
OUTPUT_DIR = Path("output")
CSV_PATH = OUTPUT_DIR / "books_dataset.csv"
SUMMARY_PATH = OUTPUT_DIR / "scraping_summary.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("codealpha_scraper")


def create_session():
    """Create a reusable HTTP session with retries for temporary errors."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "CodeAlphaWebScrapingStudentProject/1.0 "
            "(educational use; contact: student@example.com)"
        )
    })
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_soup(session, url):
    """Download a page and parse its HTML."""
    response = session.get(url, timeout=25)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def parse_price(text):
    """Convert a displayed price such as '£51.77' into a numeric value."""
    match = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
    return float(match.group(1)) if match else None


def parse_book_card(card, page_url):
    """Extract fields available on a listing page."""
    title_link = card.select_one("h3 a")
    price_tag = card.select_one(".price_color")
    availability_tag = card.select_one(".availability")
    rating_tag = card.select_one("p.star-rating")
    image_tag = card.select_one("img")

    title = title_link.get("title", "").strip() if title_link else ""
    product_url = urljoin(page_url, title_link.get("href", "")) if title_link else ""
    image_url = urljoin(page_url, image_tag.get("src", "")) if image_tag else ""

    rating = None
    if rating_tag:
        rating_classes = rating_tag.get("class", [])
        rating_words = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        for word, value in rating_words.items():
            if word in rating_classes:
                rating = value
                break

    availability = (
        " ".join(availability_tag.stripped_strings)
        if availability_tag else ""
    )

    return {
        "title": title,
        "price_gbp": parse_price(price_tag.get_text(" ", strip=True)) if price_tag else None,
        "availability": availability,
        "rating_out_of_5": rating,
        "product_url": product_url,
        "image_url": image_url,
        "listing_page_url": page_url,
    }


def scrape_book_details(session, product_url):
    """Optionally visit each product page to collect extra fields."""
    soup = get_soup(session, product_url)
    description = ""
    description_header = soup.find(id="product_description")
    if description_header:
        description_tag = description_header.find_next_sibling("p")
        if description_tag:
            description = description_tag.get_text(" ", strip=True)

    upc = ""
    category = ""
    breadcrumb = soup.select("ul.breadcrumb li a")
    if len(breadcrumb) >= 3:
        category = breadcrumb[-1].get_text(" ", strip=True)

    for row in soup.select("table.table-striped tr"):
        header = row.find("th")
        value = row.find("td")
        if header and value and header.get_text(strip=True).lower() == "upc":
            upc = value.get_text(strip=True)
            break

    return {
        "category": category,
        "upc": upc,
        "description": description,
    }


def find_next_page(soup, current_url):
    """Resolve the site's 'next' pagination link, if present."""
    next_link = soup.select_one("li.next a")
    if not next_link:
        return None
    return urljoin(current_url, next_link.get("href", ""))


def scrape(max_pages=None, include_details=False, delay=0.5):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    session = create_session()
    current_url = BASE_URL
    records = []
    visited = set()
    page_count = 0

    while current_url and current_url not in visited:
        if max_pages is not None and page_count >= max_pages:
            break

        logger.info("Scraping listing page: %s", current_url)
        visited.add(current_url)
        soup = get_soup(session, current_url)
        cards = soup.select("article.product_pod")

        if not cards:
            logger.warning("No book cards found on %s; stopping.", current_url)
            break

        for card in cards:
            record = parse_book_card(card, current_url)
            if not record["title"]:
                continue

            if include_details and record["product_url"]:
                try:
                    time.sleep(delay)
                    record.update(scrape_book_details(session, record["product_url"]))
                except requests.RequestException as exc:
                    logger.warning("Could not fetch product detail %s: %s",
                                   record["product_url"], exc)
                    record.update({"category": "", "upc": "", "description": ""})
            else:
                record.update({"category": "", "upc": "", "description": ""})

            records.append(record)

        page_count += 1
        current_url = find_next_page(soup, current_url)
        if current_url:
            time.sleep(delay)

    if not records:
        raise RuntimeError(
            "No records were scraped. Check your internet connection and target HTML."
        )

    # Remove duplicate product URLs while preserving order.
    unique_records = []
    seen_urls = set()
    for record in records:
        key = record["product_url"]
        if key and key in seen_urls:
            continue
        if key:
            seen_urls.add(key)
        unique_records.append(record)

    fieldnames = [
        "title", "price_gbp", "availability", "rating_out_of_5",
        "category", "upc", "description", "product_url", "image_url",
        "listing_page_url"
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_records)

    prices = [r["price_gbp"] for r in unique_records if r["price_gbp"] is not None]
    summary = [
        "CodeAlpha Internship — Task 1: Web Scraping",
        f"Target: {BASE_URL}",
        f"Listing pages visited: {page_count}",
        f"Unique book records saved: {len(unique_records)}",
        f"Records with a parsed price: {len(prices)}",
        f"Average listed price (GBP): {sum(prices) / len(prices):.2f}" if prices else
        "Average listed price (GBP): unavailable",
        f"CSV output: {CSV_PATH.as_posix()}",
        f"Product detail scraping enabled: {include_details}",
        "",
        "Note: This summary describes this run only. Re-run the scraper to refresh data."
    ]
    SUMMARY_PATH.write_text("\n".join(summary), encoding="utf-8")
    logger.info("Saved %d records to %s", len(unique_records), CSV_PATH)
    logger.info("Saved run summary to %s", SUMMARY_PATH)
    return unique_records


def main():
    parser = argparse.ArgumentParser(description="Scrape Books to Scrape for the CodeAlpha task.")
    parser.add_argument("--max-pages", type=int, default=None,
                        help="Maximum listing pages to visit (default: all available pages).")
    parser.add_argument("--details", action="store_true",
                        help="Visit each product page for category, UPC, and description. Slower.")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Delay in seconds between requests (default: 0.5).")
    args = parser.parse_args()

    if args.max_pages is not None and args.max_pages < 1:
        parser.error("--max-pages must be at least 1.")
    if args.delay < 0:
        parser.error("--delay cannot be negative.")

    try:
        scrape(max_pages=args.max_pages, include_details=args.details, delay=args.delay)
    except requests.RequestException as exc:
        logger.error("Network/request error: %s", exc)
        raise SystemExit(1)
    except Exception as exc:
        logger.error("Scraping failed: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
