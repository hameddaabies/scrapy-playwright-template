"""Scrapy settings.

Polite by default. Flip knobs (concurrency, delay, playwright flag per-request)
per spider or per call as needed.
"""

from __future__ import annotations

from dotenv import load_dotenv

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

# Middlewares.
DOWNLOADER_MIDDLEWARES = {
    "myscraper.middlewares.RotateUserAgentMiddleware": 400,
    "myscraper.middlewares.ProxyMiddleware": 410,
}

# Item pipelines.
ITEM_PIPELINES = {
    "myscraper.pipelines.ValidationPipeline": 300,
}

# Feed exports — JSON Lines by default.
FEED_EXPORT_ENCODING = "utf-8"

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
