from __future__ import annotations

import base64
import hashlib
import hmac
import http.client
import json
import socket
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import Settings


class OkxError(RuntimeError):
    def __init__(self, message: str, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.payload = payload


def okx_error_message(payload: dict[str, Any]) -> str:
    code = str(payload.get("code") or "").strip()
    message = str(payload.get("msg") or "").strip()
    row_messages: list[str] = []
    rows = payload.get("data")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_code = str(row.get("sCode") or row.get("code") or "").strip()
            row_message = str(row.get("sMsg") or row.get("msg") or "").strip()
            sub_code = str(row.get("subCode") or "").strip()
            if not row_code and not row_message:
                continue
            code_label = row_code
            if sub_code:
                code_label = f"{code_label}/{sub_code}" if code_label else sub_code
            row_messages.append(f"{code_label}: {row_message}" if code_label else row_message)

    detail = "; ".join(row_messages) if row_messages else message
    if code and detail:
        return f"OKX API error {code}: {detail}"
    if code:
        return f"OKX API error {code}"
    return detail or "OKX API error"


def pos_side_error(exc: OkxError) -> bool:
    message = str(exc).lower()
    if "posside" not in message:
        return False
    payload = exc.payload or {}
    codes = [str(payload.get("code") or "")]
    rows = payload.get("data")
    if isinstance(rows, list):
        codes.extend(str(row.get("sCode") or "") for row in rows if isinstance(row, dict))
    return "51000" in codes or "51000" in message


def net_mode_retry_payload(request_payload: dict[str, Any], exc: OkxError) -> dict[str, Any] | None:
    pos_side = str(request_payload.get("posSide") or "").lower()
    if pos_side not in {"long", "short"} or not pos_side_error(exc):
        return None
    retry_payload = dict(request_payload)
    retry_payload.pop("posSide", None)
    return retry_payload


def parse_okx_candles(rows: list[list[str]]) -> list[dict[str, str]]:
    candles = []
    for row in reversed(rows):
        candles.append(
            {
                "ts": row[0],
                "open": row[1],
                "high": row[2],
                "low": row[3],
                "close": row[4],
                "volume": row[5],
                "volumeCcy": row[6] if len(row) > 6 else "",
                "volumeQuote": row[7] if len(row) > 7 else "",
                "confirm": row[8] if len(row) > 8 else "",
            }
        )
    return candles


class OkxClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def get_instruments(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/api/v5/public/instruments",
            query={"instType": "SWAP"},
            auth=False,
        )
        return response.get("data", [])

    def get_candles(self, inst_id: str, bar: str, limit: int = 300) -> list[dict[str, str]]:
        response = self._request(
            "GET",
            "/api/v5/market/candles",
            query={"instId": inst_id, "bar": bar, "limit": str(limit)},
            auth=False,
        )
        return parse_okx_candles(response.get("data", []))

    def get_history_candles(
        self, inst_id: str, bar: str, limit: int = 300, after: str | None = None
    ) -> list[dict[str, str]]:
        query = {"instId": inst_id, "bar": bar, "limit": str(limit)}
        if after:
            query["after"] = str(after)
        response = self._request(
            "GET",
            "/api/v5/market/history-candles",
            query=query,
            auth=False,
        )
        return parse_okx_candles(response.get("data", []))

    def get_tickers(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/api/v5/market/tickers",
            query={"instType": "SWAP"},
            auth=False,
        )
        return response.get("data", [])

    def get_platform_24_volume(self) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/api/v5/market/platform-24-volume",
            auth=False,
            include_simulated_header=False,
        )
        rows = response.get("data", [])
        return rows[0] if rows and isinstance(rows[0], dict) else None

    def get_ticker(self, inst_id: str) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/api/v5/market/ticker",
            query={"instId": inst_id},
            auth=False,
        )
        rows = response.get("data", [])
        return rows[0] if rows and isinstance(rows[0], dict) else None

    def get_order_book(self, inst_id: str, depth: int = 10) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/api/v5/market/books",
            query={"instId": inst_id, "sz": str(min(max(depth, 1), 10))},
            auth=False,
        )
        rows = response.get("data", [])
        return rows[0] if rows and isinstance(rows[0], dict) else None

    def get_announcement_types(self, language: str = "zh-CN") -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/api/v5/support/announcement-types",
            auth=False,
            extra_headers={"Accept-Language": language},
            include_simulated_header=False,
        )
        return response.get("data", [])

    def get_announcements(self, ann_type: str = "", page: int = 1, language: str = "zh-CN") -> dict[str, Any]:
        query = _clean_query({"annType": ann_type, "page": str(page)})
        response = self._request(
            "GET",
            "/api/v5/support/announcements",
            query=query,
            auth=False,
            extra_headers={"Accept-Language": language},
            include_simulated_header=False,
        )
        data = response.get("data", [])
        if isinstance(data, list) and data:
            first = data[0]
            return first if isinstance(first, dict) else {}
        return {}

    def get_contract_long_short_account_ratio(self, inst_id: str, period: str = "5m", limit: int = 100) -> list[list[str]]:
        response = self._request(
            "GET",
            "/api/v5/rubik/stat/contracts/long-short-account-ratio-contract",
            query={"instId": inst_id, "period": period, "limit": str(limit)},
            auth=False,
        )
        return response.get("data", [])

    def get_contract_taker_volume(self, inst_id: str, period: str = "5m", limit: int = 100, unit: str = "2") -> list[list[str]]:
        response = self._request(
            "GET",
            "/api/v5/rubik/stat/taker-volume-contract",
            query={"instId": inst_id, "period": period, "limit": str(limit), "unit": unit},
            auth=False,
        )
        return response.get("data", [])

    def get_contract_open_interest_history(self, inst_id: str, period: str = "5m", limit: int = 100) -> list[list[str]]:
        response = self._request(
            "GET",
            "/api/v5/rubik/stat/contracts/open-interest-history",
            query={"instId": inst_id, "period": period, "limit": str(limit)},
            auth=False,
        )
        return response.get("data", [])

    def get_funding_rate(self, inst_id: str, timeout_seconds: float = 4.0) -> dict[str, Any] | None:
        try:
            response = self._public_get("/api/v5/public/funding-rate", {"instId": inst_id}, timeout_seconds)
        except OkxError:
            return None
        rows = response.get("data", [])
        return rows[0] if rows and isinstance(rows[0], dict) else None

    def get_open_interest_bulk(self, inst_type: str = "SWAP", timeout_seconds: float = 6.0) -> dict[str, str]:
        """Fetch open interest for every contract of a type in one call.

        Returns a mapping of instId -> open interest in USD (oiUsd). A single
        bulk call replaces per-contract requests so sentiment enrichment does not
        fan out into dozens of slow upstream requests."""
        try:
            response = self._public_get("/api/v5/public/open-interest", {"instType": inst_type}, timeout_seconds)
        except OkxError:
            return {}
        out: dict[str, str] = {}
        for row in response.get("data") or []:
            if not isinstance(row, dict) or not row.get("instId"):
                continue
            oi_usd = row.get("oiUsd")
            if oi_usd is None:
                oi_usd = row.get("oi")
            if oi_usd is not None:
                out[str(row["instId"])] = str(oi_usd)
        return out

    def _public_get(self, path: str, query: dict[str, str] | None = None, timeout_seconds: float = 4.0) -> dict[str, Any]:
        """Single-shot public GET with a short timeout and no retry.

        Used by best-effort enrichment where a slow or flaky upstream must never
        block the request path behind a proxy timeout. Any failure raises OkxError."""
        query_string = f"?{urlencode(query)}" if query else ""
        url = f"{self.settings.base_url}{path}{query_string}"
        request = Request(url, headers={"User-Agent": "okx-dashboard/0.1"}, method="GET")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except (HTTPError, URLError, http.client.IncompleteRead, TimeoutError, socket.timeout, OSError) as exc:
            raise OkxError(f"OKX public request failed: {exc}") from exc
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise OkxError("OKX public response was not valid JSON") from exc
        if parsed.get("code") not in {None, "0"}:
            raise OkxError(okx_error_message(parsed), parsed)
        return parsed

    def get_balance(self) -> dict[str, Any]:
        return self._request("GET", "/api/v5/account/balance", auth=True)

    def get_positions(self) -> dict[str, Any]:
        return self._request("GET", "/api/v5/account/positions", query={"instType": "SWAP"}, auth=True)

    def get_leverage_info(self, inst_id: str, margin_mode: str) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v5/account/leverage-info",
            query={"instId": inst_id, "mgnMode": margin_mode},
            auth=True,
        )

    def set_leverage(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v5/account/set-leverage", body=payload, auth=True)

    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v5/trade/order", body=payload, auth=True)

    def close_position(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v5/trade/close-position", body=payload, auth=True)

    def cancel_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v5/trade/cancel-order", body=payload, auth=True)

    def get_pending_orders(self, inst_id: str | None = None) -> dict[str, Any]:
        query = {"instType": "SWAP"}
        if inst_id:
            query["instId"] = inst_id
        return self._request("GET", "/api/v5/trade/orders-pending", query=query, auth=True)

    # ---- 交易所侧止盈止损条件单（P2-2，字段语义需模拟盘实测确认）----

    def place_algo_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """提交算法单（止盈止损 OCO / 单腿条件单）。"""
        return self._request("POST", "/api/v5/trade/order-algo", body=payload, auth=True)

    def cancel_algo_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        """撤销算法单。payload 需含 algoId 或 algoClOrdId + instId。"""
        return self._request("POST", "/api/v5/trade/cancel-algo-order", body=payload, auth=True)

    def get_algo_orders(self, inst_id: str | None = None) -> dict[str, Any]:
        """查询当前未触发的算法单。"""
        query = _clean_query({"instType": "SWAP", "instId": inst_id})
        return self._request("GET", "/api/v5/trade/algo-current-orders", query=query, auth=True)

    def get_order(self, ord_id: str, inst_id: str) -> dict[str, Any] | None:
        """按订单号查询普通订单详情（用于取成交均价 avgPx）。"""
        query = _clean_query({"ordId": ord_id, "instId": inst_id})
        response = self._request("GET", "/api/v5/trade/order", query=query, auth=True)
        rows = response.get("data", [])
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return rows[0]
        return None

    def get_trade_bills(
        self, bill_type: str = "2", limit: int = 100, after: str | None = None
    ) -> list[dict[str, Any]]:
        """读取交易账单流水（type=2 为成交）。

        每笔成交流水带 ``clOrdId`` / ``pnl``（该笔已实现毛盈亏）/ ``fee``（手续费，
        负数扣减）。按 clOrdId 聚合即可得到某个订单的真实、含手续费结算盈亏。
        这是 OKX 已结算口径，优于此前的「平仓前持仓浮动盈亏」估算。

        ``after`` 为 OKX 的账单游标：返回 billId 早于该值的记录，用于翻页。
        """
        query = _clean_query(
            {"type": str(bill_type), "limit": str(max(1, min(int(limit), 100))), "after": after}
        )
        response = self._request("GET", "/api/v5/account/bills", query=query, auth=True)
        rows = response.get("data", [])
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []

    def get_all_trade_bills(
        self, bill_type: str = "2", limit: int = 100, max_pages: int = 10
    ) -> list[dict[str, Any]]:
        """按 billId 游标翻页聚合成交账单，覆盖百笔以上的历史成交。

        OKX ``/api/v5/account/bills`` 单页最多 100 条，按时间倒序返回，``after``
        游标返回更早记录。循环至返回不足一页、游标不再推进或达到 max_pages 上限，
        避免异常接口导致无限循环。按 billId 去重，防止游标边界重复。
        """
        collected: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        after: str | None = None
        for _ in range(max(1, max_pages)):
            page = self.get_trade_bills(bill_type=bill_type, limit=limit, after=after)
            if not page:
                break
            page_added = 0
            oldest_id: str | None = None
            for row in page:
                bill_id = str(row.get("billId") or "").strip()
                if bill_id:
                    oldest_id = bill_id  # 页面按时间倒序，最后一条即最早
                    if bill_id in seen_ids:
                        continue
                    seen_ids.add(bill_id)
                collected.append(row)
                page_added += 1
            # 无新增（整页重复）或游标无法推进，停止翻页
            if page_added == 0 or not oldest_id or oldest_id == after:
                break
            after = oldest_id
            if len(page) < limit:
                break
        return collected

    def get_staking_defi_offers(
        self,
        product_id: str = "",
        protocol_type: str = "",
        ccy: str = "",
    ) -> list[dict[str, Any]]:
        query = _clean_query({"productId": product_id, "protocolType": protocol_type, "ccy": ccy})
        response = self._request("GET", "/api/v5/finance/staking-defi/offers", query=query, auth=True)
        return response.get("data", [])

    def get_staking_defi_active_orders(
        self,
        product_id: str = "",
        protocol_type: str = "",
        ccy: str = "",
        state: str = "",
    ) -> list[dict[str, Any]]:
        query = _clean_query({"productId": product_id, "protocolType": protocol_type, "ccy": ccy, "state": state})
        response = self._request("GET", "/api/v5/finance/staking-defi/orders-active", query=query, auth=True)
        return response.get("data", [])

    def get_staking_defi_order_history(
        self,
        product_id: str = "",
        protocol_type: str = "",
        ccy: str = "",
        after: str = "",
        before: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = _clean_query(
            {
                "productId": product_id,
                "protocolType": protocol_type,
                "ccy": ccy,
                "after": after,
                "before": before,
                "limit": str(limit),
            }
        )
        response = self._request("GET", "/api/v5/finance/staking-defi/orders-history", query=query, auth=True)
        return response.get("data", [])

    def get_eth_staking_product_info(self) -> dict[str, Any]:
        response = self._request("GET", "/api/v5/finance/staking-defi/eth/product-info", auth=True)
        data = response.get("data", [])
        if isinstance(data, list):
            return data[0] if data else {}
        return data if isinstance(data, dict) else {}

    def get_eth_staking_balance(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/v5/finance/staking-defi/eth/balance", auth=True)
        return response.get("data", [])

    def get_eth_staking_history(
        self,
        request_type: str = "",
        status: str = "",
        after: str = "",
        before: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = _clean_query(
            {"type": request_type, "status": status, "after": after, "before": before, "limit": str(limit)}
        )
        response = self._request("GET", "/api/v5/finance/staking-defi/eth/purchase-redeem-history", query=query, auth=True)
        return response.get("data", [])

    def get_eth_staking_apy_history(self, days: int) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/v5/finance/staking-defi/eth/apy-history", query={"days": str(days)}, auth=False)
        return response.get("data", [])

    def get_sol_staking_product_info(self) -> dict[str, Any]:
        response = self._request("GET", "/api/v5/finance/staking-defi/sol/product-info", auth=True)
        data = response.get("data", {})
        if isinstance(data, list):
            return data[0] if data else {}
        return data if isinstance(data, dict) else {}

    def get_sol_staking_balance(self) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/v5/finance/staking-defi/sol/balance", auth=True)
        return response.get("data", [])

    def get_sol_staking_history(
        self,
        request_type: str = "",
        status: str = "",
        after: str = "",
        before: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = _clean_query(
            {"type": request_type, "status": status, "after": after, "before": before, "limit": str(limit)}
        )
        response = self._request("GET", "/api/v5/finance/staking-defi/sol/purchase-redeem-history", query=query, auth=True)
        return response.get("data", [])

    def get_sol_staking_apy_history(self, days: int) -> list[dict[str, Any]]:
        response = self._request("GET", "/api/v5/finance/staking-defi/sol/apy-history", query={"days": str(days)}, auth=False)
        return response.get("data", [])

    def _request(
        self,
        method: str,
        path: str,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        auth: bool = False,
        extra_headers: dict[str, str] | None = None,
        include_simulated_header: bool = True,
    ) -> dict[str, Any]:
        method = method.upper()
        query_string = f"?{urlencode(query)}" if query else ""
        request_path = f"{path}{query_string}"
        url = f"{self.settings.base_url}{request_path}"
        body_text = json.dumps(body, separators=(",", ":")) if body else ""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "okx-dashboard/0.1",
        }
        if extra_headers:
            headers.update(extra_headers)

        if include_simulated_header and self.settings.simulated_trading:
            headers["x-simulated-trading"] = "1"

        if auth:
            self.settings.require_credentials()
            timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            headers.update(self._auth_headers(timestamp, method, request_path, body_text))

        raw_body = self._send_with_retries(url, method, headers, body_text)

        parsed = json.loads(raw_body)
        if parsed.get("code") not in {None, "0"}:
            raise OkxError(okx_error_message(parsed), parsed)
        return parsed

    def _send_with_retries(self, url: str, method: str, headers: dict[str, str], body_text: str) -> str:
        last_error: Exception | None = None
        for attempt in range(3):
            request = Request(
                url,
                data=body_text.encode("utf-8") if body_text else None,
                headers=headers,
                method=method,
            )
            try:
                with urlopen(request, timeout=self.settings.timeout_seconds) as response:
                    return response.read().decode("utf-8")
            except HTTPError as exc:
                raw_body = exc.read().decode("utf-8", errors="replace")
                try:
                    parsed = json.loads(raw_body)
                except json.JSONDecodeError:
                    raise OkxError(f"OKX HTTP {exc.code}: {raw_body}") from exc
                raise OkxError(f"OKX HTTP {exc.code}: {okx_error_message(parsed)}", parsed) from exc
            except http.client.IncompleteRead as exc:
                partial = exc.partial or b""
                if partial:
                    raw_body = partial.decode("utf-8", errors="replace")
                    try:
                        json.loads(raw_body)
                        return raw_body
                    except json.JSONDecodeError:
                        pass
                last_error = exc
                if attempt < 2:
                    time.sleep([0.5, 1.2][attempt])
                    continue
            except (http.client.RemoteDisconnected, TimeoutError, socket.timeout) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep([0.5, 1.2][attempt])
                    continue
            except URLError as exc:
                raise OkxError(f"OKX request failed: {exc}") from exc
        raise OkxError(f"OKX response was incomplete after retries: {last_error}")

    def _auth_headers(self, timestamp: str, method: str, request_path: str, body_text: str) -> dict[str, str]:
        message = f"{timestamp}{method}{request_path}{body_text}"
        signature = base64.b64encode(
            hmac.new(
                self.settings.api_secret.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha256,
            ).digest()
        ).decode("utf-8")
        return {
            "OK-ACCESS-KEY": self.settings.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.settings.passphrase,
        }


def now_ms() -> int:
    return int(time.time() * 1000)


def _clean_query(query: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in query.items() if str(value or "").strip()}
