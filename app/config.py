"""設定クラス。

要件12章のセキュリティ要件に従う。
- SECRET_KEY / APP_PASSWORD_HASH は環境変数から読む（未設定なら起動失敗）
- 本番は DEBUG=False、Secure Cookie
"""
import os
from datetime import timedelta


class Config:
    """共通設定。"""

    # --- 必須の環境変数（未設定なら create_app で起動を止める）---
    SECRET_KEY = os.environ.get("SECRET_KEY")
    APP_PASSWORD_HASH = os.environ.get("APP_PASSWORD_HASH")

    # --- データベース ---
    # 未指定ならプロジェクト内 data/ にフォールバック（ローカル開発用）。
    # 本番は .env の DATABASE_URL（絶対パス・スラッシュ4本）を使う。
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- セッション ---
    # ログインの有効期限は30日（毎回のログインを避ける・要件8章）
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # --- Cookie セキュリティ（要件12章）---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # SECURE は本番のみ True（ローカルhttpでもログインできるように）
    SESSION_COOKIE_SECURE = False

    # --- CSRF（Flask-WTF）---
    WTF_CSRF_ENABLED = True

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # HTTPS必須（PythonAnywhere Force HTTPS）


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False  # テストではCSRFを無効化
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # テストでは環境変数に依存しない既定値を用意する
    SECRET_KEY = "test-secret-key"
    # テスト用パスワード "test" のハッシュは conftest で上書きする
    APP_PASSWORD_HASH = None


def resolve_config(name: str | None) -> type[Config]:
    """FLASK_ENV / 引数から設定クラスを決める。"""
    mapping = {
        "production": ProductionConfig,
        "development": DevelopmentConfig,
        "testing": TestingConfig,
    }
    return mapping.get((name or "").lower(), DevelopmentConfig)
