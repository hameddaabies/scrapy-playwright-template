"""Scrapy settings.

Polite by default. Flip knobs (concurrency, delay, playwright flag per-request)
per spider or per call as needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from playwright.async_api import Request as PlaywrightRequest

load_dotenv()

BOT_NAME = "myscraper"
SPIDER_MODULES = ["myscraper.spiders"]
NEWSPIDER_MODULE = "myscraper.spiders"

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1.0

# Autothrottle — respectful, adaptive.
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Per-domain throttle overrides — pin a tighter concurrency / longer delay on
# specific hosts without slowing the whole crawl. Useful when one upstream is
# strict (small marketing site, rate-limited API) while the rest of the run is
# polite default. Keys are the request slot — for plain HTTP, Scrapy uses the
# hostname by default. Uncomment and tune per target.
#
# DOWNLOAD_SLOTS = {
#     "books.toscrape.com": {"concurrency": 1, "delay": 2.0, "randomize_delay": True},
#     "quotes.toscrape.com": {"concurrency": 4, "delay": 0.5},
# }

# Retries on transient errors.
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 522, 524, 408]

# Playwright download handler. Request with meta={"playwright": True} to use.
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30_000

# Subresource types to drop before they hit the network. A rendered page pulls
# every image, font and video the browser would show a human, none of which the
# parser reads — on an image-heavy listing page that is the bulk of the bytes and
# most of the wall-clock. Stylesheets are deliberately kept: waits like
# ``wait_for_selector`` resolve on element visibility, which CSS decides, so
# dropping them makes renders flaky. Add "script" only for pages whose content
# is server-rendered — on a JS-rendered target it aborts the render itself.
PLAYWRIGHT_ABORT_RESOURCE_TYPES = frozenset({"image", "font", "media"})


def should_abort_request(request: PlaywrightRequest) -> bool:
    """Return True for in-page requests whose bytes the parser never needs.

    The Playwright handler calls this for every request the page makes and
    aborts the flagged ones. Tune via ``PLAYWRIGHT_ABORT_RESOURCE_TYPES`` above,
    or extend the body to match on ``request.url`` for analytics/ad hosts.
    """
    return request.resource_type in PLAYWRIGHT_ABORT_RESOURCE_TYPES


PLAYWRIGHT_ABORT_REQUEST = should_abort_request

# Middlewares.
DOWNLOADER_MIDDLEWARES = {
    "myscraper.middlewares.RotateUserAgentMiddleware": 400,
    "myscraper.middlewares.ProxyMiddleware": 410,
    # Seeds a raw Cookie header from the COOKIE_HEADER env var. Enable when
    # scraping pages that require a logged-in session, a cookie consent token,
    # or a Cloudflare clearance cookie — paste the header from browser DevTools
    # into .env and uncomment.
    # "myscraper.middlewares.CookieHeaderMiddleware": 420,
    # Drops requests whose URL matches a regex in URL_DENY_PATTERNS (comma-
    # separated). Scopes the crawl by path where allowed_domains scopes by host
    # — prune cart/login/tracking or faceted-filter URLs. Runs early so dropped
    # requests never reach the network. Uncomment to enable.
    # "myscraper.middlewares.UrlDenyPatternMiddleware": 390,
}

# Cap how deep link-following recurses from the start URLs. 0 means unlimited
# (the default). Set a positive value to bound a frontier that would otherwise
# crawl an entire site via "next"/related links. Pairs well with the URL deny
# patterns above.
# DEPTH_LIMIT = 3

# Item pipelines.
ITEM_PIPELINES = {
    "myscraper.pipelines.ValidationPipeline": 300,
    # Log per-run item count after validation — enable to track yield per spider.
    # "myscraper.pipelines.ItemCountPipeline": 900,
}

# Feed exports — JSON Lines by default.
FEED_EXPORT_ENCODING = "utf-8"

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
