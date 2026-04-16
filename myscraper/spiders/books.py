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
        price_str = response.css("p.price_color::text").get("")
        match = re.search(r"(\d+\.\d+)", price_str)
        price_gbp = float(match.group(1)) if match else 0.0

        availability = response.css("p.availability::text").getall()
        in_stock = any("In stock" in line for line in availability)

        rating_class = response.css("p.star-rating::attr(class)").get("")
        rating_word = rating_class.replace("star-rating", "").strip()
        rating = RATING_WORDS.get(rating_word, 1)

        yield {
            "title": title,
            "price_gbp": price_gbp,
            "in_stock": in_stock,
            "rating": rating,
            "url": response.url,
        }
