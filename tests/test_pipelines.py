"""Unit tests for myscraper.pipelines."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from scrapy.exceptions import DropItem

from myscraper.pipelines import ItemCountPipeline, ValidationPipeline


def _spider(name: str = "test") -> MagicMock:
    spider = MagicMock()
    spider.name = name
    return spider


def test_count_increments_per_item() -> None:
    pipeline = ItemCountPipeline()
    spider = _spider()
    pipeline.open_spider(spider)
    for i in range(5):
        pipeline.process_item({"field": i}, spider)
    pipeline.close_spider(spider)
    logged_args = spider.logger.info.call_args[0]
    assert 5 in logged_args


def test_count_is_zero_on_empty_run() -> None:
    pipeline = ItemCountPipeline()
    spider = _spider()
    pipeline.open_spider(spider)
    pipeline.close_spider(spider)
    logged_args = spider.logger.info.call_args[0]
    assert 0 in logged_args


def test_process_item_passes_item_through() -> None:
    pipeline = ItemCountPipeline()
    spider = _spider()
    pipeline.open_spider(spider)
    item = {"title": "Light in the Attic", "price_gbp": 9.99}
    result = pipeline.process_item(item, spider)
    assert result is item


def test_spider_name_appears_in_log() -> None:
    pipeline = ItemCountPipeline()
    spider = _spider(name="books")
    pipeline.open_spider(spider)
    pipeline.close_spider(spider)
    logged_args = spider.logger.info.call_args[0]
    assert "books" in logged_args


def _valid_book() -> dict:
    return {
        "title": "Light in the Attic",
        "price_gbp": 9.99,
        "in_stock": True,
        "rating": 4,
        "url": "https://books.toscrape.com/catalogue/light-in-the-attic_1000/index.html",
    }


def test_validation_returns_dict_for_valid_book() -> None:
    pipeline = ValidationPipeline()
    result = pipeline.process_item(_valid_book(), _spider(name="books"))
    assert result == _valid_book()


def test_validation_drops_book_with_bad_rating() -> None:
    pipeline = ValidationPipeline()
    bad = _valid_book() | {"rating": 9}
    with pytest.raises(DropItem):
        pipeline.process_item(bad, _spider(name="books"))


def test_validation_drops_book_with_negative_price() -> None:
    pipeline = ValidationPipeline()
    bad = _valid_book() | {"price_gbp": -1.0}
    with pytest.raises(DropItem):
        pipeline.process_item(bad, _spider(name="books"))


def test_validation_drops_item_missing_required_field() -> None:
    pipeline = ValidationPipeline()
    bad = _valid_book()
    del bad["url"]
    with pytest.raises(DropItem):
        pipeline.process_item(bad, _spider(name="books"))


def test_validation_passes_through_unknown_spider() -> None:
    pipeline = ValidationPipeline()
    item = {"anything": "goes", "schema": None}
    result = pipeline.process_item(item, _spider(name="unmapped"))
    assert result is item


def test_validation_uses_quote_schema_for_quotes_spider() -> None:
    pipeline = ValidationPipeline()
    quote = {
        "text": "The world as we have created it is a process of our thinking.",
        "author": "Albert Einstein",
        "tags": ["change", "deep-thoughts"],
        "url": "https://quotes.toscrape.com/page/1/",
    }
    assert pipeline.process_item(quote, _spider(name="quotes")) == quote
    bad_quote = quote | {"tags": "not-a-list"}
    with pytest.raises(DropItem):
        pipeline.process_item(bad_quote, _spider(name="quotes"))
