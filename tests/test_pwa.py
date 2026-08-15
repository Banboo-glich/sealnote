"""PWA関連のテスト（要件16章）。"""
import json


def test_manifest_returns_200_and_valid_json(client):
    """manifest.json が200で返り、JSONとして読めること。"""
    res = client.get("/static/manifest.json")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["name"] == "シールノート"
    assert data["start_url"] == "/"
    assert data["display"] == "standalone"
    assert data["theme_color"] == "#C4848F"
    assert data["background_color"] == "#FBF8F7"
    # アイコンに192と512が含まれること
    sizes = {icon["sizes"] for icon in data["icons"]}
    assert "192x192" in sizes
    assert "512x512" in sizes


def test_service_worker_served(client):
    """sw.js が配信されること。"""
    res = client.get("/static/sw.js")
    assert res.status_code == 200
