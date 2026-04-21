"""Item pipelines.

ValidationPipeline  — rejects malformed items at the schema boundary.
ItemCountPipeline   — logs total items scraped at the end of each run.
"""

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


class ItemCountPipeline:
    """Logs total items scraped at the end of each run.

    Wire in *after* ValidationPipeline so the count reflects only items that
    passed validation:

        ITEM_PIPELINES = {
            "myscraper.pipelines.ValidationPipeline": 300,
            "myscraper.pipelines.ItemCountPipeline": 900,
        }
    """

    def open_spider(self, spider) -> None:  # type: ignore[no-untyped-def]
        self._count = 0

    def process_item(self, item, spider):  # type: ignore[no-untyped-def]
        self._count += 1
        return item

    def close_spider(self, spider) -> None:  # type: ignore[no-untyped-def]
        spider.logger.info(
            "ItemCountPipeline: %d item(s) scraped by '%s'",
            self._count,
            spider.name,
        )
