"""今月の発見のテスト（要件23-9）。

build_discoveries はDBに触れない純粋関数なので、スタブだけで検証できる。
"""
from datetime import date, datetime

from app.summary.discoveries import build_discoveries


class Rec:
    """Content 相当の軽量スタブ。"""

    def __init__(
        self,
        title="題名",
        category="book",
        creator=None,
        rating=None,
        memo=None,
        logged_date=None,
        wished_at=None,
        created_at=None,
    ):
        self.title = title
        self.category = category
        self.creator = creator
        self.rating = rating
        self.memo = memo
        self.logged_date = logged_date or date(2026, 8, 10)
        self.wished_at = wished_at
        self.created_at = created_at

    @property
    def memo_length(self):
        return len(self.memo) if self.memo else 0


LONG = "あ" * 40
LONGER = "あ" * 60


def rule_ids(result):
    return [d["rule_id"] for d in result]


def texts(result):
    return " / ".join(d["text"] for d in result)


# --- 0件・1件 -----------------------------------------------------------


def test_empty_returns_empty_list():
    """記録0件で空リスト。例外を出さない（要件23-9）。"""
    assert build_discoveries([]) == []
    assert build_discoveries([], []) == []


def test_single_record_always_returns_one():
    """記録1件なら必ず1件返る（要件23-6）。"""
    result = build_discoveries([Rec(title="ひとつだけ")])
    assert rule_ids(result) == ["only_one"]
    assert "ひとつだけ" in result[0]["text"]


def test_two_plain_records_fall_back_to_bookends():
    """何も成立しなくても、記録2件以上ならフォールバックが出る（要件23-6）。"""
    records = [
        Rec(title="さいしょ", logged_date=date(2026, 8, 1)),
        Rec(title="さいご", logged_date=date(2026, 8, 20)),
    ]
    result = build_discoveries(records)
    assert rule_ids(result) == ["bookends"]
    assert "さいしょ" in result[0]["text"]
    assert "さいご" in result[0]["text"]


def test_never_says_nothing_found():
    """「発見がありませんでした」は出さない（要件23-6）。"""
    for records in ([Rec()], [Rec(), Rec()], [Rec() for _ in range(5)]):
        assert len(build_discoveries(records)) >= 1


# --- longest_memo / memo_gap -------------------------------------------


def test_longest_memo():
    records = [
        Rec(title="短いほう", memo="みじかい"),
        Rec(title="長いほう", memo=LONG),
    ]
    result = build_discoveries(records)
    assert result[0]["rule_id"] == "longest_memo"
    assert "長いほう" in result[0]["text"]


def test_longest_memo_needs_two_memoed_records():
    """メモのある記録が1件だけなら成立しない。"""
    records = [Rec(title="ひとつ", memo=LONG), Rec(title="メモなし")]
    assert "longest_memo" not in rule_ids(build_discoveries(records))


def test_longest_memo_needs_40_chars():
    records = [
        Rec(title="A", memo="あ" * 39),
        Rec(title="B", memo="あ" * 10),
    ]
    assert "longest_memo" not in rule_ids(build_discoveries(records))


def test_memo_gap_wins_when_not_top_rated():
    """最長メモが最高評価でないなら memo_gap（排他・要件23-5）。"""
    records = [
        Rec(title="語ったほう", memo=LONGER, rating=3),
        Rec(title="高評価", memo="みじかい", rating=5),
    ]
    result = build_discoveries(records)
    assert result[0]["rule_id"] == "memo_gap"
    assert "語ったほう" in result[0]["text"]
    # 文言中の数字が実際の評価と一致すること（要件23-9）
    assert "評価は3だったけれど" in result[0]["text"]
    assert "longest_memo" not in rule_ids(result)


def test_memo_gap_not_used_when_top_rated():
    records = [
        Rec(title="語ったほう", memo=LONGER, rating=5),
        Rec(title="ほか", memo="みじかい", rating=3),
    ]
    assert build_discoveries(records)[0]["rule_id"] == "longest_memo"


