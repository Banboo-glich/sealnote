"""気になるリストのテスト（要件21-11）。

最重要は「wish の行が既存画面のどこにも現れないこと」。
機能追加そのものより、この絞り込み漏れのほうが事故になりやすい。
"""
import re
from datetime import date, datetime

import pytest


@pytest.fixture
def wish(db):
    """DBに直接入れた気になる項目1件。"""
    from app.models import Content

    item = Content(
        category="book",
        title="まだ読んでいない本",
        creator="作者名",
        status="wish",
        wished_at=datetime(2026, 8, 10, 12, 0),
        logged_date=None,
    )
    db.session.add(item)
    db.session.commit()
    return item


# --- 7-2: 既存画面への非表示（最重要）---------------------------------


def test_wish_does_not_appear_on_home(auth_client, wish):
    body = auth_client.get("/").get_data(as_text=True)
    assert "まだ読んでいない本" not in body


def test_wish_not_counted_in_home_totals(auth_client, db, wish):
    """「これまで」「きょう」の数に混入しない。"""
    from app.models import Content

    db.session.add(
        Content(category="movie", title="見た映画", logged_date=date.today())
    )
    db.session.commit()

    body = auth_client.get("/").get_data(as_text=True)
    # 記録は1件だけ。wish を数えていれば 2 になる。
    assert '<span class="count__num">1</span>' in body


def test_wish_does_not_appear_in_list(auth_client, wish):
    body = auth_client.get("/logs?year=2026&month=8").get_data(as_text=True)
    assert "まだ読んでいない本" not in body


def test_wish_not_counted_in_summary(auth_client, db, wish):
    """まとめの集計に一切含めない（要件21-9）。"""
    from app.models import Content

    db.session.add(
        Content(category="movie", title="見た映画", logged_date=date(2026, 8, 12))
    )
    db.session.commit()

    body = auth_client.get("/summary/2026/8/12").get_data(as_text=True)
    assert "まだ読んでいない本" not in body
    assert '<span class="stat-card__num num">1</span>' in body


def test_wish_id_is_404_on_log_screens(auth_client, wish):
    """記録用の画面に wish のIDを渡しても404。"""
    assert auth_client.get(f"/logs/{wish.id}/edit").status_code == 404
    assert auth_client.post(f"/logs/{wish.id}/delete").status_code == 404


# --- 7-3: 一覧・追加・削除 --------------------------------------------


def test_add_wish_needs_only_two_fields(auth_client, db):
    """カテゴリとタイトルだけで追加できる（要件21-7）。"""
    from app.models import Content

    res = auth_client.post(
        "/wishes",
        data={"category": "movie", "title": "気になる映画"},
        follow_redirects=True,
    )
    assert res.status_code == 200

    item = Content.query.filter_by(title="気になる映画").one()
    assert item.status == "wish"
    assert item.wished_at is not None
    assert item.logged_date is None
    assert item.rating is None


def test_wish_list_shows_newest_first(auth_client, db):
    """並びは追加が新しい順のみ（要件21-10）。"""
    from app.models import Content

    for n, when in [("古いほう", datetime(2026, 8, 1)), ("新しいほう", datetime(2026, 8, 20))]:
        db.session.add(
            Content(category="book", title=n, status="wish", wished_at=when)
        )
    db.session.commit()

    body = auth_client.get("/wishes").get_data(as_text=True)
    assert body.index("新しいほう") < body.index("古いほう")


def test_wish_list_empty_message_is_inviting(auth_client):
    """空のときは「まだ何もありません」ではなく誘導文（要件21-10）。"""
    body = auth_client.get("/wishes").get_data(as_text=True)
    assert "気になったものを入れておけます" in body


def test_delete_wish(auth_client, db, wish):
    from app.models import Content

    auth_client.post(f"/wishes/{wish.id}/delete")
    assert Content.query.count() == 0


# --- 7-4: 変換 ---------------------------------------------------------


def _checked_radios(html: str) -> dict:
    """checked が付いている radio を {name: value} で返す。

    テンプレートでは checked が次の行に来るため、空白をつぶしてから読む。
    """
    flat = re.sub(r"\s+", " ", html)
    found = {}
    for m in re.finditer(r'<input type="radio" name="(\w+)" value="([^"]*)" ([^>]*)>', flat):
        if "checked" in m.group(3):
            found[m.group(1)] = m.group(2)
    return found


