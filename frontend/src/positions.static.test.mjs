import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
const positionsStart = source.indexOf("function PositionsPage()");
const accountStart = source.indexOf("function AccountPage()");
const positionsSource = source.slice(positionsStart, accountStart);

test("positions aggregate current open-position floating pnl independently of table filters", () => {
  assert.match(positionsSource, /const openPositions = React\.useMemo\(\(\) => positions\.filter\(positionIsOpen\)/);
  assert.match(positionsSource, /const totalUpl = openPositions\.reduce\(/);
  assert.match(positionsSource, /const pnlCounts = React\.useMemo\(\(\) => openPositions\.reduce/);
  assert.match(positionsSource, /<strong>未实现盈亏汇总<\/strong>/);
  assert.match(positionsSource, /label="浮动盈亏合计"/);
  assert.match(positionsSource, /label="盈利持仓"/);
  assert.match(positionsSource, /label="亏损持仓"/);
  assert.match(positionsSource, /label="持平持仓"/);
  assert.match(positionsSource, /label="保证金"/);
  assert.match(positionsSource, /label="名义 USD"/);
  assert.match(positionsSource, /refreshLabel/);
  assert.match(positionsSource, /const accountUnavailable = account\?\.source === "okx-unavailable"/);
  assert.match(positionsSource, /\{account\?\.warning \? <Notice tone="warning">\{account\.warning\}<\/Notice> : null\}/);
});

test("account and positions preserve complete snapshots on HTTP and network errors", () => {
  const accountSource = source.slice(accountStart);
  assert.match(source, /function accountFailureSnapshot\(current: AccountResponse \| null, label: string\)/);
  assert.match(source, /current\?\.configured && current\.summary && Array\.isArray\(current\.positions\)/);
  assert.match(source, /source: "okx-stale-cache"/);
  assert.match(source, /if \(source === "error"\) return "暂不可用"/);
  for (const pageSource of [positionsSource, accountSource]) {
    assert.match(pageSource, /if \(!response\.ok\) \{\s*setAccount\(\(current\) => accountFailureSnapshot\(current, /);
    assert.match(pageSource, /\} catch \{\s*setAccount\(\(current\) => accountFailureSnapshot\(current, /);
    assert.doesNotMatch(pageSource, /message: payload\.detail/);
  }
});

test("positions show signed semantic pnl values without using raw transport details", () => {
  assert.match(source, /function pnlValueClass\(/);
  assert.match(source, /function formatSignedValue\(/);
  assert.match(source, /function formatSignedPercentRatio\(/);
  assert.match(positionsSource, /className=\{pnlValueClass\(upl\)\}/);
  assert.match(positionsSource, /formatSignedValue\(upl\)/);
  assert.match(positionsSource, /className=\{pnlValueClass\(ratio\)\}/);
  assert.match(positionsSource, /formatSignedPercentRatio\(ratio\)/);
  assert.match(positionsSource, /account\?\.refresh\?\.label/);
  assert.doesNotMatch(positionsSource, /IncompleteRead/);
});

test("scoped pnl styles override generic table typography without recolouring other pages", () => {
  assert.match(styles, /\.positionPnlSummary \.miniMetric strong\.pnl-positive,\n\.positionDataTable td \.pnl-positive/);
  assert.match(styles, /\.positionPnlSummary \.miniMetric strong\.pnl-negative,\n\.positionDataTable td \.pnl-negative/);
  assert.match(styles, /\.positionPnlSummary \.miniMetric strong\.pnl-neutral,\n\.positionDataTable td \.pnl-neutral/);
  assert.match(styles, /\.signalLogInlineChip\.pnl-positive/);
  assert.match(styles, /\.signalLogInlineChip\.pnl-negative/);
});
