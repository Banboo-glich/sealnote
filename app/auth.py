"""認証（要件8章）。

単一パスワードによるゲート方式。ユーザー名は無い。Flask-Login は使わない。
- APP_PASSWORD_HASH と check_password_hash で照合
- セッションに認証フラグを保存（有効期限30日）
- ログイン試行はレート制限（10分に10回）
"""
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
    current_app,
)
from werkzeug.security import check_password_hash

from . import limiter
from .forms import LoginForm

bp = Blueprint("auth", __name__)

SESSION_KEY = "authenticated"


def is_authenticated() -> bool:
    return session.get(SESSION_KEY) is True


def login_required(view):
    """未認証なら /login へリダイレクトするデコレータ。"""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            # 元の遷移先を保持して、ログイン後に戻す（GETのみ）
            nxt = request.path if request.method == "GET" else None
            return redirect(url_for("auth.login", next=nxt))
        return view(*args, **kwargs)

    return wrapped


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per 10 minutes", methods=["POST"])  # 要件8章
def login():
    # すでに認証済みならホームへ
    if is_authenticated():
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        password_hash = current_app.config.get("APP_PASSWORD_HASH")
        if password_hash and check_password_hash(password_hash, form.password.data):
            session[SESSION_KEY] = True
            session.permanent = True  # 30日有効（config の LIFETIME）
            nxt = request.args.get("next")
            # オープンリダイレクト防止：同一サイト内のパスのみ許可
            if nxt and nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            return redirect(url_for("main.home"))
        flash("あいことばが ちがうみたい", "error")

    return render_template("login.html", form=form)


@bp.route("/logout", methods=["POST"])  # GET不可（要件6章）
def logout():
    session.pop(SESSION_KEY, None)
    return redirect(url_for("auth.login"))
