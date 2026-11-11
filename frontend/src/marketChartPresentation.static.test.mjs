import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { runInNewContext } from "node:vm";
import { transformSync } from "esbuild";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
const chartPage = source.slice(source.indexOf("function MarketPage("), source.indexOf("function MarketAiOutlookPage("));
const orderBook = source.slice(source.indexOf("function MarketOrderBook("), source.indexOf("function MarketPage("));
const warningHelper = source.slice(source.indexOf("function compactRealtimeWarning("), source.indexOf("function isTransientMarketWsError("));

test("chart header separates page action, data status, and view controls", () => {
  assert.match(chartPage, /<PageHeader eyebrow="实时行情" title="行情图表" actions=\{/);
  assert.match(chartPage, /<div className="marketChartToolbar" aria-label="图表工具栏">/);
  assert.match(chartPage, /<div className="marketChartDataStatus" aria-label="行情数据状态">/);
  assert.match(chartPage, /<div className="marketChartViewControls" aria-label="图表视图">/);
  assert.match(styles, /\.marketChartToolbar\s*\{[\s\S]*?padding: var\(--space-2\) var\(--space-3\);/);
  assert.match(styles, /@media \(max-width: 767px\)\s*\{[\s\S]*?\.marketChartViewControls\s*\{[\s\S]*?overflow-x: auto;/);
});

test("chart statuses never expose raw transport exceptions", () => {
  assert.match(warningHelper, /if \(!text\) return "";/);
  assert.match(warningHelper, /websocket\|connection\|nonetype\|resume_reading/);
  assert.match(warningHelper, /价格实时连接暂不可用，系统正在自动重连。/);
  assert.match(warningHelper, /K线数据暂未更新，系统正在自动重试。/);
  assert.match(chartPage, /compactRealtimeWarning\(tickerRealtime\.warning, "market\.ticker"\)/);
  assert.match(chartPage, /compactRealtimeWarning\(candleWarning, "market\.candles"\)/);
  assert.match(chartPage, /const candleStreamLive = marketRealtime\.connected && candleSourceLive;/);
  assert.match(chartPage, /candles\.length === 0 \? initialChartLoading \? "数据加载中" : "暂无K线数据" : candleStreamLive \? "实时推送" : "最近可用数据"/);
  assert.match(chartPage, /candles\.length === 0 \? "K线准备中"/);
});

test("technical WebSocket failures become scoped Chinese status, while useful warnings remain", () => {
  const plainHelper = warningHelper.replace("message?: string, topic?: string", "message, topic");
  const compactWarning = runInNewContext(`${plainHelper}; compactRealtimeWarning`);
  const rawFailure = "OKX ticker WebSocket connection failed: 'NoneType' object has no attribute 'resume_reading'";

  assert.equal(compactWarning(), "");
  assert.equal(compactWarning(rawFailure, "market.ticker"), "价格实时连接暂不可用，系统正在自动重连。");
  assert.equal(compactWarning(rawFailure, "market.candles"), "K线数据暂未更新，系统正在自动重试。");
  assert.equal(compactWarning("当前行情使用缓存", "market.ticker"), "当前行情使用缓存");
});

test("candle detail dialog keeps the selected node instead of following later hover updates", () => {
  assert.match(chartPage, /const \[candleDetail, setCandleDetail\] = React\.useState<CandleDetailSnapshot \| null>\(null\)/);
  assert.match(chartPage, /openCandleAtTimeRef\.current = \(time\) => openCandleDetail\(candleByChartTime\.get\(time\)\)/);
  assert.match(chartPage, /chart\.subscribeClick\(handleChartClick\)/);
  assert.match(chartPage, /chart\.unsubscribeClick\(handleChartClick\)/);
  assert.match(chartPage, /candle: \{ \.\.\.candle \}/);
  assert.match(chartPage, /<Modal[\s\S]*?opened=\{candleDetail !== null\}[\s\S]*?title="K线节点详情"/);
  assert.match(chartPage, /disabled=\{!detailCandle\}/);
  assert.match(chartPage, /涨跌以前一根K线收盘价为基准/);
  assert.match(chartPage, /selectedCandleAmplitude\.toLocaleString\("zh-CN", \{ maximumFractionDigits: 2 \}\)/);
  assert.match(chartPage, /candleDetail\.candle\.volumeQuote \? <CandleInspectorMetric label="成交额"/);
  assert.match(chartPage, /当前数据源未提供该节点成交额/);
  assert.match(styles, /\.candleDetailGrid\s*\{[\s\S]*?grid-template-columns: repeat\(4, minmax\(0, 1fr\)\)/);
  assert.match(styles, /\.marketChartMain \.candleInspectorMetric:first-child,[\s\S]*?grid-column: 1 \/ -1/);
});

test("near-zero candle changes render as neutral zero after two-decimal rounding", () => {
  const helperSource = source.slice(source.indexOf("function displayCandlePercent("), source.indexOf("function candleAmplitude("));
  const plainHelper = helperSource.replace("value: number | null", "value");
  const displayCandlePercent = runInNewContext(`${plainHelper}; displayCandlePercent`);

  assert.equal(displayCandlePercent(-0.004), 0);
  assert.equal(displayCandlePercent(0.004), 0);
  assert.equal(displayCandlePercent(-0.006), -0.01);
  assert.equal(displayCandlePercent(null), null);
  assert.match(chartPage, /detailCandlePercent === 0 \? "" : changeClass\(detailCandlePercent\)/);
  assert.match(chartPage, /selectedCandlePercent === 0 \? "" : changeClass\(selectedCandlePercent\)/);
});

test("chart volume and headline metrics keep period and unit boundaries", () => {
  assert.match(source, /function toVolumeData\(candles: Candle\[\]\)/);
  assert.match(chartPage, /volumeSeries\.setData\(toVolumeData\(candles\)\)/);
  assert.match(chartPage, /const dayChange = tickerChangeFromBases\(selectedTicker, \["sodUtc8"\]\);/);
  assert.match(chartPage, /const activity24h = market24hActivity\(selectedTicker, selected\);/);
  assert.match(chartPage, /label=\{activity24h\.label\} value=\{activity24h\.value\}/);
  assert.match(source, /label: `24h 成交量（\$\{base\}）`/);
  assert.match(source, /label: "24h 成交量（张）"/);
  assert.doesNotMatch(chartPage, /latestCandle\?\.volumeQuote/);
});

test("volume bars follow candle timestamps and leave unavailable volume blank", () => {
  const helper = source.slice(source.indexOf("function toVolumeData("), source.indexOf("const RECENT_CANDLE_WINDOW"));
  const toVolumeData = runInNewContext(`${transformSync(helper, { loader: "ts" }).code}; toVolumeData`);
  const result = toVolumeData([
    { ts: "1000", open: "10", close: "11", volume: "12.5" },
    { ts: "2000", open: "11", close: "10", volume: "0" },
    { ts: "3000", open: "10", close: "11", volume: "" },
    { ts: "4000", open: "10", close: "11", volume: "bad" }
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(result)), [
    { time: 1, value: 12.5, color: "#1dbf73" },
    { time: 2, value: 0, color: "#f05d6f" },
    { time: 3 },
    { time: 4 }
  ]);
});

test("24-hour activity chooses a valid quote, base, or contract unit", () => {
  const helper = source.slice(source.indexOf("function market24hActivity("), source.indexOf("function instrumentActivityLabel("));
  const market24hActivity = runInNewContext(`${transformSync(helper, { loader: "ts" }).code}; market24hActivity`, {
    instrumentCurrencies: () => ({ base: "ETH", quote: "USDT" }),
    toNumber: (value) => value === undefined || value === null || value === "" || !Number.isFinite(Number(value)) ? null : Number(value),
    formatCompact: (value) => String(value)
  });
  const activity = (ticker) => JSON.parse(JSON.stringify(market24hActivity(ticker, "ETH-USDT-SWAP")));
  assert.deepEqual(activity({ volCcyQuote24h: "1000", volCcy24h: "2", vol24h: "20" }), { label: "24h 成交额（USDT）", value: "1000", unit: "USDT" });
  assert.deepEqual(activity({ volCcyQuote24h: "bad", volCcy24h: "2", vol24h: "20" }), { label: "24h 成交量（ETH）", value: "2", unit: "ETH" });
  assert.deepEqual(activity({ volCcy24h: "", vol24h: "20" }), { label: "24h 成交量（张）", value: "20", unit: "张" });
  assert.deepEqual(activity({ volCcyQuote24h: "-1", volCcy24h: "bad" }), { label: "24h 成交量", value: "--", unit: "" });
});

test("read-only depth stays scoped to selected visible contract and expires stale levels", () => {
  assert.match(orderBook, /document\.hidden/);
  assert.match(orderBook, /controller\?\.abort\(\)/);
  assert.match(orderBook, /next\.instId === instId/);
  assert.match(orderBook, /response\?\.instId === instId/);
  assert.match(orderBook, /Date\.now\(\) - current\.data\.ts <= 15_000/);
  assert.match(orderBook, /数量（张）/);
  assert.match(orderBook, /累计（张）/);
  assert.doesNotMatch(orderBook, /下单|买入|卖出/);
  assert.match(chartPage, /<MarketOrderBook instId=\{selected\} \/>/);
  assert.match(styles, /@container \(min-width: 960px\)/);
});
