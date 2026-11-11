from backend.app import main
from backend.app.db import Database
from fastapi import HTTPException
import pytest


def test_us_event_candidate_keeps_unknown_time_and_forecast_empty():
    event = main.us_event_candidate(
        "Federal Reserve", "fomc-2026-09", "FOMC 会议与利率决议", "monetary",
        "https://example.test/fed", main.us_event_timestamp("September 16, 2026"), time_known=False,
    )
    assert event["forecast"] is None
    assert event["official"] is True
    assert '"timeKnown": false' in event["source_summary"]


def test_us_event_view_uses_persisted_events_after_provider_failure(monkeypatch, tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'events.sqlite3'}")
    db.init()
    event = main.us_event_candidate(
        "BLS", "cpi-2026-09-17", "Consumer Price Index", "inflation",
        "https://example.test/bls", main.us_event_timestamp("September 17, 2026", "08:30 AM"), time_known=True,
    )
    db.upsert_market_event(event)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "now_ms", lambda: 1_000_000)
    monkeypatch.setattr(main, "refresh_us_market_events_in_background", lambda: True)
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "providerStatuses": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})

    payload = main.market_us_events_view("2026-09-17", "2026-09-17", "inflation", "scheduled")
    assert payload["data"][0]["title"] == "Consumer Price Index"
    assert payload["data"][0]["forecast"] is None
    assert payload["refreshing"] is True
    assert payload["warnings"] == []


