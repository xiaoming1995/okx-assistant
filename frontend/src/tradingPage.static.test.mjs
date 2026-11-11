import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("trade page keeps local order history without the pending orders panel", () => {
  assert.match(source, /function TradingPage/);
  assert.doesNotMatch(source, /title="未成交订单"/);
  assert.doesNotMatch(source, /\bpendingOrders\b/);
  assert.match(source, /title="本地订单记录"/);
  assert.match(source, /new URLSearchParams\(\{[\s\S]*?limit: String\(orderPageSize\),[\s\S]*?offset: String/);
  assert.match(source, /fetch\(`\$\{API_BASE\}\/api\/trading\/orders\?\$\{params\.toString\(\)\}`\)/);
  assert.match(source, /payload\.paging/);
});

test("trade page grid only reserves rows for the ticket and local history", () => {
  assert.match(styles, /\.tradeGrid \{[\s\S]*?grid-template-columns: minmax\(310px, 360px\) minmax\(0, 1fr\);[\s\S]*?grid-template-rows: minmax\(0, 1fr\);/);
  assert.match(styles, /@media \(max-width: 1200px\) \{[\s\S]*?\.tradeGrid \{[\s\S]*?grid-template-columns: 1fr;[\s\S]*?grid-template-rows: auto minmax\(260px, auto\);/);
});

test("trade ticket makes leverage contract context explicit and keeps advanced order types collapsed", () => {
  assert.match(source, /const leverageContext = `\$\{instId\.toUpperCase\(\)\} · \$\{leverageScope\}`/);
  assert.match(source, /aria-label="当前合约杠杆"/);
  assert.match(source, /账户当前 \{leverageLoading \? "读取中" : leverageSummary\}/);
  assert.match(source, /primaryOrderTypeOptions/);
  assert.match(source, /advancedOrderTypeOptions/);
  assert.match(source, /高级类型/);
});

test("trade order history exposes server-backed search, filters, and pagination", () => {
  assert.match(source, /const \[orderSearch, setOrderSearch\]/);
  assert.match(source, /params\.set\("q", orderSearch\.trim\(\)\)/);
  assert.match(source, /params\.set\("action", orderActionFilter\)/);
  assert.match(source, /params\.set\("state", orderStateFilter\)/);
  assert.match(source, /搜索合约 \/ 订单号 \/ 错误信息/);
  assert.match(source, /当前合约/);
  assert.match(source, /全部记录/);
  assert.match(source, /setOrderPageIndex\(\(value\) => Math\.min\(orderPageCount, value \+ 1\)\)/);
  assert.match(styles, /\.tradeOrderControls \{[\s\S]*?grid-template-columns: minmax\(260px, 1fr\) auto minmax\(112px, auto\) minmax\(112px, auto\);/);
  assert.match(styles, /@media \(max-width: 1200px\) \{[\s\S]*?\.tradeOrderControls,[\s\S]*?grid-template-columns: 1fr;/);
});