def test_memo_gap_not_used_when_unrated():
    """評価が無いと「評価は◯だったけれど」と言えないので longest_memo。"""
    records = [
        Rec(title="語ったほう", memo=LONGER, rating=None),
        Rec(title="ほか", memo="みじかい", rating=5),
    ]
    assert build_discoveries(records)[0]["rule_id"] == "longest_memo"


# --- long_wait ----------------------------------------------------------


def test_long_wait():
    records = [
        Rec(
            title="ずっと気になってた",
            logged_date=date(2026, 8, 20),
            wished_at=datetime(2026, 8, 1),
        ),
        Rec(title="ふつう", logged_date=date(2026, 8, 5)),
    ]
    result = build_discoveries(records)
    assert "long_wait" in rule_ids(result)
    # 日数が実際の差と一致すること（要件23-9）
    assert "19日後に見ました" in texts(result)


def test_long_wait_needs_seven_days():
    records = [
        Rec(logged_date=date(2026, 8, 7), wished_at=datetime(2026, 8, 1)),
        Rec(logged_date=date(2026, 8, 8)),
    ]
    assert "long_wait" not in rule_ids(build_discoveries(records))


# --- reunion ------------------------------------------------------------


def test_reunion():
    now = [Rec(title="新作", creator="宮沢賢治", logged_date=date(2026, 8, 10))]
    past = [Rec(title="前作", creator="宮沢賢治", logged_date=date(2026, 5, 3))]
    result = build_discoveries(now, past + now)
    assert "reunion" in rule_ids(result)
    assert "宮沢賢治を記録するのは、2026年5月以来2回目です" in texts(result)


def test_reunion_survives_without_history():
    """過去データが一切なくても例外を出さない（要件23-9）。"""
    records = [Rec(creator="だれか")]
    for history in (None, [], records):
        result = build_discoveries(records, history)
        assert "reunion" not in rule_ids(result)
        assert len(result) >= 1  # 何かは必ず返る


def test_unknown_history_does_not_claim_first():
    """履歴を渡さない（None）と「これが初めてです」と断定しない。

    履歴の渡し忘れで嘘の発見が出るのを防ぐ（要件23-4：外さない）。
    """
    records = [Rec(title="A", category="stage"), Rec(title="B", category="stage")]

    assert "first_category" not in rule_ids(build_discoveries(records, None))
    # 履歴を調べた結果として空なら、初めてだと言ってよい
    assert "first_category" in rule_ids(build_discoveries(records, records))


def test_reunion_ignores_same_month():
    """同じ月の中で2件あっても「以来2回目」にはしない。"""
    now = [
        Rec(title="A", creator="同じ人", logged_date=date(2026, 8, 1)),
        Rec(title="B", creator="同じ人", logged_date=date(2026, 8, 20)),
    ]
    assert "reunion" not in rule_ids(build_discoveries(now, now))


def test_reunion_skipped_when_third_time():
    """過去に2件あると「2回目」が嘘になるので出さない。"""
    now = [Rec(title="3作目", creator="常連", logged_date=date(2026, 8, 10))]
    past = [
        Rec(title="1作目", creator="常連", logged_date=date(2026, 4, 1)),
        Rec(title="2作目", creator="常連", logged_date=date(2026, 6, 1)),
    ]
    assert "reunion" not in rule_ids(build_discoveries(now, past + now))


# --- busy_day -----------------------------------------------------------


def test_busy_day():
    records = [Rec(logged_date=date(2026, 8, 15)) for _ in range(3)]
    result = build_discoveries(records)
    assert "busy_day" in rule_ids(result)
    assert "8月15日は、1日に3つ記録しました" in texts(result)


def test_busy_day_needs_three():
    records = [Rec(logged_date=date(2026, 8, 15)) for _ in range(2)]
    assert "busy_day" not in rule_ids(build_discoveries(records))


# --- first_category -----------------------------------------------------