def test_expired_timeline_cache_starts_one_background_refresh(monkeypatch):
    started: list[bool] = []
    monkeypatch.setattr(main, "now_ms", lambda: 1_000_000)
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "providerStatuses": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})
    monkeypatch.setattr(main, "us_event_refreshing", False)

    class ImmediateThread:
        def __init__(self, *, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    def refresh(*, force=False):
        started.append(force)
        main.us_event_refresh_cache.update({"ts": 1_000_000, "warnings": [], "providers": ["BLS"], "providerStatuses": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})
        return main.us_event_refresh_cache

    monkeypatch.setattr(main, "Thread", ImmediateThread)
    monkeypatch.setattr(main, "refresh_us_market_events", refresh)

    assert main.refresh_us_market_events_in_background() is True
    assert started == [True]
    assert main.us_event_refreshing is False
    assert main.refresh_us_market_events_in_background() is False


def test_us_event_window_rejects_invalid_or_unbounded_ranges():
    with pytest.raises(HTTPException):
        main.market_us_events_view("bad", "2026-09-17")
    with pytest.raises(HTTPException):
        main.market_us_events_view("2026-01-01", "2026-03-01")
    with pytest.raises(HTTPException):
        main.market_us_events_view("2026-09-17", "2026-09-17", "unknown")


def test_fed_fixture_emits_only_explicit_calendar_sub_events():
    fixture = """
        January 27-28, 2026 FOMC Meeting Statement Press Conference Projection Materials
        Minutes released: February 18, 2026
    """
    events = main.parse_fed_timeline_events(fixture, "https://www.federalreserve.gov/example")
    titles = {event["title"] for event in events}
    assert titles == {
        "美联储利率决策（美国）", "美联储新闻发布会（美国）",
        "FOMC 经济预测（美国）", "FOMC 会议纪要",
    }
    assert all(event["forecast"] is None for event in events)
    assert all('"timeKnown": false' in event["source_summary"] for event in events)


def test_bls_bea_fixture_normalization_preserves_explicit_fields_only():
    bls = main.parse_us_event_schedule(
        "Thursday, September 17, 2026 08:30 AM Consumer Price Index", "BLS", "https://www.bls.gov/schedule/2026/",
        [("Consumer Price Index", "inflation")],
    )
    bea = main.parse_us_event_schedule(
        "September 25, 2026 08:30 AM Gross Domestic Product", "BEA", "https://www.bea.gov/news/schedule/full",
        [("Gross Domestic Product", "growth")],
    )
    assert [(event["title"], event["category"], event["forecast"]) for event in bls + bea] == [
        ("Consumer Price Index", "inflation", None), ("Gross Domestic Product", "growth", None),
    ]
    assert all('"timeKnown": true' in event["source_summary"] for event in bls + bea)


def test_bls_released_values_are_matched_to_the_latest_official_calendar_event(monkeypatch):
    release_at = main.us_event_timestamp("September 11, 2026", "08:30 AM")
    earlier_at = main.us_event_timestamp("August 12, 2026", "08:30 AM")
    assert release_at and earlier_at
    monkeypatch.setattr(main, "now_ms", lambda: release_at + 60_000)
    events = [
        main.us_event_candidate("BLS", "cpi-earlier", "Consumer Price Index", "inflation", "https://example.test/schedule", earlier_at, time_known=True),
        main.us_event_candidate("BLS", "cpi-release", "Consumer Price Index", "inflation", "https://example.test/schedule", release_at, time_known=True),
    ]
    monkeypatch.setattr(main, "load_bls_latest_series", lambda: {
        "Consumer Price Index": {
            "actual": "334.980",
            "previous": "333.918",
            "period_label": "2026 August",
            "unit": "CPI-U（1982-84=100）",
        }
    })

    released = main.enrich_bls_released_events(events)

    assert len(released) == 1
    event = released[0]
    assert event["provider_event_key"] == "cpi-release"
    assert event["state"] == "released"
    assert event["actual"] == "334.980"
    assert event["previous_value"] == "333.918"
    assert event["forecast"] is None
    assert event["source_url"] == main.BLS_RELEASE_DATA_URL


def test_bls_history_backfills_past_official_dates_in_observation_order(monkeypatch):
    july_release = main.us_event_timestamp("August 12, 2026", "08:30 AM")
    august_release = main.us_event_timestamp("September 11, 2026", "08:30 AM")
    assert july_release and august_release
    monkeypatch.setattr(main, "now_ms", lambda: august_release + 60_000)
    events = [
        main.us_event_candidate("BLS", "cpi-july", "Consumer Price Index", "inflation", "https://example.test/schedule", july_release, time_known=True),
        main.us_event_candidate("BLS", "cpi-august", "Consumer Price Index", "inflation", "https://example.test/schedule", august_release, time_known=True),
    ]

    released = main.enrich_bls_released_events(events, {
        "Consumer Price Index": [
            {"actual": "334.980", "previous": "333.918", "period_label": "2026 August", "unit": "CPI-U"},
            {"actual": "333.918", "previous": "332.608", "period_label": "2026 July", "unit": "CPI-U"},
        ]
    })

    assert [(event["provider_event_key"], event["actual"], event["previous_value"], event["period_label"]) for event in released] == [
        ("cpi-july", "333.918", "332.608", "2026 July"),
        ("cpi-august", "334.980", "333.918", "2026 August"),
    ]


def test_bls_uses_verified_calendar_cache_when_live_calendar_is_blocked(monkeypatch):
    now = main.us_event_timestamp("September 14, 2026")
    assert now
    monkeypatch.setattr(main, "now_ms", lambda: now)
    monkeypatch.setattr(main, "http_text_request", lambda *_args, **_kwargs: (_ for _ in ()).throw(main.OfficialSourceError("官方站点拒绝当前服务请求", "HTTP 403")))
    monkeypatch.setattr(main, "load_bls_series_history", lambda: {
        "Consumer Price Index": [
            {"actual": "334.980", "previous": "333.918", "period_label": "2026 August", "unit": "CPI-U"},
            {"actual": "333.918", "previous": "332.608", "period_label": "2026 July", "unit": "CPI-U"},
            {"actual": "332.608", "previous": "331.118", "period_label": "2026 June", "unit": "CPI-U"},
            {"actual": "331.118", "previous": "330.211", "period_label": "2026 May", "unit": "CPI-U"},
            {"actual": "330.211", "previous": "329.015", "period_label": "2026 April", "unit": "CPI-U"},
            {"actual": "329.015", "previous": "327.122", "period_label": "2026 March", "unit": "CPI-U"},
            {"actual": "327.122", "previous": "325.802", "period_label": "2026 February", "unit": "CPI-U"},
            {"actual": "325.802", "previous": "323.976", "period_label": "2026 January", "unit": "CPI-U"},
            {"actual": "323.976", "previous": "322.000", "period_label": "2025 December", "unit": "CPI-U"},
        ]
    })

    events = main.load_bls_timeline_events()
    september_cpi = next(event for event in events if event["provider_event_key"] == "consumer-price-index-2026-09-11" and event["state"] == "released")
    august_cpi = next(event for event in events if event["provider_event_key"] == "consumer-price-index-2026-08-12" and event["state"] == "released")
    assert september_cpi["actual"] == "334.980"
    assert august_cpi["actual"] == "333.918"
    assert september_cpi["source_url"] == main.BLS_RELEASE_DATA_URL


def test_bls_verified_calendar_cache_is_reported_as_retained(monkeypatch, tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'bls-schedule-cache.sqlite3'}")
    db.init()
    event = main.us_event_candidate(
        "BLS", "consumer-price-index-2026-08-12", "Consumer Price Index", "inflation",
        "https://www.bls.gov/schedule/news_release/cpi.htm", main.us_event_timestamp("August 12, 2026", "08:30 AM"),
        time_known=True, summary="BLS 官方发布日程缓存；实时日历恢复后会自动校正。",
    )
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "us_event_providers", lambda: [main.FunctionUsEventProvider("BLS", lambda: [event])])
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "providerStatuses": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})

    refresh = main.refresh_us_market_events()

    assert refresh["providerStatuses"] == [{
        "provider": "BLS", "status": "retained", "eventCount": 1, "retainedCount": 1,
        "message": "BLS 公开日历暂不可读，正在使用已校验的官方日程缓存。",
    }]


