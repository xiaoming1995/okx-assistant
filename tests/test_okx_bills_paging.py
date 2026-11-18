"""P2-1：结算账单翻页，覆盖百笔以上成交账户。"""

from backend.app.okx import OkxClient


class _PagingClient(OkxClient):
    """用脚本化页面替身 _request，验证翻页游标与去重。"""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def _request(self, method, path, query=None, body=None, auth=False, **kwargs):
        self.calls.append(dict(query or {}))
        after = (query or {}).get("after") or ""
        page = self.pages.get(after, [])
        return {"code": "0", "data": page}


def _bill(bill_id, cl_ord_id, pnl="1"):
    return {"billId": bill_id, "clOrdId": cl_ord_id, "pnl": pnl, "fee": "0"}


def test_get_trade_bills_passes_after_cursor():
    client = _PagingClient({"b0": [_bill("b1", "o1")]})
    rows = client.get_trade_bills(after="b0")
    assert rows and rows[0]["billId"] == "b1"
    assert client.calls[-1]["after"] == "b0"
    assert client.calls[-1]["type"] == "2"
    assert client.calls[-1]["limit"] == "100"


def test_get_all_trade_bills_pages_through_all_results():
    # 第一页 2 条，第二页 2 条，第三页 1 条（不足一页触发停止）
    pages = {
        "": [_bill("b3", "o3"), _bill("b2", "o2")],
        "b2": [_bill("b1", "o1"), _bill("b0", "o0")],
        "b0": [_bill("b-1", "o-1")],
    }
    client = _PagingClient(pages)
    rows = client.get_all_trade_bills(limit=2, max_pages=10)
    assert [r["billId"] for r in rows] == ["b3", "b2", "b1", "b0", "b-1"]
    # 至少翻了三次：after 依次为空、b2、b0
    afters = [c.get("after") or "" for c in client.calls]
    assert "" in afters and "b2" in afters and "b0" in afters


def test_get_all_trade_bills_deduplicates_boundary_rows():
    # 第二页首条 billId 与第一页末条重复（游标边界重叠），应去重
    pages = {
        "": [_bill("b2", "o2"), _bill("b1", "o1")],
        "b1": [_bill("b1", "o1"), _bill("b0", "o0")],
    }
    client = _PagingClient(pages)
    rows = client.get_all_trade_bills(limit=2, max_pages=10)
    assert [r["billId"] for r in rows] == ["b2", "b1", "b0"]


def test_get_all_trade_bills_stops_when_cursor_not_advancing():
    # 每页返回的 oldest_id 与请求的 after 相同（异常接口），应立即停止而非死循环
    pages = {"": [_bill("b1", "o1"), _bill("b0", "o0")], "b0": [_bill("b0", "o0")]}
    client = _PagingClient(pages)
    rows = client.get_all_trade_bills(limit=2, max_pages=10)
    assert len(rows) == 2  # 第二页全是重复，page_added=0 停止
    assert len(client.calls) == 2


def test_get_all_trade_bills_respects_max_pages():
    # 每页都满且游标持续推进，受 max_pages 限制停止。
    # 每页 2 条唯一记录，最老一条成为下一页 after，无重叠。
    pages = {}
    for i in range(20):
        after = "" if i == 0 else f"b{2 * i - 1}"
        pages[after] = [
            _bill(f"b{2 * i + 2}", f"o{2 * i + 2}"),
            _bill(f"b{2 * i + 1}", f"o{2 * i + 1}"),
        ]
    client = _PagingClient(pages)
    rows = client.get_all_trade_bills(limit=2, max_pages=3)
    assert len(client.calls) == 3
    assert len(rows) == 6