def test_convert_form_is_prefilled(auth_client, wish):
    """カテゴリ・タイトル・作り手が入力済みで出る（要件21-8）。"""
    body = auth_client.get(f"/wishes/{wish.id}/log").get_data(as_text=True)

    assert 'value="まだ読んでいない本"' in body
    assert 'value="作者名"' in body
    assert _checked_radios(body).get("category") == "book"


def test_convert_form_defaults_date_to_today_and_no_rating(auth_client, wish):
    """評価は未選択、日付は今日が初期値（要件21-8）。"""
    body = auth_client.get(f"/wishes/{wish.id}/log").get_data(as_text=True)

    assert _checked_radios(body).get("rating") == ""
    assert f'value="{date.today().isoformat()}"' in body


def test_convert_does_not_create_a_new_row(auth_client, db, wish):
    """行を増やさず、同じ行が done に変わる（要件21-8・21-11）。"""
    from app.models import Content

    wish_id = wish.id
    before = Content.query.count()

    auth_client.post(
        f"/wishes/{wish_id}/log",
        data={
            "category": "book",
            "title": "まだ読んでいない本",
            "creator": "作者名",
            "rating": "5",
            "memo": "よかった",
            "logged_date": "2026-08-15",
        },
    )

    assert Content.query.count() == before  # 増えていない
    item = db.session.get(Content, wish_id)  # 同じID
    assert item.status == "done"
    assert item.logged_date == date(2026, 8, 15)
    assert item.rating == 5
    assert item.memo == "よかった"


def test_convert_keeps_wished_at(auth_client, db, wish):
    """変換後も wished_at が残る（リスト経由だと分かるようにするため）。"""
    from app.models import Content

    wish_id = wish.id
    auth_client.post(
        f"/wishes/{wish_id}/log",
        data={
            "category": "book",
            "title": "まだ読んでいない本",
            "logged_date": "2026-08-15",
        },
    )
    assert db.session.get(Content, wish_id).wished_at == datetime(2026, 8, 10, 12, 0)


def test_converted_item_then_appears_in_list(auth_client, db, wish):
    """変換後は通常の記録として一覧に出る。"""
    auth_client.post(
        f"/wishes/{wish.id}/log",
        data={
            "category": "book",
            "title": "まだ読んでいない本",
            "logged_date": "2026-08-15",
        },
    )
    body = auth_client.get("/logs?year=2026&month=8").get_data(as_text=True)
    assert "まだ読んでいない本" in body


def test_done_id_is_404_on_convert(auth_client, db):
    """done のIDを /wishes/<id>/log で開くと404（要件21-11）。"""
    from app.models import Content

    item = Content(category="book", title="見た本", logged_date=date(2026, 8, 1))
    db.session.add(item)
    db.session.commit()

    assert auth_client.get(f"/wishes/{item.id}/log").status_code == 404
    assert auth_client.post(f"/wishes/{item.id}/log").status_code == 404


# --- 7-5: まとめへの1行 ------------------------------------------------


def test_summary_shows_converted_count(auth_client, db):
    from app.models import Content

    db.session.add(
        Content(
            category="book",
            title="リスト経由",
            logged_date=date(2026, 8, 12),
            wished_at=datetime(2026, 8, 1),
        )
    )
    db.session.add(
        Content(category="movie", title="直接記録", logged_date=date(2026, 8, 12))
    )
    db.session.commit()

    body = auth_client.get("/summary/2026/8/12").get_data(as_text=True)
    assert "気になるリストから" in body


def test_summary_hides_line_when_no_conversion(auth_client, db):
    """0件のときは行を出さない（要件21-13 7-5）。"""
    from app.models import Content

    db.session.add(
        Content(category="movie", title="直接記録", logged_date=date(2026, 8, 12))
    )
    db.session.commit()

    body = auth_client.get("/summary/2026/8/12").get_data(as_text=True)
    assert "気になるリストから" not in body


def test_summary_survives_with_only_wishes(auth_client, wish):
    """気になる項目しか無くても、まとめが例外を出さない（要件21-11）。"""
    assert auth_client.get("/summary/2026/8/10").status_code == 200


# --- 認証 --------------------------------------------------------------


def test_wishes_require_login(client):
    for path in ["/wishes", "/wishes/new"]:
        res = client.get(path)
        assert res.status_code in (302, 401), path
