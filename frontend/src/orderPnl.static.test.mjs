import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
const backend = readFileSync(new URL("../../backend/app/order_pnl.py", import.meta.url), "utf8");
const db = readFileSync(new URL("../../backend/app/db.py", import.meta.url), "utf8");

test("local order records expose a realized PnL column", () => {
  assert.match(source, /<th>盈亏<\/th>/);
  assert.match(source, /<th>合约 \/ 订单号<\/th>/);
  assert.match(source, /className="orderPnlCell"/);
  assert.match(source, /formatOrderPnl\(event\.pnl_usd\)/);
  assert.match(source, /pnlValueClass\(pnlValue\)/);
  assert.match(source, /formatOrderPnlPct\(event\.pnl_pct\)/);
});

test("order rows explain the PnL basis and show order/strategy provenance", () => {
  assert.match(source, /orderPnlBasisLabel\(event\.pnl_basis\)/);
  assert.match(source, /ID \$\{orderRef\}/);
  assert.match(source, /策略 #\$\{event\.strategy_id\}/);
  assert.match(source, /信号 #\$\{event\.signal_id\}/);
  assert.match(source, /该笔平仓没有可结算的 OKX 账单/);
  assert.match(source, /开仓与撤单不产生已实现盈亏/);
});

test("order page summarizes priced closes with an explicit disclaimer", () => {
  assert.match(source, /setOrderPnlSummary\(payload\.pnlSummary \?\? null\)/);
  assert.match(source, /pnlSummary\?: \{[\s\S]*?pageRealizedTotal: string/);
  assert.match(source, /本页平仓盈亏合计/);
  assert.match(source, /\{orderPnlSummary\.pricedCloses\}\/\{orderPnlSummary\.closeCount\} 笔平仓可计价/);
  assert.match(source, /settledCloses \? ` · \$\{orderPnlSummary\.settledCloses\} 笔按 OKX 账单结算`/);
  assert.match(source, /结算值含手续费；未结算的单据取平仓前持仓浮动盈亏估算/);
  assert.match(source, /orderPnlSummary && orderPnlSummary\.closeCount > 0/);
});

test("settled orders are visually distinguished and break down gross and fee", () => {
  assert.match(source, /event\.pnl_settled \? " orderPnlSettled" : ""/);
  assert.match(source, /毛 \$\{formatOrderPnl\(event\.pnl_gross\)\} \/ 手续费 \$\{formatOrderPnl\(event\.pnl_fee\)\}/);
  assert.match(source, /event\.bill_count \? ` · \$\{event\.bill_count\} 笔成交` : ""/);
  assert.match(source, /if \(basis === "okx-bills-settled"\) return "OKX 已结算（含手续费）"/);
  assert.match(styles, /orderPnlSettled \{[\s\S]*?text-decoration: underline dotted/);
});

test("order PnL styling keeps the table readable", () => {
  assert.match(styles, /\.orderHistoryTable \{\s*min-width: 1050px;/);
  assert.match(styles, /\.orderPnlSummary \{[\s\S]*?flex-wrap: wrap/);
  assert.match(styles, /\.orderHistoryTable td\.orderPnlCell \.pnl-positive/);
  assert.match(styles, /\.orderHistoryTable td\.orderPnlCell \.pnl-negative/);
  assert.match(styles, /\.orderHistoryTable td\.orderPnlCell \.pnl-neutral/);
  assert.match(styles, /\.orderHistoryTable td small \{[\s\S]*?display: block/);
});

test("backend derives estimated PnL from pre-close position snapshots", () => {
  assert.match(backend, /def position_pnl\(/);
  assert.match(backend, /def signal_pnl_links\(/);
  assert.match(backend, /def nearest_snapshot_pnl\(/);
  assert.match(backend, /def attach_order_pnl\(/);
  assert.match(backend, /PNL_BASIS_SNAPSHOT/);
  assert.match(backend, /SNAPSHOT_WINDOW_MS = 120_000/);
});

test("backend settles realized PnL from OKX trade bills including fees", () => {
  assert.match(backend, /PNL_BASIS_BILLS = "okx-bills-settled"/);
  assert.match(backend, /def index_bills_by_order\(/);
  assert.match(backend, /def settle_order_pnl\(/);
  assert.match(backend, /def apply_settled_pnl\(/);
  assert.match(backend, /gross \+ fee/);
  assert.match(backend, /pnl_gross/);
  assert.match(backend, /pnl_fee/);
});

test("OKX client and order list wire up settled bills with caching and graceful fallback", () => {
  const okx = readFileSync(new URL("../../backend/app/okx.py", import.meta.url), "utf8");
  const main = readFileSync(new URL("../../backend/app/main.py", import.meta.url), "utf8");
  assert.match(okx, /def get_trade_bills\(/);
  assert.match(okx, /"\/api\/v5\/account\/bills"/);
  assert.match(main, /SETTLEMENT_CACHE_MS = 30_000/);
  assert.match(main, /def settlement_bills_index\(/);
  assert.match(main, /order_pnl\.apply_settled_pnl\(local_events, bills_index\)/);
  assert.match(main, /def invalidate_settlement_cache\(/);
});

test("both database backends persist PnL columns with a smooth migration", () => {
  assert.equal((db.match(/pnl_usd TEXT/g) || []).length >= 2, true);
  assert.match(db, /_ensure_column\("sim_order_events", "pnl_basis", "TEXT"\)/);
  assert.match(db, /ALTER TABLE sim_order_events ADD COLUMN IF NOT EXISTS pnl_usd TEXT/);
  assert.match(db, /message, request_json, response_json, pnl_usd, pnl_pct, pnl_basis/);
  assert.match(db, /def position_snapshot_rows_between\(/);
});
