"""Validation pipeline — rejects malformed items at the boundary."""

from __future__ import annotations

from pydantic import ValidationError
from scrapy.exceptions import DropItem

from .items import BookItem


class ValidationPipeline:
    def process_item(self, item, spider):  # type: ignore[no-untyped-def]
        try:
            validated = BookItem.model_validate(dict(item))
        except ValidationError as e:
            raise DropItem(f"invalid item: {e}") from e
        return validated.model_dump()
