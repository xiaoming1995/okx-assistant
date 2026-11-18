import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");

test("shared realtime hook connects to the backend feed and keeps rest fallback callbacks", () => {
  assert.match(source, /function useRealtimeFeed/);
  assert.match(source, /new WebSocket\(`\$\{WS_BASE\}\/ws\/realtime`\)/);
  assert.match(source, /op: "subscribe"/);
  assert.match(source, /payload\.refreshRequired/);
  assert.match(source, /onSnapshotRequiredRef\.current\?\.\(payload\)/);
  assert.match(source, /实时通道暂不可用，已保留 REST 回退/);
});

test("market workbench owns shared ticker and chart-snapshot realtime data", () => {
  const workspaceStart = source.indexOf("function MarketContractWorkspace(");
  const chartStart = source.indexOf("function MarketPage(");
  const aiStart = source.indexOf("function MarketAiOutlookPage(");
  const statsStart = source.indexOf("function MarketStatsPage(");
  const tradeStart = source.indexOf("function TradingPage(");
  const workspaceSource = source.slice(workspaceStart, chartStart);
  const chartSource = source.slice(chartStart, aiStart);
  const aiSource = source.slice(aiStart, statsStart);
  const statsSource = source.slice(statsStart, tradeStart);

  assert.match(workspaceSource, /const tickerRealtime = useRealtimeFeed\(\{/);
  assert.match(workspaceSource, /topics: \["market\.ticker"\]/);
  assert.match(workspaceSource, /setTickerUpdatedAt\(payload\.ts \?\? Date\.now\(\)\);/);
  assert.match(workspaceSource, /setTickerSource\(payload\.source \?\? "okx-ws"\);/);
  assert.match(workspaceSource, /const chartRealtime = useRealtimeFeed\(\{/);
  assert.match(workspaceSource, /topics: \["market\.candles"\]/);
  assert.match(workspaceSource, /const \[chartSnapshot, setChartSnapshot\]/);
  assert.match(workspaceSource, /payload\.snapshot/);
  assert.doesNotMatch(chartSource, /topics: \["market\.candles"\]/);
  assert.doesNotMatch(chartSource, /topics: \["market\.ticker"\]/);
  assert.match(workspaceSource, /payload\.type === "market\.candles" && payload\.instId === selected && payload\.bar === chartBar/);
  assert.match(workspaceSource, /const \[chartSource, setChartSource\]/);
  assert.match(source, /const \{ filteredInstruments, displayedInstruments, realtimeSubscriptionInstruments \} = useMarketInstrumentRows/);
  assert.match(workspaceSource, /realtimeSubscriptionInstruments\.map\(\(item\) => item\.inst_id\)/);
  assert.doesNotMatch(source, /displayedInstruments\.slice\(0, 80\)/);
  assert.match(source, /marketNoticeSlot/);
  assert.match(source, /className="candleInspector"/);
  assert.match(source, /chart\.subscribeCrosshairMove\(handleCrosshairMove\)/);
  assert.match(source, /const detailCandle = hoveredCandleTime === null \? latestCandle : candleByChartTime\.get\(hoveredCandleTime\) \?\? latestCandle;/);
  assert.match(source, /统计部分回退/);
  assert.match(source, /!\s*compact && uniqueWarnings\.length/);
  assert.doesNotMatch(source, /<section className="marketStats">/);
  assert.doesNotMatch(source, /label="上一根变化"/);
  assert.match(source, /compactRealtimeWarning/);
  assert.match(source, /topic\?: string/);
  assert.match(source, /部分价格实时订阅失败，已保留 REST\/缓存快照。/);
  assert.match(source, /source === "partial-fallback"/);
  assert.match(source, /payload\.source === "partial-fallback"/);
  assert.match(source, /payload\.skippedInstIds\?\.includes\(selected\)/);
  assert.match(workspaceSource, /compactRealtimeWarning\(payload\.message \?\? payload\.warning, payload\.topic\)/);
  assert.doesNotMatch(aiSource, /useRealtimeFeed\(\{/);
  assert.doesNotMatch(statsSource, /useRealtimeFeed\(\{/);
  assert.match(source, /const tradeRealtime = useRealtimeFeed\(\{/);
  assert.match(source, /topics: \["market\.ticker", "account", "positions"\]/);
  const ordersStart = source.indexOf("function OrdersPage(");
  const ordersSource = source.slice(ordersStart, source.indexOf("function strategyInstrumentLabel("));
  assert.match(ordersSource, /topics: \["orders"\]/);
  assert.match(ordersSource, /payload\.type === "order\.update"/);
  assert.match(ordersSource, /onSnapshotRequired: \(payload\) => \{[\s\S]*?loadOrders\(\)/);
  assert.match(source, /loadTickers\(\)\.catch\(\(\) => undefined\)/);
});

test("account positions and automation use realtime as refresh signals over rest snapshots", () => {
  assert.match(source, /const positionsRealtime = useRealtimeFeed\(\{/);
  assert.match(source, /const accountRealtime = useRealtimeFeed\(\{/);
  assert.match(source, /const cleanAutomationRealtime = useRealtimeFeed\(\{/);
  assert.match(source, /const signalLogRealtime = useRealtimeFeed\(\{/);
  assert.match(source, /loadAccount\(true\)\.catch\(\(\) => undefined\)/);
  assert.match(source, /loadSignalLogs\(\)\.catch\(\(\) => undefined\)/);
});

test("query oriented pages remain rest first", () => {
  assert.match(source, /\/api\/trading\/leverage\?instId=/);
  assert.match(source, /\/api\/announcements\/types/);
  assert.match(source, /\/api\/earn\/offers/);
  assert.match(source, /\/api\/automation\/signals\?limit=300/);
});
