"""集計ロジックのテスト（要件16章）。

build_summary は純粋関数なのでDBなしで検証できる。
"""
from datetime import date

from app.summary.service import build_summary


class FakeContent:
    """Content 相当の軽量スタブ。"""

    def __init__(self, category, rating=None, memo=None, logged_date=None):
        self.category = category
        self.rating = rating
        self.memo = memo
        self.logged_date = logged_date or date(2026, 8, 1)

    @property
    def memo_length(self):
        return len(self.memo) if self.memo else 0


def test_empty_does_not_raise():
    """記録0件でも例外を出さない（要件16章）。"""
    result = build_summary([])
    assert result["total_count"] == 0
    assert result["active_days"] == 0
    assert result["by_category"] == []
    assert result["top_category"] is None
    assert result["favorites"] == []


def test_counts_and_active_days():
    items = [
        FakeContent("book", logged_date=date(2026, 8, 1)),
        FakeContent("book", logged_date=date(2026, 8, 1)),
        FakeContent("movie", logged_date=date(2026, 8, 2)),
    ]
    result = build_summary(items)
    assert result["total_count"] == 3
    assert result["active_days"] == 2  # 8/1 と 8/2
    assert result["by_category"][0] == ("book", 2)
    assert result["top_category"] == "book"


def test_favorites_order_by_rating():
    """お気に入りは評価の降順（要件5章 優先1）。"""
    items = [
        FakeContent("book", rating=3),
        FakeContent("movie", rating=5),
        FakeContent("music", rating=4),
    ]
    favs = build_summary(items)["favorites"]
    assert [f.rating for f in favs] == [5, 4, 3]


def test_favorites_tiebreak_by_memo_length():
    """評価同点ならメモ文字数の降順（要件5章 優先2）。"""
    items = [
        FakeContent("book", rating=5, memo="みじかい"),
        FakeContent("movie", rating=5, memo="とてもながいながいメモをかいた"),
    ]
    favs = build_summary(items)["favorites"]
    assert favs[0].category == "movie"  # メモが長い方が上


def test_favorites_tiebreak_by_date():
    """評価もメモ長も同点なら記録日の降順（要件5章 優先3）。"""
    items = [
        FakeContent("book", rating=5, memo="abcd", logged_date=date(2026, 8, 1)),
        FakeContent("movie", rating=5, memo="wxyz", logged_date=date(2026, 8, 20)),
    ]
    favs = build_summary(items)["favorites"]
    assert favs[0].category == "movie"  # 新しい方が上


def test_favorites_excludes_unrated():
    """評価未入力は候補に含めない（要件5章）。"""
    items = [
        FakeContent("book", rating=None, memo="長い長いメモ"),
        FakeContent("movie", rating=2),
    ]
    favs = build_summary(items)["favorites"]
    assert len(favs) == 1
    assert favs[0].category == "movie"


def test_favorites_limited_to_three():
    items = [FakeContent("book", rating=5) for _ in range(5)]
    favs = build_summary(items)["favorites"]
    assert len(favs) == 3


def test_prev_period_diff():
    """前の期間（前週）との差が正しい（要件15章 Phase4）。"""
    items = [FakeContent("book"), FakeContent("movie")]
    result = build_summary(items, prev_total=5)
    assert result["prev_total"] == 5
    assert result["diff"] == -3  # 2 - 5

    result_none = build_summary(items, prev_total=None)
    assert result_none["diff"] is None
