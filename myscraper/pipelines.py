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
    # The Playwright-rendered variant yields the same schema as "quotes".
    "quotes_js": QuoteItem,
}


class ValidationPipeline:
    """Rejects malformed items at the schema boundary.

    Each rejection is recorded under the ``validation/dropped`` stat, plus a
    per-spider ``validation/dropped/<spider>`` breakdown, so the final crawl
    stats show how many items failed schema validation — distinct from
    Scrapy's catch-all ``item_dropped_count``, which also counts items dropped
    for other reasons. Stats wiring is optional: when constructed without a
    stats collector (e.g. in unit tests) the counters are simply skipped.

    Items from a spider with no entry in ``_SPIDER_MODELS`` pass through
    unvalidated; a warning is logged once per spider so a newly added spider's
    unchecked output doesn't go unnoticed.
    """

    def __init__(self, stats=None) -> None:  # type: ignore[no-untyped-def]
        self.stats = stats
        self._warned_unmapped: set[str] = set()

    @classmethod
    def from_crawler(cls, crawler):  # type: ignore[no-untyped-def]
        return cls(stats=crawler.stats)

    def process_item(self, item, spider):  # type: ignore[no-untyped-def]
        model = _SPIDER_MODELS.get(spider.name)
        if model is None:
            if spider.name not in self._warned_unmapped:
                self._warned_unmapped.add(spider.name)
                spider.logger.warning(
                    "ValidationPipeline: no schema registered for spider '%s'; "
                    "its items pass through unvalidated (add it to _SPIDER_MODELS)",
                    spider.name,
                )
            return item
        try:
            validated = model.model_validate(dict(item))
        except ValidationError as e:
            if self.stats is not None:
                self.stats.inc_value("validation/dropped")
                self.stats.inc_value(f"validation/dropped/{spider.name}")
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
