"""Downloader middlewares: user-agent rotation + optional proxy injection.

Both are plumbed in settings.py. Keep these simple — production systems
usually swap these for richer versions (e.g. proxy-tier routing), but the
shape is identical.
"""

from __future__ import annotations

import os
import random

DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]


class RotateUserAgentMiddleware:
    def __init__(self, user_agents: list[str]) -> None:
        self.user_agents = user_agents

    @classmethod
    def from_crawler(cls, crawler):  # type: ignore[no-untyped-def]
        raw = os.getenv("USER_AGENTS", "")
        uas = [u.strip() for u in raw.split(",") if u.strip()] or DEFAULT_USER_AGENTS
        return cls(uas)

    def process_request(self, request, spider):  # type: ignore[no-untyped-def]
        request.headers["User-Agent"] = random.choice(self.user_agents)
        return None


class ProxyMiddleware:
    """Sets request.meta['proxy'] from PROXY_URL env var (if present)."""

    def __init__(self, proxy_url: str | None) -> None:
        self.proxy_url = proxy_url

    @classmethod
    def from_crawler(cls, crawler):  # type: ignore[no-untyped-def]
        return cls(os.getenv("PROXY_URL") or None)

    def process_request(self, request, spider):  # type: ignore[no-untyped-def]
        if self.proxy_url and "proxy" not in request.meta:
            request.meta["proxy"] = self.proxy_url
        return None


class CookieHeaderMiddleware:
    """Attaches a raw ``Cookie`` header from ``COOKIE_HEADER`` env (if present).

    Useful for bootstrapping an authenticated scrape from a logged-in browser
    session: open DevTools → Network → copy the ``Cookie`` request header and
    drop it into ``.env``. Skips requests that already carry a Cookie header
    so per-request overrides win.

    Scrapy's built-in cookies middleware handles Set-Cookie round-tripping;
    this one only seeds the initial value. Leave both enabled together when
    the target site refreshes cookies mid-session.
    """

    def __init__(self, cookie_header: str | None) -> None:
        self.cookie_header = cookie_header

    @classmethod
    def from_crawler(cls, crawler):  # type: ignore[no-untyped-def]
        raw = os.getenv("COOKIE_HEADER", "").strip()
        return cls(raw or None)

    def process_request(self, request, spider):  # type: ignore[no-untyped-def]
        if self.cookie_header and "Cookie" not in request.headers:
            request.headers["Cookie"] = self.cookie_header
        return None
