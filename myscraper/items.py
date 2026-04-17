"""Pydantic-validated items.

Using Pydantic instead of scrapy.Item so the schema is shared across spiders,
pipelines, and downstream consumers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BookItem(BaseModel):
    title: str
    price_gbp: float = Field(ge=0)
    in_stock: bool
    rating: int = Field(ge=1, le=5)
    url: str


class QuoteItem(BaseModel):
    text: str
    author: str
    tags: list[str]
    url: str
