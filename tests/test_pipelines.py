"""Unit tests for myscraper.pipelines."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from myscraper.pipelines import ItemCountPipeline


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
