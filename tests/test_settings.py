"""Unit tests for myscraper.settings."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from myscraper.settings import (
    PLAYWRIGHT_ABORT_REQUEST,
    PLAYWRIGHT_ABORT_RESOURCE_TYPES,
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
