import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("shared loading primitives announce real request states and respect reduced motion", () => {
  assert.match(source, /function DataLoadingState\(/);
  assert.match(source, /role="status" aria-live="polite"/);
  assert.match(source, /function DataLoadingSkeleton\(/);
  assert.match(source, /aria-hidden="true"/);
  assert.match(styles, /\.dataLoadingState\s*\{/);
  assert.match(styles, /\.dataLoadingSkeleton\s*\{/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.dataLoadingSpinner,[\s\S]*?animation: none;/);
});

test("shared market workspace distinguishes first loads from retained-data refreshes", () => {
  const workspace = source.slice(source.indexOf("function MarketContractWorkspace("), source.indexOf("function MarketPage("));
  assert.match(workspace, /const \[instrumentsLoading, setInstrumentsLoading\]/);
  assert.match(workspace, /const \[tickersLoading, setTickersLoading\]/);
  assert.match(workspace, /const \[chartLoading, setChartLoading\]/);
  assert.match(workspace, /loading=\{instrumentsLoading\}/);
  assert.match(workspace, /setChartLoading\(true\)/);
  assert.match(workspace, /setChartLoading\(false\)/);
  const rail = source.slice(source.indexOf("function MarketInstrumentRail("), source.indexOf("function MarketContractWorkspace("));
  assert.match(rail, /<DataLoadingSkeleton variant="rail" label="正在读取合约列表"/);
  assert.match(rail, /disabled=\{loading\} aria-busy=\{loading\}/);
});

test("market chart, AI analysis, and statistics provide safe loading behavior", () => {
  const marketPage = source.slice(source.indexOf("function MarketPage("), source.indexOf("function MarketAiOutlookPage("));
  const aiPage = source.slice(source.indexOf("function MarketAiOutlookPage("), source.indexOf("function MarketStatsPage("));
  const statsHook = source.slice(source.indexOf("function useMarketStats("), source.indexOf("type MarketStatsModel"));
  const panel = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(marketPage, /const initialChartLoading = chartLoading && candles\.length === 0;/);
  assert.match(marketPage, /chartLoadingOverlay/);
  assert.match(aiPage, /const analysisAvailable = Boolean\(chartSnapshot\?\.snapshotId\);/);
  assert.match(panel, /disabled=\{loading \|\| !analysisAvailable\}/);
  assert.match(panel, /图表准备中/);
  assert.doesNotMatch(statsHook, /setMarketStats\(null\)/);
  assert.match(source, /const initialStatsLoading = stats\.marketStatsLoading && !stats\.marketStats;/);
  assert.match(source, /统计更新中/);
});

test("list and account pages do not confuse initial data loading with completed empty data", () => {
  assert.match(source, /正在读取已保存日历/);
  assert.match(source, /正在读取公告分类/);
  assert.match(source, /正在读取公告列表/);
  assert.match(source, /const earnInitialLoading = refreshing && !offers/);
  assert.match(source, /const accountInitialLoading = accountRefreshing && !account;/);
  assert.match(source, /正在读取当前持仓与账户摘要/);
  assert.match(source, /正在读取账户资产与余额/);
  assert.match(source, /正在读取自动交易状态/);
  assert.match(source, /正在读取 AI 用量记录/);
});
