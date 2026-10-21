"""Example spider — quotes.toscrape.com/scroll, an infinite-scroll page.

The page loads ten quotes, then fetches the next batch only when the viewport
nears the bottom; there is no "next" link to follow. ``wait_for_selector`` alone
would parse just the first batch, so the render also runs a scroll loop in the
page that keeps scrolling until the quote count stops growing.

Yields the same ``QuoteItem`` schema as ``quotes`` and ``quotes_js``.

Run with:
    scrapy crawl quotes_scroll -O output/quotes_scroll.jsonl
"""

from __future__ import annotations

import scrapy
from scrapy_playwright.page import PageMethod

from myscraper.spiders.quotes_js import QuotesJsSpider

# Scroll to the bottom, give the next batch time to land, and stop once a full
# pause adds no quotes. ``max_rounds`` bounds the loop if the page never settles.
SCROLL_UNTIL_STABLE_JS = """
async ({ selector, pauseMs, maxRounds }) => {
  let previous = -1;
  for (let round = 0; round < maxRounds; round++) {
    const count = document.querySelectorAll(selector).length;
    if (count === previous) break;
    previous = count;
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise((resolve) => setTimeout(resolve, pauseMs));
  }
  return previous;
}
"""


class QuotesScrollSpider(QuotesJsSpider):
    name = "quotes_scroll"
    start_urls = ["https://quotes.toscrape.com/scroll"]

    scroll_pause_ms = 1000
    max_scroll_rounds = 30

    def _render_request(self, url: str) -> scrapy.Request:
        """Wait for the first batch, then scroll until no new quotes load."""
        return scrapy.Request(
            url,
            callback=self.parse,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "div.quote"),
                    PageMethod(
                        "evaluate",
                        SCROLL_UNTIL_STABLE_JS,
                        {
                            "selector": "div.quote",
                            "pauseMs": self.scroll_pause_ms,
                            "maxRounds": self.max_scroll_rounds,
                        },
                    ),
                ],
            },
        )