def test_bls_series_history_retries_a_transient_official_disconnect(monkeypatch):
    monkeypatch.setattr(main, "now_ms", lambda: main.us_event_timestamp("September 14, 2026") or 0)
    attempts = 0

    def request(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise OSError("remote disconnected")
        return {"Results": {"series": [{"seriesID": "CUUR0000SA0", "data": [{"year": "2026", "period": "M08", "periodName": "August", "value": "334.980"}]}]}}

    monkeypatch.setattr(main, "http_json_request", request)
    monkeypatch.setattr(main.time, "sleep", lambda _seconds: None)

    history = main.load_bls_series_history()
    assert attempts == 2
    assert history["Consumer Price Index"][0]["actual"] == "334.980"


def test_bls_series_loader_uses_only_explicit_current_and_prior_rows(monkeypatch):
    monkeypatch.setattr(main, "now_ms", lambda: main.us_event_timestamp("September 13, 2026") or 0)
    monkeypatch.setattr(main, "http_json_request", lambda *_args, **_kwargs: {
        "Results": {"series": [
            {"seriesID": "CUUR0000SA0", "data": [
                {"year": "2026", "periodName": "August", "value": "334.980"},
                {"year": "2026", "periodName": "July", "value": "333.918"},
            ]},
            {"seriesID": "WPUFD4", "data": [{"year": "2026", "periodName": "August", "value": "157.604"}]},
            {"seriesID": "CES0000000001", "data": [{"year": "2026", "periodName": "August", "value": "159075"}]},
            {"seriesID": "JTS000000000000000JOL", "data": [{"year": "2026", "periodName": "July", "value": "7271"}]},
        ]}
    })

    values = main.load_bls_latest_series()

    assert values["Consumer Price Index"] == {
        "actual": "334.980",
        "previous": "333.918",
        "period_label": "2026 August",
        "unit": "CPI-U（1982-84=100）",
    }
    assert values["Producer Price Index"]["previous"] == ""
    assert values["Employment Situation"]["actual"] == "159075"
    assert values["Job Openings and Labor Turnover"]["period_label"] == "2026 July"


def test_schedule_parser_keeps_a_release_title_in_its_own_official_row():
    fixture = """
      <table>
        <tr><td>Thursday, September 17, 2026 08:30 AM</td><td>Consumer Price Index</td></tr>
        <tr><td>Friday, September 18, 2026 08:30 AM</td><td>Employment Situation</td></tr>
      </table>
    """
    events = main.parse_us_event_schedule(
        fixture, "BLS", "https://www.bls.gov/schedule/2026/",
        [("Consumer Price Index", "inflation"), ("Employment Situation", "employment")],
    )
    assert [(event["title"], event["scheduled_at"]) for event in events] == [
        ("Consumer Price Index", main.us_event_timestamp("September 17, 2026", "08:30 AM")),
        ("Employment Situation", main.us_event_timestamp("September 18, 2026", "08:30 AM")),
    ]


def test_schedule_parser_does_not_borrow_a_later_entry_title():
    fixture = """
      Thursday, September 17, 2026 08:30 AM General calendar note.
      Friday, September 18, 2026 08:30 AM Consumer Price Index
    """
    events = main.parse_us_event_schedule(
        fixture, "BLS", "https://www.bls.gov/schedule/2026/", [("Consumer Price Index", "inflation")],
    )
    assert len(events) == 1
    assert events[0]["scheduled_at"] == main.us_event_timestamp("September 18, 2026", "08:30 AM")


def test_schedule_parser_keeps_each_title_with_its_own_date_in_flattened_calendar_text():
    fixture = """
      Tuesday, September 8, 2026 08:30 AM Consumer Price Index
      Wednesday, September 9, 2026 10:00 AM Producer Price Index
      Thursday, September 10, 2026 08:30 AM Employment Situation
    """
    events = main.parse_us_event_schedule(
        fixture, "BLS", "https://www.bls.gov/schedule/2026/",
        [("Consumer Price Index", "inflation"), ("Producer Price Index", "inflation"), ("Employment Situation", "employment")],
    )

    assert [(event["title"], event["scheduled_at"]) for event in events] == [
        ("Consumer Price Index", main.us_event_timestamp("September 8, 2026", "08:30 AM")),
        ("Producer Price Index", main.us_event_timestamp("September 9, 2026", "10:00 AM")),
        ("Employment Situation", main.us_event_timestamp("September 10, 2026", "08:30 AM")),
    ]


def test_schedule_parser_keeps_calendar_week_cells_independent():
    fixture = """
      <table><tr>
        <td>Friday, October 2, 2026 08:30 AM Employment Situation</td>
        <td>Wednesday, October 14, 2026 08:30 AM Consumer Price Index</td>
        <td>Thursday, October 15, 2026 08:30 AM Producer Price Index</td>
      </tr></table>
    """
    events = main.parse_us_event_schedule(
        fixture, "BLS", "https://www.bls.gov/schedule/2026/",
        [("Consumer Price Index", "inflation"), ("Producer Price Index", "inflation"), ("Employment Situation", "employment")],
    )

    assert [(event["title"], event["scheduled_at"]) for event in events] == [
        ("Employment Situation", main.us_event_timestamp("October 2, 2026", "08:30 AM")),
        ("Consumer Price Index", main.us_event_timestamp("October 14, 2026", "08:30 AM")),
        ("Producer Price Index", main.us_event_timestamp("October 15, 2026", "08:30 AM")),
    ]


def test_bls_refresh_removes_unmatched_future_schedule_rows(monkeypatch, tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'reconcile.sqlite3'}")
    db.init()
    now = main.us_event_timestamp("October 1, 2026")
    valid_at = main.us_event_timestamp("October 15, 2026", "08:30 AM")
    stale_at = main.us_event_timestamp("October 14, 2026", "08:30 AM")
    assert now and valid_at and stale_at
    stale = main.us_event_candidate("BLS", "producer-price-index-2026-10-14", "Producer Price Index", "inflation", "https://example.test/bls", stale_at, time_known=True)
    published = main.us_event_candidate("BLS", "consumer-price-index-2026-09-11", "Consumer Price Index", "inflation", "https://example.test/bls", main.us_event_timestamp("September 11, 2026", "08:30 AM"), time_known=True, state="released", actual="334.980")
    valid = main.us_event_candidate("BLS", "producer-price-index-2026-10-15", "Producer Price Index", "inflation", "https://example.test/bls", valid_at, time_known=True)
    db.upsert_market_event(stale)
    db.upsert_market_event(published)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "now_ms", lambda: now)
    monkeypatch.setattr(main, "us_event_providers", lambda: [main.FunctionUsEventProvider("BLS", lambda: [valid])])
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "providerStatuses": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})

    main.refresh_us_market_events()

    rows = db.list_market_events(now, valid_at + 1, [], [])
    assert [row["provider_event_key"] for row in rows] == ["producer-price-index-2026-10-15"]
    assert db.get_market_event(published["id"])["actual"] == "334.980"


