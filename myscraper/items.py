"""Pydantic-validated items.

Using Pydantic instead of scrapy.Item so the schema is shared across spiders,
pipelines, and downstream consumers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _require_absolute_url(cls, v: str) -> str:
    """Reject relative or scheme-less URLs.

    A spider that forgets ``urljoin()`` on a relative ``href`` yields a URL
    that looks fine at a glance but is unusable downstream. Catching it here,
    at the schema boundary, turns a silent data-quality bug into an
    immediate dropped-item stat instead of a confusing 404 three steps later.
    """
    if not v.startswith(("http://", "https://")):
        raise ValueError("url must be an absolute http(s) URL")
    return v


class BookItem(BaseModel):
    # Spiders read text with ``.get("")``, so a drifted selector yields "".
    # Require a non-empty value so that drops the item instead of storing it.
    title: str = Field(min_length=1)
    # Optional so an unreadable price is recorded as "unknown" rather than
    # fabricated as a free book. A present value is still bounded at >= 0.
    price_gbp: float | None = Field(default=None, ge=0)
    in_stock: bool
    # Optional so an unreadable star-rating is recorded as "unknown" rather
    # than fabricated as a one-star book. A present value is still bounded 1-5.
    rating: int | None = Field(default=None, ge=1, le=5)
    url: str

    _check_url = field_validator("url")(_require_absolute_url)


class QuoteItem(BaseModel):
    # Non-empty for the same reason as ``BookItem.title``.
    text: str = Field(min_length=1)
    author: str = Field(min_length=1)
    tags: list[str]
    url: str

    _check_url = field_validator("url")(_require_absolute_url)
