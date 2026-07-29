"""Example spider — books.toscrape.com.

A public practice site explicitly intended for scraping tutorials.
Extracts title, price, stock status, rating, and URL for every book.

Run with:
    scrapy crawl books -O output/books.jsonl
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

import scrapy

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def parse_price(text: str) -> float:
    """Parse a price from a currency string, tolerating thousands separators.

    Strips the leading currency symbol and digit-group commas before parsing,
    so a four-figure price such as ``"£1,234.56"`` yields ``1234.56`` instead of
    truncating to ``234.56`` (a naive ``\\d+\\.\\d+`` match starts at the comma).
    The fractional part is optional, so a whole-number price such as ``"£52"``
    yields ``52.0`` rather than falling through to the missing-price default.
    Returns ``0.0`` when no numeric price is found, so a missing price degrades
    gracefully rather than crashing the parse.
    """
    match = re.search(r"\d[\d,]*(?:\.\d+)?", text)
    if not match:
        return 0.0
    return float(match.group(0).replace(",", ""))


def parse_rating(class_attr: str) -> int | None:
    """Parse a 1-5 star rating from a ``star-rating`` class attribute.

    Returns ``None`` when the word after ``star-rating`` is absent or not one
    of One-Five. An unreadable rating must stay distinguishable from a genuine
    one-star book: defaulting to ``1`` would make a renamed class or a missing
    element indistinguishable from real data, and the fabricated value would
    pass schema validation unnoticed.
    """
    rating_word = class_attr.replace("star-rating", "").strip()
    return RATING_WORDS.get(rating_word)


class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response):
        for card in response.css("article.product_pod"):
            rel_url = card.css("h3 a::attr(href)").get()
            detail_url = urljoin(response.url, rel_url) if rel_url else None
            if detail_url:
                yield scrapy.Request(detail_url, callback=self.parse_detail)

        next_href = response.css("li.next a::attr(href)").get()
        if next_href:
            yield scrapy.Request(urljoin(response.url, next_href), callback=self.parse)

    def parse_detail(self, response):
        title = response.css("div.product_main h1::text").get("").strip()
        price_gbp = parse_price(response.css("p.price_color::text").get(""))

        availability = response.css("p.availability::text").getall()
        in_stock = any("In stock" in line for line in availability)

        rating = parse_rating(response.css("p.star-rating::attr(class)").get(""))

        yield {
            "title": title,
            "price_gbp": price_gbp,
            "in_stock": in_stock,
            "rating": rating,
            "url": response.url,
        }
