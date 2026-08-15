"""アプリケーションファクトリ（要件11・15章）。

create_app() で拡張を初期化し、Blueprint を登録する。
"""
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- 拡張のインスタンス（アプリ非依存で先に作る）---
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",  # ストレージを明示（要件11章）
    default_limits=[],  # 既定の制限はかけない。ログインにだけ個別に付ける
)


def create_app(config_name: str | None = None) -> Flask:
    from .config import resolve_config

    app = Flask(__name__)

    config_name = config_name or os.environ.get("FLASK_ENV")
    config_class = resolve_config(config_name)
    app.config.from_object(config_class)

    # --- 必須の環境変数チェック（要件15章 Phase5 の受け入れ基準）---
    # テスト時は既定値を使うので免除する。
    if not app.config.get("TESTING"):
        _require_config(app)
        # DATABASE_URL 未指定ならローカル data/ にフォールバック
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            data_dir = os.path.join(app.root_path, "..", "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.abspath(os.path.join(data_dir, "sealnote.db"))
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    # --- 拡張の初期化 ---
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    # モデルを import してマイグレーションに認識させる
    from . import models  # noqa: F401

    # --- Blueprint 登録 ---
    from .auth import bp as auth_bp
    from .main import bp as main_bp
    from .logs.routes import bp as logs_bp
    from .summary.routes import bp as summary_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(summary_bp)

    # --- テンプレートで使う定数を注入 ---
    from .constants import CATEGORY_LABELS, CATEGORIES

    @app.context_processor
    def inject_categories():
        return {"CATEGORY_LABELS": CATEGORY_LABELS, "CATEGORIES": CATEGORIES}

    # --- エラーページ ---
    from flask import render_template

    @app.errorhandler(429)
    def too_many_requests(e):
        # レート制限超過（要件8章：429を返す）
        return render_template("429.html"), 429

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app


def _require_config(app: Flask) -> None:
    """SECRET_KEY / APP_PASSWORD_HASH が無ければ起動を止める（要件12・15章）。"""
    missing = [
        name
        for name in ("SECRET_KEY", "APP_PASSWORD_HASH")
        if not app.config.get(name)
    ]
    if missing:
        raise RuntimeError(
            "必須の環境変数が未設定です: "
            + ", ".join(missing)
            + "。.env を確認してください（.env.example 参照）。"
        )
