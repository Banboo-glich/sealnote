"""集計ロジック（要件11章）。

build_summary() は「記録のリストを受け取り、集計結果の辞書を返す」純粋関数。
DBに触れない。テストしやすく、将来の年間まとめでも再利用できる。
お気に入りの判定は要件5章に従う。
"""
from __future__ import annotations

from datetime import date
from typing import Iterable, Any

from ..constants import CATEGORY_KEYS
from .discoveries import build_discoveries


def build_summary(
    items: Iterable[Any],
    prev_total: int | None = None,
    all_records: Iterable[Any] | None = None,
    label_rule_id: str | None = None,
    period_start: "date | None" = None,
) -> dict:
    """記録のリストから、まとめ画面に必要な集計結果を返す。

    引数:
        items: Content 相当のオブジェクト列。各要素は
            .title(str), .category(str), .creator(str|None), .rating(int|None),
            .memo(str|None), .logged_date(date), .memo_length(int),
            .wished_at(datetime|None) を持つ。
            呼び出し側で status="done" に絞ってあることを前提とする。
        prev_total: 前の期間（前週）の総記録数。差分の計算用。無ければ None。
        all_records: 全期間の記録（発見の reunion / first_category 用）。
            None は「履歴が不明」を意味する。詳細は build_discoveries を参照。
        label_rule_id: ひとことラベル（22章）で採用されたルールID。
        period_start: 集計期間の初日（週の月曜）。発見の「過去」の基準になる。

    戻り値の辞書キー:
        total_count: 総記録数
        active_days: 記録があった日数
        by_category: [(key, count), ...] 件数の降順（0件カテゴリは除く）
        top_category: 最も多かったカテゴリの key（同数は要件順で先勝ち）。無ければ None
        favorites: お気に入り上位3件（Contentオブジェクトのリスト）
        prev_total: 前の期間の総記録数（引数のまま。None可）
        diff: total_count - prev_total（prev_total が None なら None）
        from_wish_count: そのうち気になるリスト経由で見た件数（要件21-9）
        discoveries: 発見 0〜2件（要件23章）
    """
    items = list(items)

    total_count = len(items)
    active_days = len({item.logged_date for item in items})

    # --- カテゴリ別件数（降順）---
    counts: dict[str, int] = {}
    for item in items:
        counts[item.category] = counts.get(item.category, 0) + 1

    # 件数降順。同数のときは要件のカテゴリ順（CATEGORY_KEYS）で安定させる。
    order = {key: i for i, key in enumerate(CATEGORY_KEYS)}
    by_category = sorted(
        counts.items(),
        key=lambda kv: (-kv[1], order.get(kv[0], len(order))),
    )

    top_category = by_category[0][0] if by_category else None

    favorites = _pick_favorites(items, limit=3)

    diff = None if prev_total is None else total_count - prev_total

    # 気になるリスト経由で見た件数（要件21-9）。
    # 残っている件数は数えない。未消化を数字で見せると振り返りが未達成の確認になるため。
    from_wish_count = sum(
        1 for item in items if getattr(item, "wished_at", None) is not None
    )

    return {
        "total_count": total_count,
        "active_days": active_days,
        "by_category": by_category,
        "top_category": top_category,
        "favorites": favorites,
        "prev_total": prev_total,
        "diff": diff,
        "from_wish_count": from_wish_count,
        "discoveries": build_discoveries(
            items,
            all_records=all_records,
            label_rule_id=label_rule_id,
            period_start=period_start,
        ),
    }


def _pick_favorites(items: list, limit: int = 3) -> list:
    """お気に入り判定（要件5章）。

    優先順位:
        1. 評価の降順
        2. 同点ならメモの文字数の降順
        3. それも同点なら記録日の降順
    評価が未入力（None）の記録は候補に含めない。
    """
    rated = [item for item in items if item.rating is not None]
    rated.sort(
        key=lambda item: (item.rating, item.memo_length, item.logged_date),
        reverse=True,
    )
    return rated[:limit]