def test_bls_refresh_removes_malformed_historical_schedule_rows_after_source_success(monkeypatch, tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'historical-reconcile.sqlite3'}")
    db.init()
    now = main.us_event_timestamp("September 14, 2026")
    stale_at = main.us_event_timestamp("August 7, 2026", "08:30 AM")
    valid_at = main.us_event_timestamp("August 12, 2026", "08:30 AM")
    future_at = main.us_event_timestamp("October 14, 2026", "08:30 AM")
    assert now and stale_at and valid_at and future_at
    stale = main.us_event_candidate("BLS", "consumer-price-index-2026-08-07", "Consumer Price Index", "inflation", "https://example.test/bls", stale_at, time_known=True)
    source_url = "https://www.bls.gov/schedule/2026/"
    valid = main.us_event_candidate("BLS", "consumer-price-index-2026-08-12", "Consumer Price Index", "inflation", source_url, valid_at, time_known=True)
    future = main.us_event_candidate("BLS", "consumer-price-index-2026-10-14", "Consumer Price Index", "inflation", source_url, future_at, time_known=True)
    released = main.us_event_candidate("BLS", "consumer-price-index-2026-07-14", "Consumer Price Index", "inflation", "https://example.test/bls", main.us_event_timestamp("July 14, 2026", "08:30 AM"), time_known=True, state="released", actual="333.918")
    db.upsert_market_event(stale)
    db.upsert_market_event(released)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "now_ms", lambda: now)
    monkeypatch.setattr(main, "us_event_providers", lambda: [main.FunctionUsEventProvider("BLS", lambda: [valid, future])])
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "providerStatuses": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})

    main.refresh_us_market_events()

    rows = db.list_market_events(stale_at, future_at + 1, [], [])
    assert [row["provider_event_key"] for row in rows] == ["consumer-price-index-2026-08-12", "consumer-price-index-2026-10-14"]
    assert db.get_market_event(released["id"])["actual"] == "333.918"


