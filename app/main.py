"""ホーム画面（要件F-06）。

今日の記録・累計・まとめへの導線を表示する。
"""
from datetime import date

from flask import Blueprint, render_template
from sqlalchemy import func

from . import db
from .auth import login_required
from .models import Content
from .constants import STATUS_DONE

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def home():
    today = date.today()

    # 気になる項目（status="wish"）はシールではないので、どの数にも含めない（要件21-5）
    total = (
        db.session.query(func.count(Content.id))
        .filter(Content.status == STATUS_DONE)
        .scalar()
        or 0
    )
    today_count = (
        db.session.query(func.count(Content.id))
        .filter(Content.status == STATUS_DONE, Content.logged_date == today)
        .scalar()
        or 0
    )
    # 最近貼ったシール数枚（ホームの気配用）
    recent = (
        Content.query.filter(Content.status == STATUS_DONE)
        .order_by(Content.logged_date.desc(), Content.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "home.html",
        total=total,
        today_count=today_count,
        recent=recent,
    )
