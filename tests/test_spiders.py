"""Parser tests for the example spiders.

Feeds recorded HTML fixtures through a spider callback and asserts the parsed
output, so the CSS selectors and the price/rating extraction logic are covered
without hitting the network.
"""

from __future__ import annotations

from scrapy.http import HtmlResponse, Request

from myscraper.spiders.books import BooksSpider

_DETAIL_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

# Trimmed-down copy of a real books.toscrape.com detail page — only the nodes the
# spider actually reads.
_BOOK_DETAIL_HTML = """
<html><body>
  <div class="product_main">
    <h1>A Light in the Attic</h1>
    <p class="star-rating Three"></p>
    <p class="price_color">£51.77</p>
    <p class="instock availability">
      <i class="icon-ok"></i>
      In stock (22 available)
    </p>
  </div>
</body></html>
"""


def _response(html: str, url: str = _DETAIL_URL) -> HtmlResponse:
    return HtmlResponse(
        url=url,
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=Request(url=url),
    )


def _parse_detail(html: str) -> dict:
    spider = BooksSpider()
    return next(iter(spider.parse_detail(_response(html))))


def test_parse_detail_extracts_all_fields() -> None:
    item = _parse_detail(_BOOK_DETAIL_HTML)
    assert item == {
        "title": "A Light in the Attic",
        "price_gbp": 51.77,
        "in_stock": True,
        "rating": 3,
        "url": _DETAIL_URL,
    }


def test_parse_detail_reports_out_of_stock() -> None:
    html = _BOOK_DETAIL_HTML.replace("In stock (22 available)", "Out of stock")
    assert _parse_detail(html)["in_stock"] is False


def test_parse_detail_defaults_unknown_rating_to_one() -> None:
    html = _BOOK_DETAIL_HTML.replace("star-rating Three", "star-rating Zero")
    assert _parse_detail(html)["rating"] == 1


def test_parse_detail_defaults_missing_price_to_zero() -> None:
    html = _BOOK_DETAIL_HTML.replace('<p class="price_color">£51.77</p>', "")
    assert _parse_detail(html)["price_gbp"] == 0.0
