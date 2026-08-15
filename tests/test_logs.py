"""記録CRUDのスモークテスト（要件F-01〜F-05）。"""
from datetime import date

from tests.conftest import TEST_PASSWORD


def test_create_and_list(auth_client, db):
    from app.models import Content

    res = auth_client.post(
        "/logs",
        data={
            "category": "stage",
            "title": "テスト舞台",
            "creator": "劇団テスト",
            "rating": "4",
            "memo": "よかった",
            "logged_date": "2026-08-10",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert Content.query.count() == 1

    c = Content.query.first()
    assert c.category == "stage"
    assert c.title == "テスト舞台"
    assert c.rating == 4


def test_create_without_rating(auth_client, db):
    """評価未入力でも保存できる（必須はカテゴリとタイトルのみ）。"""
    from app.models import Content

    auth_client.post(
        "/logs",
        data={"category": "book", "title": "無評価の本", "logged_date": "2026-08-11"},
        follow_redirects=True,
    )
    c = Content.query.first()
    assert c is not None
    assert c.rating is None


def test_title_required(auth_client, db):
    """タイトル未入力は保存されない。"""
    from app.models import Content

    auth_client.post(
        "/logs",
        data={"category": "book", "title": "", "logged_date": "2026-08-11"},
    )
    assert Content.query.count() == 0


def test_edit_updates(auth_client, db):
    from app.models import Content

    auth_client.post(
        "/logs",
        data={"category": "book", "title": "旧タイトル", "logged_date": "2026-08-01"},
    )
    c = Content.query.first()
    auth_client.post(
        f"/logs/{c.id}",
        data={"category": "movie", "title": "新タイトル", "logged_date": "2026-08-01"},
    )
    updated = db.session.get(Content, c.id)
    assert updated.title == "新タイトル"
    assert updated.category == "movie"


def test_delete_removes(auth_client, db):
    from app.models import Content

    auth_client.post(
        "/logs",
        data={"category": "book", "title": "消す本", "logged_date": "2026-08-01"},
    )
    c = Content.query.first()
    auth_client.post(f"/logs/{c.id}/delete")
    assert Content.query.count() == 0


def test_summary_page_renders(auth_client):
    """指定週のまとめが表示される（0件でもエラーにならない）。"""
    res = auth_client.get("/summary/2026/8/10")  # 月曜
    assert res.status_code == 200


def test_summary_normalizes_to_week_start(auth_client, db):
    """週の途中の日を指定しても、その週（月〜日）が集計される。"""
    from app.models import Content

    # 2026/8/10(月)〜8/16(日) の週。境界の外側も置いて漏れを確認する。
    # 画面にタイトルが出るのはお気に入り欄だけなので、評価をつけておく。
    for day, title in [(9, "前の週"), (10, "月曜"), (16, "日曜"), (17, "次の週")]:
        db.session.add(
            Content(
                category="book",
                title=title,
                rating=5,
                logged_date=date(2026, 8, day),
            )
        )
    db.session.commit()

    body = auth_client.get("/summary/2026/8/13").get_data(as_text=True)  # 木曜
    assert "月曜" in body and "日曜" in body
    assert "前の週" not in body and "次の週" not in body


def test_summary_current_redirects(auth_client):
    res = auth_client.get("/summary")
    assert res.status_code == 302


def test_summary_old_month_url_redirects(auth_client):
    """旧・月別URLは、その月の1日を含む週へリダイレクトする。"""
    res = auth_client.get("/summary/2026/8")
    assert res.status_code == 302
    assert res.headers["Location"].endswith("/summary/2026/7/27")  # 8/1(土)の週の月曜


def test_summary_rejects_invalid_date(auth_client):
    res = auth_client.get("/summary/2026/2/30")
    assert res.status_code == 404
