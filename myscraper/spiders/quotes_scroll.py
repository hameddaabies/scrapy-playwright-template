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
# pause adds no quotes. ``max_rounds`` bounds the loop if the page never settles;
# ``settled`` reports which of the two ended it, so a cut-off render is visible.
SCROLL_UNTIL_STABLE_JS = """
async ({ selector, pauseMs, maxRounds }) => {
  let previous = -1;
  for (let round = 0; round < maxRounds; round++) {
    const count = document.querySelectorAll(selector).length;
    if (count === previous) return { settled: true, count };
    previous = count;
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise((resolve) => setTimeout(resolve, pauseMs));
  }
  return { settled: false, count: document.querySelectorAll(selector).length };
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

    def parse(self, response):
        """Warn when the scroll loop hit ``max_scroll_rounds`` before settling.

        scrapy-playwright stores each ``PageMethod``'s return value on its
        ``result`` attribute. An unsettled loop means more quotes were still
        loading, so the items below are a truncated set, not the full page.
        """
        methods = response.meta.get("playwright_page_methods") or []
        scroll = methods[-1].result if methods else None
        if isinstance(scroll, dict) and not scroll.get("settled", True):
            self.logger.warning(
                "Scroll loop hit max_scroll_rounds=%d before %s settled; "
                "parsing a possibly truncated set of %d quotes",
                self.max_scroll_rounds,
                response.url,
                scroll.get("count", 0),
            )
        yield from super().parse(response)
