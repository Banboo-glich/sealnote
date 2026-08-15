"""まとめ画面のルート（要件F-05, 6章）。

振り返りの単位は「週」（月曜はじまり・日曜おわり）。
- /summary は今週のまとめへリダイレクト
- /summary/<year>/<month>/<day> で、その日を含む週のまとめ
- 前週・翌週リンク。0件の週へのリンクは無効表示にする
- /summary/<year>/<month> は旧URL。その月の1日を含む週へリダイレクトする
"""
from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, abort

from .. import db
from ..auth import login_required
from ..models import Content
from ..constants import STATUS_DONE
from .service import build_summary

bp = Blueprint("summary", __name__)


@bp.route("/summary")
@login_required
def current():
    return redirect(_week_url(date.today()))


@bp.route("/summary/<int:year>/<int:month>")
@login_required
def month(year: int, month: int):
    """旧・月別まとめのURL。ブックマーク救済のためのリダイレクトのみ。"""
    if not (1 <= month <= 12):
        abort(404)
    try:
        first = date(year, month, 1)
    except ValueError:
        abort(404)
    return redirect(_week_url(first))


@bp.route("/summary/<int:year>/<int:month>/<int:day>")
@login_required
def week(year: int, month: int, day: int):
    try:
        target = date(year, month, day)
    except ValueError:
        abort(404)

    start = _week_start(target)
    end = start + timedelta(days=6)

    items = _items_between(start, end)

    # 先週比のため前週の総数を数える
    prev_start = start - timedelta(days=7)
    prev_end = start - timedelta(days=1)
    prev_total = _count_between(prev_start, prev_end)

    summary = build_summary(
        items,
        prev_total=prev_total,
        # 発見の reunion / first_category 用。週の前にある記録だけを、
        # 必要な列だけ読む（全行をオブジェクトで持たない）。
        all_records=_history_before(start),
        period_start=start,
    )

    next_start = start + timedelta(days=7)
    next_end = next_start + timedelta(days=6)

    return render_template(
        "summary.html",
        summary=summary,
        start=start,
        end=end,
        prev_start=prev_start,
        prev_end=prev_end,
        next_start=next_start,
        next_end=next_end,
        prev_has=prev_total > 0,
        next_has=_count_between(next_start, next_end) > 0,
    )


# --- ヘルパ ---
def _week_start(day: date) -> date:
    """その日を含む週の月曜日を返す。"""
    return day - timedelta(days=day.weekday())


def _week_url(day: date) -> str:
    start = _week_start(day)
    return url_for("summary.week", year=start.year, month=start.month, day=start.day)


def _items_between(start: date, end: date) -> list:
    # 気になる項目は集計に一切含めない（要件21-5・21-9）
    return (
        Content.query.filter(
            Content.status == STATUS_DONE,
            Content.logged_date >= start,
            Content.logged_date <= end,
        )
        .order_by(Content.logged_date.desc(), Content.created_at.desc())
        .all()
    )


def _history_before(start: date) -> list:
    """その週より前の記録の履歴（要件23章の発見で使う）。

    使うのは作り手・カテゴリ・記録日だけなので、その3列に絞って読む。
    空リストは「調べた結果、過去の記録が無かった」を意味する（None とは違う）。
    """
    return (
        db.session.query(
            Content.category, Content.creator, Content.logged_date
        )
        .filter(
            Content.status == STATUS_DONE,
            Content.logged_date < start,
        )
        .all()
    )


def _count_between(start: date, end: date) -> int:
    return (
        db.session.query(db.func.count(Content.id))
        .filter(
            Content.status == STATUS_DONE,
            Content.logged_date >= start,
            Content.logged_date <= end,
        )
        .scalar()
        or 0
    )
