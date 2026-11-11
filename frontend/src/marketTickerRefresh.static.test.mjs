import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");

test("ticker refresh payload has a structured compatibility contract", () => {
  assert.match(source, /type TickerRefresh = \{/);
  assert.match(source, /state\?: "fresh" \| "refreshing" \| "backing_off" \| "stale" \| "initializing" \| "unavailable"/);
  assert.match(source, /type TickersResponse = \{[\s\S]*?refresh\?: TickerRefresh/);
  assert.match(source, /const payload = \(await response\.json\(\)\) as TickersResponse;/);
  assert.match(source, /setTickerRefresh\(payload\.refresh \?\? null\);/);
});

test("market workspace translates retained ticker snapshots without raw transport text", () => {
  const helperSource = source.slice(source.indexOf("function tickerRefreshStatus"), source.indexOf("function compactRealtimeWarning"));
  assert.match(helperSource, /列表快照 · 自动重试/);
  assert.match(helperSource, /列表快照 · 后台刷新/);
  assert.match(helperSource, /行情列表暂不可用，正在等待完整行情快照/);
  assert.match(helperSource, /所选合约价格仍在实时更新/);
  assert.doesNotMatch(helperSource, /IncompleteRead/);

  const workspaceSource = source.slice(source.indexOf("function MarketContractWorkspace"), source.indexOf("function MarketPage"));
  assert.match(workspaceSource, /tickerRefresh/);
  assert.match(workspaceSource, /setWarning\(payload\.warning \?\? ""\);/);
  assert.doesNotMatch(workspaceSource, /OKX response was incomplete after retries/);
});

test("all market workspace pages surface compact ticker freshness state", () => {
  const marketPageSource = source.slice(source.indexOf("function MarketPage"), source.indexOf("function MarketAiOutlookPage"));
  const aiPageSource = source.slice(source.indexOf("function MarketAiOutlookPage"), source.indexOf("function MarketStatsPage"));
  const statsPageSource = source.slice(source.indexOf("function MarketStatsPage"), source.indexOf("function MarketAnnouncementsPage"));

  [marketPageSource, aiPageSource, statsPageSource].forEach((pageSource) => {
    assert.match(pageSource, /tickerRefreshStatus\(tickerRefresh, tickerRealtime\.connected\)/);
    assert.match(pageSource, /title=\{tickerFreshness\.detail\}/);
    assert.match(pageSource, /\{tickerFreshness\.pill\}/);
  });
});
