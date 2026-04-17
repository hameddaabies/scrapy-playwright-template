"""Validation pipeline — rejects malformed items at the boundary."""

from __future__ import annotations

from pydantic import BaseModel, ValidationError
from scrapy.exceptions import DropItem

from .items import BookItem, QuoteItem

# Map spider name → Pydantic model. Add an entry here when adding a new spider.
_SPIDER_MODELS: dict[str, type[BaseModel]] = {
    "books": BookItem,
    "quotes": QuoteItem,
}


class ValidationPipeline:
    def process_item(self, item, spider):  # type: ignore[no-untyped-def]
        model = _SPIDER_MODELS.get(spider.name)
        if model is None:
            return item
        try:
            validated = model.model_validate(dict(item))
        except ValidationError as e:
            raise DropItem(f"invalid item: {e}") from e
        return validated.model_dump()
