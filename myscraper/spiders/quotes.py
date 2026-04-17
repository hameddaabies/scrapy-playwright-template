"""Example spider — quotes.toscrape.com.

A public practice site with structured quotes, authors, and tags.
Extracts quote text, author name, tags, and the page URL it was found on.

Run with:
    scrapy crawl quotes -O output/quotes.jsonl
"""

from __future__ import annotations

from urllib.parse import urljoin

import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/"]

    def parse(self, response):
        for quote in response.css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get("").strip(),
                "author": quote.css("small.author::text").get("").strip(),
                "tags": quote.css("a.tag::text").getall(),
                "url": response.url,
            }

        next_href = response.css("li.next a::attr(href)").get()
        if next_href:
            yield scrapy.Request(urljoin(response.url, next_href), callback=self.parse)
