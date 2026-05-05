"""Unit tests for myscraper.middlewares."""

from __future__ import annotations

import pytest
from scrapy.http import Request

from myscraper.middlewares import (
    DEFAULT_USER_AGENTS,
    ProxyMiddleware,
    RotateUserAgentMiddleware,
)


def test_rotate_ua_uses_defaults_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("USER_AGENTS", raising=False)
    mw = RotateUserAgentMiddleware.from_crawler(crawler=None)
    assert mw.user_agents == DEFAULT_USER_AGENTS


def test_rotate_ua_parses_comma_separated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_AGENTS", "ua-one,  ua-two ,ua-three")
    mw = RotateUserAgentMiddleware.from_crawler(crawler=None)
    assert mw.user_agents == ["ua-one", "ua-two", "ua-three"]


def test_rotate_ua_falls_back_when_env_is_empty_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_AGENTS", "   ,  ,")
    mw = RotateUserAgentMiddleware.from_crawler(crawler=None)
    assert mw.user_agents == DEFAULT_USER_AGENTS


def test_rotate_ua_sets_header_from_pool() -> None:
    pool = ["only-ua"]
    mw = RotateUserAgentMiddleware(pool)
    request = Request(url="https://example.com")
    assert mw.process_request(request, spider=None) is None
    assert request.headers["User-Agent"].decode("ascii") == "only-ua"


def test_proxy_mw_no_proxy_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROXY_URL", raising=False)
    mw = ProxyMiddleware.from_crawler(crawler=None)
    request = Request(url="https://example.com")
    mw.process_request(request, spider=None)
    assert "proxy" not in request.meta


def test_proxy_mw_sets_meta_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROXY_URL", "http://user:pass@proxy.example:8080")
    mw = ProxyMiddleware.from_crawler(crawler=None)
    request = Request(url="https://example.com")
    mw.process_request(request, spider=None)
    assert request.meta["proxy"] == "http://user:pass@proxy.example:8080"


def test_proxy_mw_does_not_override_existing_meta() -> None:
    mw = ProxyMiddleware(proxy_url="http://default-proxy:8080")
    request = Request(url="https://example.com", meta={"proxy": "http://override:9090"})
    mw.process_request(request, spider=None)
    assert request.meta["proxy"] == "http://override:9090"
