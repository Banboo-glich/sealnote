"""pytest 共通フィクスチャ。"""
import pytest
from werkzeug.security import generate_password_hash

from app import create_app, db as _db, limiter

TEST_PASSWORD = "himitsu"


@pytest.fixture
def app():
    app = create_app("testing")
    # テスト用パスワードのハッシュを注入（平文はコードに残さない方針だが、
    # テスト内で生成するため問題ない）
    app.config["APP_PASSWORD_HASH"] = generate_password_hash(TEST_PASSWORD)

    with app.app_context():
        _db.create_all()
        # レート制限のカウンタをテストごとにリセット（メモリ共有のため）
        try:
            limiter.reset()
        except Exception:
            pass
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(app):
    """ログイン済みのクライアント。"""
    client = app.test_client()
    client.post("/login", data={"password": TEST_PASSWORD})
    return client


@pytest.fixture
def db(app):
    return _db
