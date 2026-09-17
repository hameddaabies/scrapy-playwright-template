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
    title: str
    price_gbp: float = Field(ge=0)
    in_stock: bool
    # Optional so an unreadable star-rating is recorded as "unknown" rather
    # than fabricated as a one-star book. A present value is still bounded 1-5.
    rating: int | None = Field(default=None, ge=1, le=5)
    url: str

    _check_url = field_validator("url")(_require_absolute_url)


class QuoteItem(BaseModel):
    text: str
    author: str
    tags: list[str]
    url: str

    _check_url = field_validator("url")(_require_absolute_url)
