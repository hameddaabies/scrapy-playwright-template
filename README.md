# scrapy-playwright-template

[![tests](https://github.com/hameddaabies/scrapy-playwright-template/actions/workflows/tests.yml/badge.svg)](https://github.com/hameddaabies/scrapy-playwright-template/actions/workflows/tests.yml)

A production-shaped **Scrapy + Playwright** scaffold for scraping modern JS-heavy sites at scale. Ships with the pieces you actually need in production — user-agent rotation, proxy plumbing, retry middleware, a JSON-Lines pipeline, and a clean example spider — without the YAGNI cruft tutorials bolt on.

## What's in the box

- ✅ **Playwright download handler** — handles JS-rendered pages out of the box
- ✅ **User-agent rotation middleware** — cycles through a pool on every request
- ✅ **Proxy support via env var** — drop in residential / datacenter proxy URLs without code changes
- ✅ **Autothrottle + AUTOTHROTTLE_TARGET_CONCURRENCY** — polite by default, tunable per-domain
- ✅ **RETRY middleware** — handles 429 / 503 / timeouts with exponential backoff
- ✅ **JSON Lines feed** — one record per line, stream-friendly, easy to post-process
- ✅ **Pydantic item validation** — reject malformed items at the pipeline boundary
- ✅ **Three example spiders** — two plain-HTTP (`books.toscrape.com`, `quotes.toscrape.com`) plus `quotes_js`, which renders a JS-only page through Playwright (public practice sites, no ToS issues)
- ✅ **URL deny + depth-limit examples** — scope a crawl by path or frontier depth, not just by host
- ✅ **Opt-in cookie + item-count middleware/pipeline** — commented in `settings.py`, one line to enable

## Quickstart

```bash
pip install -r requirements.txt
playwright install chromium   # one-time
cp .env.example .env          # edit if you want to use a proxy

scrapy crawl books -O output/books.jsonl
scrapy crawl quotes -O output/quotes.jsonl
scrapy crawl quotes_js -O output/quotes_js.jsonl   # Playwright-rendered
```

Check `output/books.jsonl` — you should see ~1000 books with title, price, availability, and rating.
`output/quotes.jsonl` has ~100 quotes with text, author, and tags.
`output/quotes_js.jsonl` has the same ~100 quotes, but scraped from `/js/`, where the
server sends an empty container and a `var data = [...]` script — fetch it without a
browser and you get zero quotes.

## Customizing

### Add a new spider

```bash
scrapy genspider myspider example.com
```

Then implement `parse()` the same way the example spider does. The Pydantic model in `myscraper/items.py` will validate whatever you yield.

### Use Playwright for a specific URL

In your spider:

```python
from scrapy_playwright.page import PageMethod

yield scrapy.Request(
    url,
    meta={
        "playwright": True,
        "playwright_page_methods": [PageMethod("wait_for_selector", "div.quote")],
    },
    callback=self.parse_rendered,
)
```

The Playwright download handler is pre-registered in `settings.py` — you just flag the
requests that need it. Wait for a selector rather than parsing straight away: navigation
resolves before the client-side render finishes, so an ungated callback sees an empty page
intermittently. See `myscraper/spiders/quotes_js.py` for a working end-to-end example —
including seeding the start URLs from `start()`, since Scrapy >= 2.13 ignores
`start_requests()` and would otherwise fetch them un-rendered.

### Swap in a real proxy

Edit `.env`:

```
PROXY_URL=http://user:pass@proxy-host:port
```

`ProxyMiddleware` applies it to plain HTTP requests, and `settings.py` passes it to the
Playwright browser as a launch option — scrapy-playwright ignores `meta["proxy"]`, so
rendered requests would otherwise bypass the proxy. Restart the crawl.

## Escalation pattern (production notes)

Most "anti-bot" content is wrong because it treats scraping like one thing. In production, I run a tiered escalation:

1. **Plain requests** — cheapest, fastest, works for ~80% of sites
2. **Playwright-rendered** — only for sites that need JS (this template, as a floor)
3. **Residential proxy + rendered** — for sites with geo / IP reputation checks
4. **Paid API** (Zyte / Diffbot) — only when self-hosting costs more than the API

This template gives you stage 1–2. Stage 3 is a `.env` change. Stage 4 is an HTTP request to a different endpoint — out of scope for a starter repo, but I've built it for clients.

## Project layout

```
scrapy-playwright-template/
├── .github/workflows/tests.yml   # CI: ruff lint + pytest on 3.10 + 3.12
├── scrapy.cfg
├── myscraper/
│   ├── __init__.py
│   ├── items.py              # Pydantic-validated items
│   ├── middlewares.py        # UA rotation, proxy, cookie, URL-deny
│   ├── pipelines.py          # validation + item-count logging
│   ├── settings.py           # Playwright + throttle + retry config
│   └── spiders/
│       ├── __init__.py
│       ├── books.py          # example spider (books.toscrape.com)
│       ├── quotes.py         # example spider (quotes.toscrape.com)
│       └── quotes_js.py      # Playwright-rendered spider (quotes.toscrape.com/js/)
├── tests/                    # fixture-driven spider/middleware/pipeline tests
├── requirements.txt
├── pyproject.toml            # ruff lint config (no packaging metadata)
├── .env.example
└── README.md
```

## Respectful crawling

This template defaults to `ROBOTSTXT_OBEY = True`, a 2-request concurrency, and a 1-second delay. **Don't turn those off without a reason.** If a site's ToS or robots.txt forbids scraping, find another data source or ask for API access.

## Who wrote this

Hamed Daabies — Data Engineer ([Upwork](https://www.upwork.com/freelancers/hameddaabies) · [LinkedIn](https://www.linkedin.com/in/hameddaabies/)).

I build production scrapers for a living, currently running a 50+ domain pipeline for a Canadian e-commerce client. Need something more than this starter? Reach out.

## License

MIT
