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
from ..constants import CATEGORY_KEYS, STATUS_DONE
from ..utils import clean_text

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

    # 気になる項目は一覧に出さない（要件21-5）
    query = Content.query.filter(
        Content.status == STATUS_DONE,
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
    return render_template(
        "log_form.html", form=form, mode="new", action=url_for("logs.create")
    )


@bp.route("/logs", methods=["POST"])
@login_required
def create():
    """保存（F-01）。"""
    form = ContentForm()
    if form.validate_on_submit():
        content = Content(
            category=form.category.data,
            title=form.title.data.strip(),
            creator=clean_text(form.creator.data),
            rating=form.rating_value(),
            memo=clean_text(form.memo.data),
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
    return render_template(
        "log_form.html", form=form, mode="new", action=url_for("logs.create")
    )


@bp.route("/logs/<int:log_id>/edit")
@login_required
def edit(log_id: int):
    """編集フォーム（F-03）。"""
    content = _get_done_or_404(log_id)
    form = ContentForm(obj=content)
    # rating は文字列選択なので明示的に詰め直す
    form.rating.data = "" if content.rating is None else str(content.rating)
    return render_template(
        "log_form.html",
        form=form,
        mode="edit",
        content=content,
        action=url_for("logs.update", log_id=content.id),
    )


@bp.route("/logs/<int:log_id>", methods=["POST"])
@login_required
def update(log_id: int):
    """更新（F-03）。"""
    content = _get_done_or_404(log_id)
    form = ContentForm()
    if form.validate_on_submit():
        content.category = form.category.data
        content.title = form.title.data.strip()
        content.creator = clean_text(form.creator.data)
        content.rating = form.rating_value()
        content.memo = clean_text(form.memo.data)
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
    return render_template(
        "log_form.html",
        form=form,
        mode="edit",
        content=content,
        action=url_for("logs.update", log_id=content.id),
    )


@bp.route("/logs/<int:log_id>/delete", methods=["POST"])
@login_required
def delete(log_id: int):
    """削除（F-04）。確認は画面側のダイアログで行う。"""
    content = _get_done_or_404(log_id)
    year, month = content.logged_date.year, content.logged_date.month
    db.session.delete(content)
    db.session.commit()
    flash("シールをはがしました", "success")
    return redirect(url_for("logs.index", year=year, month=month))


# --- ヘルパ ---
def _get_done_or_404(log_id: int) -> Content:
    """記録（done）だけを取り出す。

    気になる項目（wish）はまだシールではないので、記録用の画面では扱わない。
    /logs/<id>/edit などに wish のIDを渡しても404にする（要件21-5）。
    """
    content = db.session.get(Content, log_id)
    if content is None or content.status != STATUS_DONE:
        abort(404)
    return content


def _int_arg(name: str, default: int) -> int:
    try:
        return int(request.args.get(name, default))
    except (TypeError, ValueError):
        return default


