from decimal import Decimal

from backend.app import market_context


def ticker(inst_id: str, last: str, open24h: str, high: str = "", low: str = "") -> dict:
    return {"instId": inst_id, "last": last, "open24h": open24h, "high24h": high or last, "low24h": low or last}


def test_ticker_change_pct_and_range_position():
    assert market_context.ticker_change_pct(ticker("X", "110", "100")) == Decimal("10.00")
    assert market_context.ticker_change_pct(ticker("X", "90", "100")) == Decimal("-10.00")
    assert market_context.ticker_change_pct(ticker("X", "100", "0")) is None
    assert market_context.ticker_change_pct({"last": "", "open24h": "100"}) is None
    # 区间位置：98~102 中价 100 → 50%
    assert market_context.ticker_range_position_pct(ticker("X", "100", "100", "102", "98")) == Decimal("50.00")
    assert market_context.ticker_range_position_pct(ticker("X", "100", "100", "100", "100")) is None


def test_build_breadth_counts_rising_falling_and_advance_pct():
    tickers = [
        ticker("A-USDT-SWAP", "102", "100"),
        ticker("B-USDT-SWAP", "103", "100"),
        ticker("C-USDT-SWAP", "98", "100"),
        ticker("D-USDT-SWAP", "100", "100"),
    ]
    breadth = market_context.build_breadth(tickers)
    assert breadth["total"] == 4
    assert breadth["rising"] == 2
    assert breadth["falling"] == 1
    assert breadth["flat"] == 1
    assert breadth["advancePct"] == "50.00"


def test_build_sectors_aggregates_and_sorts_by_strength():
    members = {
        "SOL-USDT-SWAP": ticker("SOL-USDT-SWAP", "110", "100"),  # +10
        "ADA-USDT-SWAP": ticker("ADA-USDT-SWAP", "102", "100"),  # +2
        "DOGE-USDT-SWAP": ticker("DOGE-USDT-SWAP", "90", "100"),  # -10
        "PEPE-USDT-SWAP": ticker("PEPE-USDT-SWAP", "95", "100"),  # -5
    }
    sectors = market_context.build_sectors(members)
    names = [row["name"] for row in sectors]
    assert names[0] == "L1"  # L1 平均 +6 强于 Meme -7.5
    l1 = next(row for row in sectors if row["name"] == "L1")
    assert l1["members"] == 2
    assert l1["avgChange24hPct"] == "6.00"
    assert l1["risingPct"] == "100.00"
    assert l1["leader"] == "SOL"
    meme = next(row for row in sectors if row["name"] == "Meme")
    assert meme["avgChange24hPct"] == "-7.50"


def test_classify_bias_thresholds():
    breadth_weak = {"advancePct": "28.00"}
    breadth_strong = {"advancePct": "65.00"}
    breadth_mid = {"advancePct": "50.00"}
    assert market_context.classify_bias(breadth_weak, {"btc": {"change24hPct": "-1.00"}}) == "risk-off"
    assert market_context.classify_bias(breadth_mid, {"btc": {"change24hPct": "-2.50"}}) == "risk-off"
    assert market_context.classify_bias(breadth_strong, {"btc": {"change24hPct": "2.50"}}) == "risk-on"
    assert market_context.classify_bias(breadth_mid, {"btc": {"change24hPct": "0.50"}}) == "mixed"
    assert market_context.classify_bias({"advancePct": ""}, {}) == "mixed"


def test_build_market_context_handles_empty_and_sentiment():
    empty = market_context.build_market_context([], None, ["no data"])
    assert empty["breadth"]["total"] == 0
    assert empty["bias"] == "mixed"
    assert empty["warnings"] == ["no data"]

    tickers = [
        ticker("BTC-USDT-SWAP", "102", "100"),
        ticker("ETH-USDT-SWAP", "103", "100"),
        ticker("SOL-USDT-SWAP", "104", "100"),
    ]
    context = market_context.build_market_context(
        tickers,
        {"funding": {"sampled": 3, "positive": 1, "negative": 2, "neutral": 0, "avgFundingRatePct": "-0.0020"},
         "openInterest": {"sampled": 100, "totalOiUsd": "123456"}},
        [],
    )
    assert context["majors"]["btc"]["change24hPct"] == "2.00"
    assert context["majors"]["eth"]["change24hPct"] == "3.00"
    assert context["sentiment"]["funding"]["negative"] == 2
    assert context["sentiment"]["openInterest"]["totalOiUsd"] == "123456"
    brief = market_context.sector_brief(context)
    assert brief and brief[0]["name"]


def test_sector_brief_limits_rows():
    context = {"sectors": [{"name": "L1", "label": "公链 L1", "avgChange24hPct": "1", "risingPct": "100", "leader": "SOL", "leaderChange24hPct": "2"}] * 8}
    assert len(market_context.sector_brief(context, limit=3)) == 3