def test_treasury_fixture_requires_all_three_official_dates_before_enabling_auction():
    fixture = """
        <PendingAuctions>
          <Auction><SecurityType>Bill</SecurityType><SecurityTerm>42-Day</SecurityTerm>
            <AnnouncementDate>02/12/2026</AnnouncementDate><AuctionDate>02/17/2026</AuctionDate><IssueDate>02/19/2026</IssueDate>
          </Auction>
          <Auction><SecurityType>Note</SecurityType><SecurityTerm>2-Year</SecurityTerm>
            <AnnouncementDate>02/12/2026</AnnouncementDate><AuctionDate>02/17/2026</AuctionDate>
          </Auction>
        </PendingAuctions>
    """
    events = main.parse_treasury_auction_schedule(fixture, "https://www.treasurydirect.gov/example.xml")
    assert len(events) == 1
    assert events[0]["title"] == "美国国债拍卖：42-Day Bill"
    assert events[0]["category"] == "treasury"
    assert events[0]["period_label"] == "公告 02/12/2026；结算/发行 02/19/2026"
    assert events[0]["forecast"] is None
    assert '"timeKnown": false' in events[0]["source_summary"]


def test_treasury_loader_uses_the_current_official_xml_address(monkeypatch):
    requested_urls: list[str] = []
    monkeypatch.setattr(main, "http_text_request", lambda url: requested_urls.append(url) or "<PendingAuctions />")

    assert main.load_treasury_timeline_events() == []
    assert requested_urls == ["https://www.treasurydirect.gov/xml/PendingAuctions.xml"]


