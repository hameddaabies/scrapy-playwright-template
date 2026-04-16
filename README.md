# scrapy-playwright-template

A production-shaped **Scrapy + Playwright** scaffold for scraping modern JS-heavy sites at scale. Ships with the pieces you actually need in production — user-agent rotation, proxy plumbing, retry middleware, a JSON-Lines pipeline, and a clean example spider — without the YAGNI cruft tutorials bolt on.

## What's in the box

- ✅ **Playwright download handler** — handles JS-rendered pages out of the box
- ✅ **User-agent rotation middleware** — cycles through a pool on every request
- ✅ **Proxy support via env var** — drop in residential / datacenter proxy URLs without code changes
- ✅ **Autothrottle + AUTOTHROTTLE_TARGET_CONCURRENCY** — polite by default, tunable per-domain
- ✅ **RETRY middleware** — handles 429 / 503 / timeouts with exponential backoff
- ✅ **JSON Lines feed** — one record per line, stream-friendly, easy to post-process
- ✅ **Pydantic item validation** — reject malformed items at the pipeline boundary
- ✅ **Example spider** — scrapes `books.toscrape.com` (public practice site, no ToS issues)

## Quickstart

```bash
pip install -r requirements.txt
playwright install chromium   # one-time
cp .env.example .env          # edit if you want to use a proxy

scrapy crawl books -O output/books.jsonl
```

Check `output/books.jsonl` — you should see ~1000 books with title, price, availability, and rating.

## Customizing

### Add a new spider

```bash
scrapy genspider myspider example.com
```

Then implement `parse()` the same way the example spider does. The Pydantic model in `myscraper/items.py` will validate whatever you yield.

### Use Playwright for a specific URL

In your spider:

```python
yield scrapy.Request(
    url,
    meta={"playwright": True, "playwright_include_page": False},
    callback=self.parse_rendered,
)
```

The Playwright download handler is pre-registered in `settings.py` — you just flag the requests that need it.

### Swap in a real proxy

Edit `.env`:

```
PROXY_URL=http://user:pass@proxy-host:port
```

The middleware reads this env var on every request. Restart the crawl.

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
├── scrapy.cfg
├── myscraper/
│   ├── __init__.py
│   ├── items.py              # Pydantic-validated items
│   ├── middlewares.py        # UA rotation + proxy
│   ├── pipelines.py          # validation + normalization
│   ├── settings.py           # Playwright + throttle + retry config
│   └── spiders/
│       ├── __init__.py
│       └── books.py          # example spider (books.toscrape.com)
├── requirements.txt
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
