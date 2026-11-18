import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
const backend = readFileSync(new URL("../../backend/app/main.py", import.meta.url), "utf8");
const db = readFileSync(new URL("../../backend/app/db.py", import.meta.url), "utf8");
const orderPnl = readFileSync(new URL("../../backend/app/order_pnl.py", import.meta.url), "utf8");

test("order records offer an origin switch between automation and manual", () => {
  assert.match(source, /aria-label="订单来源"/);
  assert.match(source, /setOrderOriginFilter\(""\)/);
  assert.match(source, /setOrderOriginFilter\("automation"\)/);
  assert.match(source, /setOrderOriginFilter\("manual"\)/);
  assert.match(source, /params\.set\("origin", orderOriginFilter\)/);
  assert.match(source, /setOrderOriginCounts\(\{/);
});

test("each order row states whether it came from automation or a human", () => {
  assert.match(source, /<th>来源<\/th>/);
  assert.match(source, /const isAutomation = event\.origin === "automation"/);
  assert.match(source, /className={`orderOriginTag \$\{isAutomation \? "automation" : "manual"\}`}/);
  assert.match(source, /\{isAutomation \? "自动化" : "手动"\}/);
  assert.match(styles, /\.orderOriginTag\.automation/);
  assert.match(styles, /\.orderOriginTag\.manual/);
});

test("backend separates order origin end to end", () => {
  assert.match(backend, /ORDER_ORIGIN_MANUAL = "manual"/);
  assert.match(backend, /ORDER_ORIGIN_AUTOMATION = "automation"/);
  // 自动化执行路径必须显式打标。
  assert.match(backend, /close_position_for_environment\([\s\S]{0,160}origin=ORDER_ORIGIN_AUTOMATION/);
  assert.match(backend, /place_order_for_environment\([\s\S]{0,160}origin=ORDER_ORIGIN_AUTOMATION/);
  // 手动上报的 webhook 更新沿用已落库来源，不能把自动化单翻成手动。
  assert.match(backend, /"origin": order_event_origin\(environment, cl_ord_id\)/);
  assert.match(backend, /def backfill_automation_order_origins\(/);
  assert.match(backend, /backfill_automation_order_origins\(\)\r?\n/);
});

test("close orders say which strategy position they closed", () => {
  assert.match(source, /close_strategy_id/);
  assert.match(source, /平 策略 #\$\{event\.close_strategy_id\} 仓/);
  assert.match(orderPnl, /def close_strategy_attribution\(/);
  assert.match(orderPnl, /def automation_open_signals\(/);
  assert.match(orderPnl, /ATTRIBUTION_WINDOW_MS = 24 \* 60 \* 60 \* 1000/);
  assert.match(backend, /order_pnl\.close_strategy_attribution\(local_events, signal_rows\)/);
});

test("order origin column migrates on both backends and supports filtering", () => {
  assert.match(db, /origin TEXT NOT NULL DEFAULT 'manual'/);
  assert.match(db, /_ensure_column\("sim_order_events", "origin"/);
  assert.match(db, /ADD COLUMN IF NOT EXISTS origin TEXT NOT NULL DEFAULT 'manual'/);
  assert.match(db, /def sim_order_event_origin_counts\(/);
  assert.match(db, /def mark_sim_order_event_origin\(/);
  assert.match(db, /AND \(%s = '' OR origin = %s\)/);
  assert.match(db, /AND \(\? = '' OR origin = \?\)/);
});
