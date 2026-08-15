"""今月の発見（要件23章）。

集計から「本人も気づいていなかった事実」を1〜2件拾う。

素材は「何を見たか」ではなく **「どう記録したか」** に置く（要件23-2）。
利用者は月10件程度の記録を全部覚えているので、何を見たかを言われても驚きがない。
一方、どれに一番長くメモを書いたかは覚えていない。そこが唯一の未知の領域。

文言は事実と数字だけ。解釈や意味づけは足さない（要件23-4）。
テンプレートは constants.py に置き、ここには書かない（要件23-7）。

DBに触れない純粋関数。
"""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from ..constants import (
    CATEGORY_LABELS,
    DISCOVERY_BUSY_MIN,
    DISCOVERY_LIMIT,
    DISCOVERY_MEMO_MIN,
    DISCOVERY_TEMPLATES,
    DISCOVERY_WAIT_DAYS,
)


def build_discoveries(
    records: Iterable[Any],
    all_records: Iterable[Any] | None = None,
    label_rule_id: str | None = None,
    period_start: date | None = None,
) -> list[dict]:
    """その期間の発見を、優先順に最大2件返す（要件23-5）。

    引数:
        records: その月の status="done" の記録。
        all_records: 全期間の status="done" の記録（reunion / first_category 用）。
            最初の1〜2ヶ月は longest_memo・busy_day・フォールバックしか出ないが、
            それが仕様（要件23-6）。
            **None は「履歴が不明」を意味し、履歴に依存するルール
            （reunion・first_category）を評価しない。** 空リストは
            「履歴を調べた結果、過去の記録が無かった」を意味し、
            first_category が成立しうる。両者を混同すると、履歴を渡し忘れただけで
            「これが初めてです」と断定してしまう。
        label_rule_id: ひとことラベル（22章）で採用されたルールID。
            "first" のときは first_category を出さない。同じ画面で同じことを
            二度言わないため（要件23-5）。未実装のうちは None を渡す。
        period_start: 集計期間の初日。これより前が「過去」になる。
            省略すると、records の最も古い記録が属する月の1日を使う。
            週次で集計する場合は週の初日（月曜）を渡すこと。渡さないと
            同じ月の数日前の記録が「過去」に入らず、reunion が出なくなる。

    戻り値:
        [{"rule_id": str, "text": str}, ...] 0〜2件。
        記録0件なら空リスト（呼び出し側で領域ごと非表示にする・要件23-5）。
        記録が1件でもあれば必ず1件は返る（要件23-6）。
    """
    records = [r for r in records if r.logged_date is not None]
    if not records:
        return []

    if period_start is None:
        period_start = min(r.logged_date for r in records).replace(day=1)

    # 履歴が渡されていなければ、過去について何も断定しない
    history_known = all_records is not None
    past = [
        r
        for r in (all_records or [])
        if r.logged_date is not None and r.logged_date < period_start
    ]

    # 優先順に候補を組み立てる。各候補は (rule_id, text, 対象レコード集合)。
    # 対象が同じ記録どうしは重複とみなし、下位を捨てて次点を採る（要件23-5）。
    candidates = [
        _memo_rule(records),
        _long_wait(records),
        _reunion(records, past) if history_known else None,
        _busy_day(records),
        _first_category(records, past, label_rule_id) if history_known else None,
        _bookends(records),
        _only_one(records),
    ]

    chosen: list[dict] = []
    used: set = set()
    for candidate in candidates:
        if candidate is None:
            continue
        rule_id, values, targets = candidate
        if targets & used:
            continue  # 同じ記録について二度言わない
        chosen.append(
            {"rule_id": rule_id, "text": DISCOVERY_TEMPLATES[rule_id].format(**values)}
        )
        used |= targets
        if len(chosen) >= DISCOVERY_LIMIT:
            break

    return chosen


# --- 個々のルール ---------------------------------------------------------
# 戻り値は (rule_id, テンプレートに渡す値, 対象レコード集合) または None。


