"""Real-browser check of the ``quotes_js`` render gate.

The other spider tests assert on request metadata and feed pre-rendered HTML to
the callback, so nothing proves the ``wait_for_selector`` the spider requests
actually holds the parse until a client-side render lands. This module renders
a local fixture in headless Chromium — no network — and checks both halves.

Skipped when no Chromium build is installed (CI deliberately skips
``playwright install``); run ``python -m playwright install chromium`` locally.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Error, Page, sync_playwright
from scrapy.http import HtmlResponse, Request

from myscraper.spiders.quotes_js import QuotesJsSpider

_URL = "https://quotes.toscrape.com/js/"

# Mirrors the /js/ page: an empty container filled by script after a delay, so
# the DOM has no quotes at the moment set_content() returns.
_DEFERRED_RENDER_HTML = """
<html><body>
  <div class="container"></div>
  <script>
    setTimeout(() => {
      document.querySelector(".container").innerHTML = `
        <div class="quote">
          <span class="text">“Deferred quote.”</span>
          <small class="author">Ada Lovelace</small>
          <a class="tag">math</a>
        </div>`;
    }, 300);
  </script>
</body></html>
"""


@pytest.fixture(scope="module")
def browser() -> Iterator[Browser]:
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Error as exc:
            pytest.skip(f"Chromium not installed: {exc.message.splitlines()[0]}")
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    page = browser.new_page()
    yield page
    page.close()


def _spider_wait_selector() -> str:
    """The selector the spider's own request asks Playwright to wait on."""
    request = next(iter(QuotesJsSpider().start_requests()))
    (method,) = request.meta["playwright_page_methods"]
    assert method.method == "wait_for_selector"
    return method.args[0]


def _parse(html: str) -> list[dict]:
    response = HtmlResponse(
        url=_URL, body=html.encode("utf-8"), encoding="utf-8", request=Request(_URL)
    )
    return [r for r in QuotesJsSpider().parse(response) if isinstance(r, dict)]


def test_parse_without_wait_sees_no_quotes(page: Page) -> None:
    page.set_content(_DEFERRED_RENDER_HTML)
    assert _parse(page.content()) == []


def test_spider_wait_selector_gates_on_client_render(page: Page) -> None:
    page.set_content(_DEFERRED_RENDER_HTML)
    page.wait_for_selector(_spider_wait_selector(), timeout=5_000)

    assert _parse(page.content()) == [
        {
            "text": "“Deferred quote.”",
            "author": "Ada Lovelace",
            "tags": ["math"],
            "url": _URL,
        }
    ]
