"""気になるリスト（要件21章）。

まだ見ていないものを溜めておき、「見た」で記録（シール）に変換する。
変換は行をコピーせず、同じ行の status を変えるだけ（要件21-8）。

編集機能は作らない。書き直したいときは消して入れ直す（要件21-6）。
"""
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, abort, flash

from .. import db
from ..auth import login_required
from ..models import Content
from ..forms import WishForm, ContentForm
from ..constants import STATUS_WISH, STATUS_DONE
from ..utils import clean_text

bp = Blueprint("wishes", __name__)


@bp.route("/wishes")
@login_required
def index():
    """一覧（要件21-10）。

    並びは追加が新しい順のみ。古い順にすると、消化されていないものが
    上に来て未消化の確認になるため。件数バッジや経過日数も出さない。
    """
    items = (
        Content.query.filter(Content.status == STATUS_WISH)
        .order_by(Content.wished_at.desc(), Content.id.desc())
        .all()
    )
    return render_template("wishes_list.html", items=items)


@bp.route("/wishes/new")
@login_required
def new():
    return render_template("wish_form.html", form=WishForm())


@bp.route("/wishes", methods=["POST"])
@login_required
def create():
    form = WishForm()
    if form.validate_on_submit():
        wish = Content(
            category=form.category.data,
            title=form.title.data.strip(),
            creator=clean_text(form.creator.data),
            status=STATUS_WISH,
            wished_at=datetime.utcnow(),
            # まだ見ていないので記録日・評価・メモは持たない（要件21-3）
            logged_date=None,
            rating=None,
            memo=None,
        )
        db.session.add(wish)
        db.session.commit()
        flash("気になるに入れました", "success")
        return redirect(url_for("wishes.index"))
    return render_template("wish_form.html", form=form)


@bp.route("/wishes/<int:wish_id>/delete", methods=["POST"])
@login_required
def delete(wish_id: int):
    wish = _get_wish_or_404(wish_id)
    db.session.delete(wish)
    db.session.commit()
    flash("消しました", "success")
    return redirect(url_for("wishes.index"))


@bp.route("/wishes/<int:wish_id>/log")
@login_required
def log(wish_id: int):
    """変換フォーム（要件21-8）。通常の記録フォームを入力済みの状態で出す。"""
    wish = _get_wish_or_404(wish_id)
    form = ContentForm()
    form.prefill_from(wish)
    return render_template(
        "log_form.html",
        form=form,
        mode="convert",
        content=wish,
        action=url_for("wishes.log_save", wish_id=wish.id),
    )


@bp.route("/wishes/<int:wish_id>/log", methods=["POST"])
@login_required
def log_save(wish_id: int):
    """変換の保存（要件21-8）。

    新しい行は作らない。同じ行の status を done に変え、
    logged_date・rating・memo を書き込む。
    wished_at は消さずに残す（リスト経由で見たものだと分かるようにするため）。
    """
    wish = _get_wish_or_404(wish_id)
    form = ContentForm()
    if form.validate_on_submit():
        wish.category = form.category.data
        wish.title = form.title.data.strip()
        wish.creator = clean_text(form.creator.data)
        wish.rating = form.rating_value()
        wish.memo = clean_text(form.memo.data)
        wish.logged_date = form.logged_date.data
        wish.status = STATUS_DONE
        db.session.commit()
        flash("シールを貼りました", "success")
        return redirect(url_for("main.home"))

    return render_template(
        "log_form.html",
        form=form,
        mode="convert",
        content=wish,
        action=url_for("wishes.log_save", wish_id=wish.id),
    )


# --- ヘルパ ---
def _get_wish_or_404(wish_id: int) -> Content:
    """気になる項目だけを取り出す。

    すでに記録済み（done）のIDを渡された場合も404にする（要件21-6）。
    二重に変換されるのを防ぐ。
    """
    content = db.session.get(Content, wish_id)
    if content is None or content.status != STATUS_WISH:
        abort(404)
    return content