def _memo_rule(records: list) -> tuple | None:
    """優先1：いちばん長く語ったもの。

    メモのある記録が2件以上、かつ最長メモが40文字以上のとき成立。
    その記録がその月の最高評価でないなら memo_gap を優先する（排他）。
    """
    memoed = [r for r in records if r.memo]
    if len(memoed) < 2:
        return None

    longest = max(memoed, key=lambda r: (r.memo_length, r.logged_date))
    if longest.memo_length < DISCOVERY_MEMO_MIN:
        return None

    ratings = [r.rating for r in records if r.rating is not None]
    top_rating = max(ratings) if ratings else None

    # 評価が未入力だと「評価は◯だったけれど」と言えないので longest_memo にする
    if (
        longest.rating is not None
        and top_rating is not None
        and longest.rating < top_rating
    ):
        return (
            "memo_gap",
            {"rating": longest.rating, "title": longest.title},
            {longest},
        )

    return ("longest_memo", {"title": longest.title}, {longest})


def _long_wait(records: list) -> tuple | None:
    """優先2：気になるに入れてから、実際に見るまでが長かったもの。"""
    waited = [
        (r, (r.logged_date - r.wished_at.date()).days)
        for r in records
        if getattr(r, "wished_at", None) is not None
    ]
    waited = [(r, days) for r, days in waited if days >= DISCOVERY_WAIT_DAYS]
    if not waited:
        return None

    record, days = max(waited, key=lambda pair: (pair[1], pair[0].logged_date))
    return ("long_wait", {"title": record.title, "days": days}, {record})


def _reunion(records: list, past: list) -> tuple | None:
    """優先3：同じ作り手を前にも記録していたこと。

    「2回目です」と言い切るため、過去の登場がちょうど1件のときだけ成立させる。
    3回目以降に「2回目です」と出すと事実が違ってしまう（要件23-4：外さない）。
    """
    for record in sorted(records, key=lambda r: r.logged_date, reverse=True):
        creator = (record.creator or "").strip()
        if not creator:
            continue

        earlier = [p for p in past if (p.creator or "").strip() == creator]
        if len(earlier) != 1:
            continue

        previous = earlier[0]
        return (
            "reunion",
            {
                "creator": creator,
                "year": previous.logged_date.year,
                "month": previous.logged_date.month,
            },
            {record},
        )
    return None


def _busy_day(records: list) -> tuple | None:
    """優先4：1日にまとめて記録した日があること。"""
    counts: dict[date, int] = {}
    for record in records:
        counts[record.logged_date] = counts.get(record.logged_date, 0) + 1

    busiest = max(counts.items(), key=lambda kv: (kv[1], kv[0]), default=None)
    if busiest is None or busiest[1] < DISCOVERY_BUSY_MIN:
        return None

    day, count = busiest
    # 日についての発見なので、特定の記録は占有しない
    return ("busy_day", {"month": day.month, "day": day.day, "count": count}, set())


def _first_category(
    records: list, past: list, label_rule_id: str | None
) -> tuple | None:
    """優先5：過去に記録のないカテゴリが出たこと。

    ひとことラベル（22章）が同じ素材を使っている場合は出さない（要件23-5）。
    """
    if label_rule_id == "first":
        return None

    known = {r.category for r in past}
    for record in sorted(records, key=lambda r: r.logged_date):
        if record.category not in known:
            label = CATEGORY_LABELS.get(record.category, record.category)
            # カテゴリについての発見なので、特定の記録は占有しない
            return ("first_category", {"category": label}, set())
    return None


def _bookends(records: list) -> tuple | None:
    """フォールバック：最初と最後（記録2件以上）。"""
    if len(records) < 2:
        return None

    ordered = sorted(records, key=_chronological_key)
    first, last = ordered[0], ordered[-1]
    return (
        "bookends",
        {"first": first.title, "last": last.title},
        {first, last},
    )


def _only_one(records: list) -> tuple | None:
    """フォールバック：記録が1件だけのとき。

    「今月は特に発見がありませんでした」を出さないための最後の受け皿（要件23-6）。
    """
    if len(records) != 1:
        return None

    record = records[0]
    return ("only_one", {"title": record.title}, {record})


def _chronological_key(record) -> tuple:
    """同じ日の中の前後は created_at で決める。無ければ日付だけで比べる。"""
    created = getattr(record, "created_at", None)
    return (record.logged_date, created is not None, created)