def test_first_category():
    now = [
        Rec(title="はじめての舞台", category="stage", logged_date=date(2026, 8, 10)),
        Rec(title="いつもの本", category="book", logged_date=date(2026, 8, 11)),
    ]
    past = [Rec(category="book", logged_date=date(2026, 7, 1))]
    result = build_discoveries(now, past + now)
    assert "first_category" in rule_ids(result)
    assert "舞台・演劇を記録したのは、これが初めてです" in texts(result)


def test_first_category_suppressed_when_label_used_it(monkeypatch):
    """ラベルが first のときは発見に出さない（要件23-5・23-9）。"""
    now = [
        Rec(title="はじめての舞台", category="stage", logged_date=date(2026, 8, 10)),
        Rec(title="いつもの本", category="book", logged_date=date(2026, 8, 11)),
    ]
    past = [Rec(category="book", logged_date=date(2026, 7, 1))]

    with_label = build_discoveries(now, past + now, label_rule_id="first")
    assert "first_category" not in rule_ids(with_label)
    # 代わりに何かは出る（要件23-6）
    assert len(with_label) >= 1

    without_label = build_discoveries(now, past + now, label_rule_id="single")
    assert "first_category" in rule_ids(without_label)


# --- 優先順位・上限・重複 -----------------------------------------------


def test_priority_order():
    """上から順に評価され、優先度の高いものが先に来る（要件23-5）。"""
    records = [
        # longest_memo（優先1）と busy_day（優先4）の両方が成立する
        Rec(title="長文", memo=LONGER, logged_date=date(2026, 8, 15)),
        Rec(title="B", memo="みじかい", logged_date=date(2026, 8, 15)),
        Rec(title="C", logged_date=date(2026, 8, 15)),
    ]
    assert rule_ids(build_discoveries(records)) == ["longest_memo", "busy_day"]


def test_never_returns_more_than_two():
    """上限2件（要件23-5・23-9）。"""
    records = [
        Rec(
            title="長文",
            memo=LONGER,
            rating=2,
            logged_date=date(2026, 8, 15),
            wished_at=datetime(2026, 8, 1),
        ),
        Rec(title="B", memo="みじかい", rating=5, logged_date=date(2026, 8, 15)),
        Rec(title="C", category="stage", logged_date=date(2026, 8, 15)),
    ]
    assert len(build_discoveries(records, records)) == 2


def test_same_record_is_not_used_twice():
    """同じ記録を対象とする発見は重複させず、下位を捨てて次点を採る（要件23-5）。"""
    target = Rec(
        title="ひとつの記録",
        memo=LONGER,
        logged_date=date(2026, 8, 20),
        wished_at=datetime(2026, 8, 1),
    )
    records = [target, Rec(title="ほか", memo="みじかい", logged_date=date(2026, 8, 5))]

    result = build_discoveries(records)
    # longest_memo と long_wait はどちらも target が対象。片方だけ採用される。
    assert rule_ids(result).count("longest_memo") <= 1
    assert not ("longest_memo" in rule_ids(result) and "long_wait" in rule_ids(result))
    # タイトルが2回出てこない
    assert texts(result).count("ひとつの記録") == 1


def test_records_without_logged_date_are_ignored():
    """気になる項目が紛れ込んでも落ちない（logged_date が None）。"""
    records = [Rec(title="見た"), Rec(title="まだ", logged_date=None)]
    records[1].logged_date = None
    result = build_discoveries(records)
    assert rule_ids(result) == ["only_one"]
    assert "見た" in result[0]["text"]


# --- 文言の原則（要件23-4）---------------------------------------------


def test_wording_has_no_exclamation_or_second_person():
    """感嘆符を使わない。「あなたは〜」で始めない。"""
    samples = [
        build_discoveries([Rec(title="A")]),
        build_discoveries([Rec(title="A", memo=LONGER), Rec(title="B", memo="短")]),
        build_discoveries([Rec(logged_date=date(2026, 8, 15)) for _ in range(3)]),
    ]
    for result in samples:
        for d in result:
            assert "!" not in d["text"]
            assert "！" not in d["text"]
            assert not d["text"].startswith("あなた")