def test_official_text_request_retries_interrupted_reads(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return b"official calendar"

    attempts = 0

    def interrupted_once(_request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise main.IncompleteRead(b"partial", 1)
        return Response()

    monkeypatch.setattr(main, "urlopen", interrupted_once)
    monkeypatch.setattr(main.time, "sleep", lambda _seconds: None)

    assert main.http_text_request("https://example.test/calendar", retries=2) == "official calendar"
    assert attempts == 2


def test_refresh_uses_shorter_cache_when_a_scheduled_event_is_near(monkeypatch, tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'near.sqlite3'}")
    db.init()
    now = main.us_event_timestamp("September 17, 2026", "08:00 AM")
    assert now is not None
    event = main.us_event_candidate("BLS", "near", "Consumer Price Index", "inflation", "https://example.test/bls", now + 30 * 60 * 1000, time_known=True)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "now_ms", lambda: now)
    monkeypatch.setattr(main, "us_event_providers", lambda: [main.FunctionUsEventProvider("BLS", lambda: [event])])
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})
    assert main.refresh_us_market_events()["ttlSeconds"] == main.US_EVENT_NEAR_CACHE_SECONDS


def test_refresh_labels_retained_and_missing_provider_data_without_raw_errors(monkeypatch, tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'source-status.sqlite3'}")
    db.init()
    retained = main.us_event_candidate(
        "Federal Reserve", "fomc-retained", "FOMC 会议与利率决议", "monetary",
        "https://example.test/fed", main.us_event_timestamp("September 17, 2026"), time_known=False,
    )
    db.upsert_market_event(retained)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "us_event_providers", lambda: [
        main.FunctionUsEventProvider("Federal Reserve", lambda: (_ for _ in ()).throw(RuntimeError("internal token should not reach users"))),
        main.FunctionUsEventProvider("BLS", lambda: (_ for _ in ()).throw(main.OfficialSourceError("官方站点拒绝当前服务请求", "HTTP 403"))),
    ])
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "providerStatuses": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})

    refresh = main.refresh_us_market_events()

    statuses = {item["provider"]: item for item in refresh["providerStatuses"]}
    assert statuses["Federal Reserve"]["status"] == "retained"
    assert statuses["Federal Reserve"]["retainedCount"] == 1
    assert statuses["BLS"]["status"] == "unavailable"
    assert statuses["BLS"]["message"] == "官方站点拒绝当前服务请求"
    assert all("internal token" not in warning and "HTTP 403" not in warning for warning in refresh["warnings"])


def test_us_events_api_browses_filters_orders_and_reports_partial_provider_warning(monkeypatch, tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'api.sqlite3'}")
    db.init()
    first = main.us_event_candidate("BLS", "cpi", "Consumer Price Index", "inflation", "https://example.test/cpi", main.us_event_timestamp("September 17, 2026", "08:30 AM"), time_known=True)
    second = main.us_event_candidate("BLS", "jobs", "Employment Situation", "employment", "https://example.test/jobs", main.us_event_timestamp("September 17, 2026", "10:00 AM"), time_known=True)
    db.upsert_market_event(second)
    db.upsert_market_event(first)
    monkeypatch.setattr(main, "database", db)
    monkeypatch.setattr(main, "us_event_providers", lambda: [main.FunctionUsEventProvider("Federal Reserve", lambda: (_ for _ in ()).throw(RuntimeError("offline")))])
    monkeypatch.setattr(main, "us_event_refresh_cache", {"ts": 0, "warnings": [], "providers": [], "ttlSeconds": main.US_EVENT_CACHE_SECONDS})
    payload = main.market_us_events("2026-09-17", "2026-09-17")
    assert [item["title"] for item in payload["data"]] == ["Consumer Price Index", "Employment Situation"]
    assert payload["refreshing"] is True
    assert main.market_us_events("2026-09-17", "2026-09-17", "inflation")["data"][0]["title"] == "Consumer Price Index"
    with pytest.raises(HTTPException) as excessive:
        main.market_us_events("2026-01-01", "2026-03-01")
    assert excessive.value.status_code == 422
    with pytest.raises(HTTPException) as unknown:
        main.market_us_event_detail("not-a-real-event")
    assert unknown.value.status_code == 404

    detail = main.market_us_event_detail(first["id"])
    assert detail["forecast"] is None
