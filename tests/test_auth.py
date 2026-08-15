"""認証・レート制限のテスト（要件16章・最重要）。"""
from tests.conftest import TEST_PASSWORD


def test_unauthenticated_redirects_to_login(client):
    """未認証で / にアクセスすると /login へ遷移する。"""
    res = client.get("/")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]


def test_wrong_password_rejected(client):
    """誤ったパスワードでは入れない（認証フラグが立たない）。"""
    res = client.post("/login", data={"password": "wrong"}, follow_redirects=False)
    # ログインページを再表示（リダイレクトしない）
    assert res.status_code == 200
    # 続けて / を見ると、まだ未認証なのでリダイレクトされる
    res2 = client.get("/")
    assert res2.status_code == 302
    assert "/login" in res2.headers["Location"]


def test_correct_password_grants_access(client):
    """正しいパスワードで認証され、/ が見られる。"""
    res = client.post("/login", data={"password": TEST_PASSWORD})
    assert res.status_code == 302  # ホームへ
    res2 = client.get("/")
    assert res2.status_code == 200


def test_rate_limit_returns_429(client):
    """同一IPから10回を超える試行で429（要件8章）。"""
    codes = []
    for _ in range(11):
        r = client.post("/login", data={"password": "wrong"})
        codes.append(r.status_code)
    # 11回目までのどこかで429が返る（10 per 10 minutes）
    assert 429 in codes


def test_unauthenticated_post_does_not_change_data(client, db):
    """未認証のPOSTでデータが変更されないこと（要件16章）。"""
    from app.models import Content

    res = client.post(
        "/logs",
        data={
            "category": "book",
            "title": "勝手に追加",
            "logged_date": "2026-08-15",
        },
    )
    # /login へ弾かれる
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]
    assert Content.query.count() == 0


def test_logout_requires_post(auth_client):
    """ログアウトはGET不可（要件6章）。"""
    res = auth_client.get("/logout")
    assert res.status_code == 405  # Method Not Allowed
