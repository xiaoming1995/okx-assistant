import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("market stats load selected contract trading stats through backend API", () => {
  assert.match(source, /type MarketStatsResponse = \{/);
  assert.match(source, /fetch\(`\$\{API_BASE\}\/api\/market\/stats\?\$\{params\.toString\(\)\}`\)/);
  assert.match(source, /new URLSearchParams\(\{ instId: selected, period: requestedStatsPeriod, limit: "100" \}\)/);
});

test("market stats retain complete values while a refresh is in progress", () => {
  const statsHook = source.slice(source.indexOf("function useMarketStats("), source.indexOf("type MarketStatsModel"));
  assert.doesNotMatch(statsHook, /setMarketStats\(null\);/);
  assert.match(statsHook, /const displayedMarketStats = marketStats\?\.instId === selected \? marketStats : null;/);
  assert.match(statsHook, /if \(!selected\) \{/);
  assert.match(source, /统计更新中/);
  assert.match(source, /\}, \[reloadNonce, requestedStatsPeriod, selected\]\);/);
});

test("market stats expose forced retry wiring", () => {
  assert.match(source, /const reload = React\.useCallback\(\(options\?: \{ force\?: boolean \}\) => \{/);
  assert.match(source, /if \(force\) params\.set\("force", "true"\);/);
  assert.match(source, /onClick=\{\(\) => stats\.reload\(\{ force: true \}\)\}/);
  assert.match(source, /重新加载交易统计/);
});

test("market stats page separates realtime prices from period-based statistics", () => {
  assert.match(source, /const marketStatsPeriodMs: Record<string, number> = \{/);
  assert.match(source, /function nextMarketStatsRefreshDelay\(period: string\)/);
  assert.match(source, /stats\.reload\(\{ force: true \}\);/);
  assert.match(source, /价格实时/);
  assert.match(source, /价格REST回退/);
  assert.match(source, /`统计\$\{stats\.displayedStatsPeriod\}\$\{sourceLabel\(stats\.marketStats\?\.source\)\}`/);
});

test("market stats expose effective period when it differs from chart period", () => {
  assert.match(source, /function effectiveMarketStatsPeriod\(bar: string\)/);
  assert.match(source, /const statsPeriodMismatch = requestedStatsPeriod !== displayedStatsPeriod;/);
  assert.match(source, /统计周期 \{stats\.displayedStatsPeriod\}，不同于当前 K线 \{stats\.requestedStatsPeriod\}/);
  assert.match(source, /compact\?: boolean;/);
  assert.match(source, /!\s*compact \? \(/);
});

test("market stats render contract-level structure without direct trading instructions", () => {
  assert.match(source, /label="合约多空人数比"/);
  assert.match(source, /label="主动买入占比"/);
  assert.match(source, /label="持仓量 USD"/);
  assert.match(source, /净多账户较多/);
  assert.match(source, /主动买入占优/);
  assert.match(source, /持仓增加/);
  assert.doesNotMatch(source, /建议做多|建议做空|强烈买入|强烈卖出|必须交易/);
});

test("market keeps a dedicated trading data page", () => {
  assert.match(source, /type MarketTab = "radar" \| "chart" \| "aiOutlook" \| "aiRecords" \| "stats" \| "announcements" \| "usTimeline" \| "overview";/);
  assert.match(source, /parts\[1\] === "announcements"[\s\S]*?\? "announcements"[\s\S]*?: parts\[1\] === "stats"[\s\S]*?\? "stats"/);
  assert.match(source, /label: "交易数据"/);
  assert.match(source, /<MarketContractWorkspace[\s\S]*?selected=\{selectedContract\}/);
  assert.match(source, /<MarketStatsPage \/>/);
  assert.match(source, /function MarketStatsPage\(\)[\s\S]*?useMarketContractWorkspace\(\)/);
});

test("market chart prioritizes summary, contextual candle inspection, and the main price pane", () => {
  const marketPageStart = source.indexOf("function MarketPage(");
  const statsPageStart = source.indexOf("function MarketAiOutlookPage(");
  assert.ok(marketPageStart > -1);
  assert.ok(statsPageStart > marketPageStart);
  const marketPageSource = source.slice(marketPageStart, statsPageStart);
  const statsPageSource = source.slice(statsPageStart);

  assert.doesNotMatch(marketPageSource, /const stats = useMarketStats\(selected, bar\);/);
  assert.doesNotMatch(marketPageSource, /<TradingStatsSummary/);
  assert.doesNotMatch(marketPageSource, /<TradingStatsDetails/);
  assert.doesNotMatch(marketPageSource, /<section className="marketStats">/);
  assert.doesNotMatch(marketPageSource, /className="klineDetailsGrid"/);
  assert.doesNotMatch(marketPageSource, /<p>\{status\}<\/p>/);
  assert.match(marketPageSource, /className="candleInspector"/);
  assert.match(marketPageSource, /label=\{hoveredCandleTime === null \? "最新K线" : "查看K线"\}/);
  assert.match(marketPageSource, /label="开盘价"/);
  assert.match(marketPageSource, /label="最高价"/);
  assert.match(marketPageSource, /label="最低价"/);
  assert.match(marketPageSource, /label="收盘价"/);
  assert.match(marketPageSource, /label="成交额"/);
  assert.match(marketPageSource, /label="成交量（张）"/);
  assert.match(marketPageSource, /title="K线节点详情"/);
  assert.match(marketPageSource, /节点详情/);
  assert.doesNotMatch(marketPageSource, /label="K线状态"/);
  assert.doesNotMatch(marketPageSource, /label="价格更新"/);
  assert.doesNotMatch(marketPageSource, /label="K线来源"/);
  assert.match(marketPageSource, /chart\.subscribeCrosshairMove\(handleCrosshairMove\)/);
  assert.match(source, /function toVolumeData\(/);
  assert.match(marketPageSource, /chart\.addSeries\(HistogramSeries,[\s\S]*?, 1\)/);
  assert.match(marketPageSource, /volumeSeries\.setData\(toVolumeData\(candles\)\)/);
  assert.match(marketPageSource, /成交量（张）/);
  assert.match(source, /function normalizeCandleBatch\(candles: Candle\[\]\): Candle\[\]/);
  assert.match(source, /const RECENT_CANDLE_WINDOW = 48;/);
  assert.match(source, /function newestCandleWindow\(candleCount: number\)/);
  assert.match(source, /chart\.timeScale\(\)\.setVisibleLogicalRange\(newestCandleWindow\(candleCount\)\);/);
  assert.match(marketPageSource, /className="secondaryButton slim latestChartButton"/);
  assert.match(marketPageSource, /onClick=\{focusCurrentTrend\}/);
  assert.match(statsPageSource, /<TradingStatsSummary/);
  assert.match(statsPageSource, /<TradingStatsDetails stats=\{stats\} \/>/);
});

test("market workbench preserves direct-entry defaults and centralizes the self-selected empty-state recovery", () => {
  const marketPageStart = source.indexOf("function MarketPage(");
  const aiOutlookPageStart = source.indexOf("function MarketAiOutlookPage(");
  const statsPageStart = source.indexOf("function MarketStatsPage(");
  const workspaceStart = source.indexOf("function MarketContractWorkspace(");
  const workspaceEnd = marketPageStart;
  const marketPageSource = source.slice(marketPageStart, aiOutlookPageStart);
  const aiOutlookPageSource = source.slice(aiOutlookPageStart, statsPageStart);
  const statsPageSource = source.slice(statsPageStart);
  const workspaceSource = source.slice(workspaceStart, workspaceEnd);

  assert.match(source, /initialFilter=\{marketWorkbenchInitialFilter \?\? \(marketTab === "chart" \? "watch" : "usdt"\)\}/);
  assert.match(workspaceSource, /const \[filter, setFilter\] = React\.useState<InstrumentFilter>\(initialFilter\);/);
  assert.match(workspaceSource, /const showWatchlistEmptyState =\s*filter === "watch" && query\.trim\(\) === "" && instruments\.length > 0 && filteredInstruments\.length === 0;/);
  assert.match(workspaceSource, /暂无本地已关注合约/);
  assert.match(workspaceSource, /onClick=\{\(\) => setFilter\("all"\)\}/);
  assert.match(workspaceSource, /查看全部合约/);
  assert.doesNotMatch(marketPageSource, /<MarketInstrumentRail/);
  assert.doesNotMatch(aiOutlookPageSource, /<MarketInstrumentRail/);
  assert.doesNotMatch(statsPageSource, /<MarketInstrumentRail/);
  assert.match(source, /emptyState\?: React\.ReactNode;/);
});

test("market chart derives bounded moving-average overlays and visible-range context", () => {
  const marketPageStart = source.indexOf("function MarketPage(");
  const statsPageStart = source.indexOf("function MarketAiOutlookPage(");
  const marketPageSource = source.slice(marketPageStart, statsPageStart);

  assert.match(source, /const MOVING_AVERAGES = \[/);
  assert.match(source, /\{ key: "ma5", label: "MA5", period: 5, color: "#e5a823" \}/);
  assert.match(source, /\{ key: "ma10", label: "MA10", period: 10, color: "#d34b78" \}/);
  assert.match(source, /\{ key: "ma20", label: "MA20", period: 20, color: "#32afbf" \}/);
  assert.match(source, /function calculateMovingAverage\(candles: Candle\[\], period: number\): LineData\[\]/);
  assert.match(source, /function calculateMovingAverages\(candles: Candle\[\]\): MovingAverageBundle/);
  assert.match(source, /function candleCloseCountdown\(candle: Candle \| null \| undefined, bar: string, currentMs: number\)/);
  assert.match(source, /function visibleCandleExtrema\(candles: Candle\[\], range: LogicalRange \| null\)/);
  assert.match(source, /function extremaMarkers\(extrema: ReturnType<typeof visibleCandleExtrema>\): SeriesMarker<Time>\[\]/);
  assert.match(marketPageSource, /chart\.addSeries\(LineSeries,/);
  assert.match(marketPageSource, /createSeriesMarkers\(series, \[\], \{ autoScale: false \}\)/);
  assert.match(marketPageSource, /subscribeVisibleLogicalRangeChange\(handleVisibleRangeChange\)/);
  assert.match(marketPageSource, /className="chartTrendLegend"/);
  assert.match(marketPageSource, /className="chartCountdownOverlay"/);
  assert.match(marketPageSource, /candleCloseCountdown\(latestCandle, bar, chartClock\)/);
  assert.match(styles, /\.chartTrendLegend\s*\{/);
  assert.match(styles, /\.chartCountdownOverlay\s*\{/);
});

test("market chart preserves navigation and uses the remaining desktop workbench height", () => {
  assert.match(source, /<section className="marketMain marketChartMain">/);
  assert.match(styles, /\.candleInspector\s*\{[\s\S]*?grid-template-columns: minmax\(188px, 1\.5fr\) repeat\(2, minmax\(112px, 1fr\)\) auto;[\s\S]*?\}/);
  assert.match(styles, /\.chartArea\s*\{[\s\S]*?flex: 1 1 auto;[\s\S]*?\}/);
  assert.match(styles, /\.marketChartMain \.chartPanel\s*\{[\s\S]*?flex: 1 1 0;[\s\S]*?min-height: 0;[\s\S]*?\}/);
  assert.match(styles, /@media \(min-width: 1201px\) and \(min-height: 641px\) and \(max-height: 719px\)/);
  assert.match(styles, /\.marketChartMain\s*\{[\s\S]*?overflow-y: auto;[\s\S]*?\}/);
  assert.match(source, /const visibleRange = chart\.timeScale\(\)\.getVisibleLogicalRange\(\);/);
  assert.match(source, /visibleRange\.to >= previousCandleCountRef\.current - 1 - 2/);
  assert.match(source, /if \(!hasFittedChartRef\.current\) \{[\s\S]*?chart\.timeScale\(\)\.fitContent\(\);/);
  assert.match(source, /chart\.timeScale\(\)\.fitContent\(\);[\s\S]*?focusNewestCandleWindow\(chart, candles\.length\);/);
  assert.match(source, /else if \(wasViewingNewestEdge\) \{[\s\S]*?chart\.timeScale\(\)\.scrollToRealTime\(\);/);
  assert.match(styles, /@media \(min-width: 1201px\) and \(max-height: 640px\)/);
  assert.match(styles, /\.marketChartMain \.candleInspector\s*\{[\s\S]*?grid-template-columns: minmax\(188px, 1\.5fr\) repeat\(2, minmax\(112px, 1fr\)\) auto;[\s\S]*?\}/);
  assert.match(styles, /\.marketStats, \.tradingStatsGrid, \.candleInspector,[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
});

test("market chart moves TradingView attribution out of the plot area", () => {
  assert.match(source, /attributionLogo: false/);
  assert.match(source, /href="https:\/\/www\.tradingview\.com\/"/);
  assert.match(source, /className="chartHeaderMeta"/);
});
