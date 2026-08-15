"""記録のCRUD（要件F-01〜F-04, 画面/URLは要件6章）。"""
from datetime import date

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    abort,
    flash,
)

from .. import db
from ..auth import login_required
from ..models import Content
from ..forms import ContentForm
from ..constants import CATEGORY_KEYS

bp = Blueprint("logs", __name__)


@bp.route("/logs")
@login_required
def index():
    """一覧（F-02）。引数なしなら今月。月別・カテゴリ別に絞り込み。"""
    today = date.today()
    year = _int_arg("year", today.year)
    month = _int_arg("month", today.month)
    category = request.args.get("category") or None
    if category not in CATEGORY_KEYS:
        category = None

    query = Content.query.filter(
        db.extract("year", Content.logged_date) == year,
        db.extract("month", Content.logged_date) == month,
    )
    if category:
        query = query.filter(Content.category == category)

    items = query.order_by(
        Content.logged_date.desc(), Content.created_at.desc()
    ).all()

    return render_template(
        "logs_list.html",
        items=items,
        year=year,
        month=month,
        category=category,
    )


@bp.route("/logs/new")
@login_required
def new():
    """入力フォーム（F-01）。記録日の初期値は今日。"""
    form = ContentForm()
    if not form.logged_date.data:
        form.logged_date.data = date.today()
    return render_template("log_form.html", form=form, mode="new")


@bp.route("/logs", methods=["POST"])
@login_required
def create():
    """保存（F-01）。"""
    form = ContentForm()
    if form.validate_on_submit():
        content = Content(
            category=form.category.data,
            title=form.title.data.strip(),
            creator=_clean(form.creator.data),
            rating=form.rating_value(),
            memo=_clean(form.memo.data),
            logged_date=form.logged_date.data,
        )
        db.session.add(content)
        db.session.commit()
        flash("シールを貼りました", "success")
        return redirect(
            url_for(
                "logs.index",
                year=content.logged_date.year,
                month=content.logged_date.month,
            )
        )
    return render_template("log_form.html", form=form, mode="new")


@bp.route("/logs/<int:log_id>/edit")
@login_required
def edit(log_id: int):
    """編集フォーム（F-03）。"""
    content = db.session.get(Content, log_id) or abort(404)
    form = ContentForm(obj=content)
    # rating は文字列選択なので明示的に詰め直す
    form.rating.data = "" if content.rating is None else str(content.rating)
    return render_template("log_form.html", form=form, mode="edit", content=content)


@bp.route("/logs/<int:log_id>", methods=["POST"])
@login_required
def update(log_id: int):
    """更新（F-03）。"""
    content = db.session.get(Content, log_id) or abort(404)
    form = ContentForm()
    if form.validate_on_submit():
        content.category = form.category.data
        content.title = form.title.data.strip()
        content.creator = _clean(form.creator.data)
        content.rating = form.rating_value()
        content.memo = _clean(form.memo.data)
        content.logged_date = form.logged_date.data
        db.session.commit()
        flash("シールを貼りなおしました", "success")
        return redirect(
            url_for(
                "logs.index",
                year=content.logged_date.year,
                month=content.logged_date.month,
            )
        )
    return render_template("log_form.html", form=form, mode="edit", content=content)


@bp.route("/logs/<int:log_id>/delete", methods=["POST"])
@login_required
def delete(log_id: int):
    """削除（F-04）。確認は画面側のダイアログで行う。"""
    content = db.session.get(Content, log_id) or abort(404)
    year, month = content.logged_date.year, content.logged_date.month
    db.session.delete(content)
    db.session.commit()
    flash("シールをはがしました", "success")
    return redirect(url_for("logs.index", year=year, month=month))


# --- ヘルパ ---
def _int_arg(name: str, default: int) -> int:
    try:
        return int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default


def _clean(value: str | None) -> str | None:
    """空文字は None に。前後の空白を除去。"""
    if value is None:
        return None
    value = value.strip()
    return value or None
