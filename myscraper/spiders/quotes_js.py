"""Example spider — quotes.toscrape.com/js/, rendered by Playwright.

The plain-HTTP variant of this site ships the quotes in the HTML; the ``/js/``
variant ships an empty container plus a ``var data = [...]`` script and builds
the DOM client-side, so a fetch without a browser returns zero quotes. This
spider is the template's worked example of the Playwright path: it sets
``meta={"playwright": True}`` to route the request through the Playwright
download handler and waits on ``div.quote`` before the callback reads the DOM.

Waiting is not optional. ``page.goto()`` resolves on the navigation event, which
can land before the client-side render finishes, so a callback that parses
immediately sees an empty page intermittently. ``PageMethod("wait_for_selector",
...)`` pins the callback to a DOM state the parser can rely on instead.

Yields the same ``QuoteItem`` schema as the non-JS ``quotes`` spider, so the two
are directly comparable.

Run with:
    scrapy crawl quotes_js -O output/quotes_js.jsonl
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from urllib.parse import urljoin

import scrapy
from scrapy_playwright.page import PageMethod


class QuotesJsSpider(scrapy.Spider):
    name = "quotes_js"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/js/"]

    def _render_request(self, url: str) -> scrapy.Request:
        """Build a request routed through Playwright and gated on the render.

        ``playwright_include_page`` is left off: the page methods below run
        inside the handler, and handing the callback a live page object would
        make it responsible for closing it.
        """
        return scrapy.Request(
            url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div.quote"),
                ],
            },
        )

    async def start(self) -> AsyncIterator[scrapy.Request]:
        """Seed the crawl (Scrapy >= 2.13).

        The start URLs must be built here, not left to the default
        implementation: that one yields a plain ``Request`` per ``start_urls``
        entry, which fetches the un-rendered HTML and parses zero quotes. On
        Scrapy >= 2.13 ``start()`` is the entry point and the deprecated
        ``start_requests()`` below is no longer consulted, so both are defined
        to keep the template working across the supported version range.
        """
        for request in self.start_requests():
            yield request

    def start_requests(self) -> Iterator[scrapy.Request]:
        """Seed the crawl (Scrapy < 2.13)."""
        for url in self.start_urls:
            yield self._render_request(url)

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
            yield self._render_request(urljoin(response.url, next_href))
