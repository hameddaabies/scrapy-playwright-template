"""Unit tests for myscraper.settings."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from myscraper.settings import (
    CONCURRENT_REQUESTS,
    CONCURRENT_REQUESTS_PER_DOMAIN,
    PLAYWRIGHT_ABORT_REQUEST,
    PLAYWRIGHT_ABORT_RESOURCE_TYPES,
    PLAYWRIGHT_MAX_PAGES_PER_CONTEXT,
    playwright_proxy,
    should_abort_request,
)


def _request(resource_type: str) -> SimpleNamespace:
    """Stand in for a playwright.async_api.Request."""
    return SimpleNamespace(resource_type=resource_type, url="https://example.com/asset")


@pytest.mark.parametrize("resource_type", sorted(PLAYWRIGHT_ABORT_RESOURCE_TYPES))
def test_aborts_configured_resource_types(resource_type: str) -> None:
    assert should_abort_request(_request(resource_type)) is True


@pytest.mark.parametrize("resource_type", ["document", "xhr", "fetch", "script"])
def test_keeps_resource_types_the_parser_depends_on(resource_type: str) -> None:
    assert should_abort_request(_request(resource_type)) is False


def test_keeps_stylesheets_so_visibility_waits_stay_reliable() -> None:
    assert should_abort_request(_request("stylesheet")) is False


def test_setting_points_at_the_predicate() -> None:
    assert PLAYWRIGHT_ABORT_REQUEST is should_abort_request


def test_page_cap_does_not_exceed_crawl_concurrency() -> None:
    """Scrapy never has more than CONCURRENT_REQUESTS in flight, so tabs above
    that ceiling can never be opened — the extra quota only misleads."""
    assert PLAYWRIGHT_MAX_PAGES_PER_CONTEXT <= CONCURRENT_REQUESTS


def test_page_cap_leaves_pacing_to_the_politeness_settings() -> None:
    """Below the per-domain concurrency the tab semaphore, not DOWNLOAD_DELAY
    and autothrottle, would govern how fast a single-domain crawl renders."""
    assert PLAYWRIGHT_MAX_PAGES_PER_CONTEXT >= CONCURRENT_REQUESTS_PER_DOMAIN


def test_proxy_disabled_without_proxy_url() -> None:
    assert playwright_proxy(None) is None
    assert playwright_proxy("") is None


def test_proxy_without_credentials_keeps_only_server() -> None:
    assert playwright_proxy("http://proxy.example:8080") == {
        "server": "http://proxy.example:8080"
    }


def test_proxy_credentials_are_split_out_and_decoded() -> None:
    """Playwright rejects inline credentials, and providers often issue
    passwords with reserved characters that must be percent-encoded in a URL."""
    assert playwright_proxy("http://user:p%40ss@proxy.example:8080") == {
        "server": "http://proxy.example:8080",
        "username": "user",
        "password": "p@ss",
    }
