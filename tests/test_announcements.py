import pytest
from fastapi import HTTPException

from backend.app import main
from backend.app.okx import OkxError


def reset_announcement_cache():
    with main.announcement_cache_lock:
        main.announcement_types_cache.clear()
        main.announcements_cache.clear()


def test_announcement_normalization_validates_inputs():
    assert main.normalize_announcement_language("") == "zh-CN"
    assert main.normalize_announcement_language("en") == "en-US"
    assert main.normalize_announcement_type_filter("announcements-api") == "announcements-api"
    assert main.normalize_announcement_page(1) == 1

    with pytest.raises(HTTPException):
        main.normalize_announcement_language("fr-FR")
    with pytest.raises(HTTPException):
        main.normalize_announcement_type_filter("../bad")
    with pytest.raises(HTTPException):
        main.normalize_announcement_page(0)


def test_cached_announcement_types_uses_cache_and_public_source(monkeypatch):
    reset_announcement_cache()
    monkeypatch.setattr(main, "now_ms", lambda: 100000)
    calls = {"count": 0}

    class FakeClient:
        def get_announcement_types(self, language):
            calls["count"] += 1
            assert language == "zh-CN"
            return [{"annType": "announcements-api", "annTypeDesc": "API 公告"}]

    monkeypatch.setattr(main, "client", FakeClient())

    first = main.cached_announcement_types("zh-CN", force=False)
    second = main.cached_announcement_types("zh-CN", force=False)

    assert calls["count"] == 1
    assert first["source"] == "okx-announcement-types"
    assert second["source"] == "announcement-types-cache"
    assert second["data"] == [{"annType": "announcements-api", "annTypeDesc": "API 公告"}]


def test_cached_announcement_types_falls_back_to_stale_cache(monkeypatch):
    reset_announcement_cache()
    monkeypatch.setattr(main, "now_ms", lambda: 200000)

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get_announcement_types(self, _language):
            self.calls += 1
            if self.calls == 1:
                return [{"annType": "announcements-api", "annTypeDesc": "API 公告"}]
            raise OkxError("OKX API error 50011: 请求频率过快")

    fake_client = FakeClient()
    monkeypatch.setattr(main, "client", fake_client)

    first = main.cached_announcement_types("zh-CN", force=True)
    second = main.cached_announcement_types("zh-CN", force=True)

    assert first["source"] == "okx-announcement-types"
    assert second["source"] == "announcement-types-stale-cache"
    assert second["data"][0]["annType"] == "announcements-api"
    assert "50011" in second["warning"]


def test_cached_announcement_types_uses_default_types_without_cache(monkeypatch):
    reset_announcement_cache()
    monkeypatch.setattr(main, "now_ms", lambda: 250000)

    class FakeClient:
        def get_announcement_types(self, _language):
            raise OkxError("OKX API error 50011: 请求频率过快")

    monkeypatch.setattr(main, "client", FakeClient())

    payload = main.cached_announcement_types("zh-CN", force=True)

    assert payload["source"] == "announcement-types-default"
    assert any(item["annType"] == "announcements-api" for item in payload["data"])
    assert "50011" in payload["warning"]


def test_cached_announcements_normalizes_and_falls_back_by_page(monkeypatch):
    reset_announcement_cache()
    monkeypatch.setattr(main, "now_ms", lambda: 300000)

    class FakeClient:
        def __init__(self):
            self.calls = 0

        def get_announcements(self, ann_type, page, language):
            self.calls += 1
            assert ann_type == "announcements-api"
            assert page == 2
            assert language == "zh-CN"
            if self.calls == 1:
                return {
                    "details": [
                        {
                            "annType": "announcements-api",
                            "title": "欧易 WebSocket 订单频道推送行为调整公告",
                            "url": "https://www.okx.com/zh-hans/help/api-update",
                            "pTime": "1784193754036",
                            "businessPTime": "1784131200000",
                        }
                    ],
                    "totalPage": "3",
                }
            raise OkxError("OKX API error 50011: 请求频率过快")

    fake_client = FakeClient()
    monkeypatch.setattr(main, "client", fake_client)

    first = main.cached_announcements("announcements-api", 2, "zh-CN", force=True)
    second = main.cached_announcements("announcements-api", 2, "zh-CN", force=True)

    assert first["source"] == "okx-announcements"
    assert first["page"] == 2
    assert first["totalPage"] == 3
    assert first["data"][0]["pTime"] == 1784193754036
    assert second["source"] == "announcements-stale-cache"
    assert second["data"][0]["title"] == "欧易 WebSocket 订单频道推送行为调整公告"
    assert "50011" in second["warning"]


def test_announcement_routes_are_get_only():
    routes = [route for route in main.app.routes if getattr(route, "path", "").startswith("/api/announcements")]

    assert {route.path for route in routes} == {"/api/announcements/types", "/api/announcements"}
    assert all(getattr(route, "methods", set()) == {"GET"} for route in routes)
