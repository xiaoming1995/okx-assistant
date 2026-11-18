import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { runInNewContext } from "node:vm";
import { transformSync } from "esbuild";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const page = source.slice(
  source.indexOf("function MarketOverviewPage("),
  source.indexOf("function UsMarketTimelinePage(")
);

const toNumber = (value) =>
  value === undefined || value === null || value === "" || !Number.isFinite(Number(value)) ? null : Number(value);

function overviewHelpers() {
  const helper = [
    source.slice(source.indexOf("function tickerValue("), source.indexOf("function formatSigned(")),
    source.slice(source.indexOf("function instrumentQuoteTurnover("), source.indexOf("function relevanceRank(")),
    source.slice(source.indexOf("function overviewEventRelativeTime("), source.indexOf("function overviewShanghaiTime("))
  ].join("\n");
  return transformSync(helper, { loader: "ts" }).code;
}

test("market overview reads a two-sided event window and never leaves a misleading empty card", () => {
  assert.match(source, /const OVERVIEW_EVENT_PAST_DAYS = 7;/);
  assert.match(source, /const OVERVIEW_EVENT_FUTURE_DAYS = 31;/);
  assert.match(page, /shiftTimelineDate\(today, -OVERVIEW_EVENT_PAST_DAYS\)/);
  assert.match(page, /shiftTimelineDate\(today, OVERVIEW_EVENT_FUTURE_DAYS\)/);
  assert.match(page, /new Map<string, UsMarketEvent>\(\)/);
  assert.match(page, /过去 7 天与未来 31 天/);
  assert.match(page, /overviewEventRelativeTime\(event\.scheduledAt \?\? 0\)/);
  assert.match(page, /官方日历正在后台同步，完成后自动显示。/);
  assert.match(page, /\$\{healthyProviders\}\/\$\{eventProviders\.length\} 个来源正常/);
  assert.doesNotMatch(page, /官方事件正在同步。/);
  assert.doesNotMatch(page, /未来两周暂无可显示的美国事件。/);
  assert.doesNotMatch(page, /shiftTimelineDate\(today, 14\)/);
});

test("event rows count down to upcoming releases and mark already published items", () => {
  const fixedNow = 1_800_000_000_000;
  const FixedDate = class extends Date {
    static now() { return fixedNow; }
  };
  const relativeTime = runInNewContext(
    `${overviewHelpers()}; overviewEventRelativeTime`,
    { Date: FixedDate, toNumber }
  );
  assert.equal(relativeTime(fixedNow + 3 * 86_400_000), "3 天后");
  assert.equal(relativeTime(fixedNow + 2 * 3_600_000), "2 小时后");
  assert.equal(relativeTime(fixedNow + 60_000), "即将公布");
  assert.equal(relativeTime(fixedNow - 86_400_000), "已公布");
  assert.match(page, /className=\{`marketOverviewEvent\$\{upcoming \? "" : " isPast"\}`\}/);
  assert.match(styles, /\.marketOverviewEvent\.isPast strong \{/);
});

test("market breadth is computed from the shared ticker snapshot with quote turnover", () => {
  assert.match(page, /const breadth = React\.useMemo\(\(\) => overviewMarketBreadth\(tickers\?\.data\), \[tickers\]\);/);
  assert.match(page, /aria-label="市场宽度"/);
  assert.match(page, /24h 成交额（估算）/);
  assert.match(page, /const turnover = instrumentQuoteTurnover\(ticker\);/);
  assert.doesNotMatch(page, /const activity = market24hActivity\(ticker, instId\);/);
  assert.match(page, /className="marketOverviewVolumeComparison"/);
  assert.match(page, /const contractShare = platformVolUsd/);
  assert.match(styles, /grid-template-areas: "volume events" "tickers breadth";/);
  assert.match(styles, /grid-template-areas: "volume" "events" "tickers" "breadth";/);
  assert.match(styles, /align-items: stretch;/);
  assert.match(styles, /\.marketOverviewPanel > \.marketOverviewSource:last-child/);

  const overviewMarketBreadth = runInNewContext(
    `${overviewHelpers()}; overviewMarketBreadth`,
    { toNumber }
  );
  const tickers = [
    { instId: "BTC-USDT-SWAP", last: "68000", open24h: "66000", volCcy24h: "100" },
    { instId: "ETH-USDT-SWAP", last: "2000", open24h: "2200", volCcy24h: "500" },
    { instId: "SOL-USDT-SWAP", last: "100", open24h: "100", volCcy24h: "10" },
    // 6.2e13 个 SATS 只值约 49.8 万 USDT：涨幅榜按百分比、成交额按计价币折算。
    { instId: "SATS-USDT-SWAP", last: "0.000000008", open24h: "0.000000004", volCcy24h: "62254890000000" },
    { instId: "TEST002-USDT-SWAP", last: "1", open24h: "2", volCcy24h: "1" },
    { instId: "BAD-USDT-SWAP", last: "invalid", open24h: "1", volCcy24h: "1" },
    { instId: "BTC-USDT", last: "1", open24h: "2", volCcy24h: "1" }
  ];
  const breadth = overviewMarketBreadth(tickers);
  assert.equal(breadth.total, 4);
  assert.equal(breadth.up, 2);
  assert.equal(breadth.down, 1);
  assert.equal(breadth.flat, 1);
  assert.equal(breadth.sentiment, "分化");
  assert.equal(breadth.gainers.map((row) => row.instId).join(","), "SATS-USDT-SWAP,BTC-USDT-SWAP");
  assert.equal(breadth.losers.map((row) => row.instId).join(","), "ETH-USDT-SWAP");
  assert.ok(Math.abs(breadth.turnoverUsd - 8_299_039.12) < 1);
  assert.ok(breadth.medianChange > 3 && breadth.medianChange < 3.1);

  const empty = overviewMarketBreadth([]);
  assert.equal(empty.total, 0);
  assert.equal(empty.sentiment, "--");
  assert.equal(empty.turnoverUsd, null);
  assert.equal(empty.gainers.length, 0);
  assert.equal(empty.losers.length, 0);
});

test("US event titles and providers are translated in both the overview and the full calendar", () => {
  assert.match(source, /const US_EVENT_TITLE_ZH: Record<string, string> = \{/);
  assert.match(source, /function usEventDisplayTitle\(event: Pick<UsMarketEvent, "title" \| "provider">\)/);
  assert.match(source, /function usEventProviderLabel\(/);
  assert.match(page, /<strong title=\{`官方名称：\$\{event\.title\}`\}>\{usEventDisplayTitle\(event\)\}<\/strong>/);
  assert.match(page, /\{usEventProviderLabel\(event\.provider\)\}/);
  assert.doesNotMatch(page, /<strong title=\{event\.title\}>\{event\.title\}<\/strong>/);
  assert.match(source, /<strong>\{usEventDisplayTitle\(event\)\}<\/strong>/);
  assert.match(source, /unavailableProviders\.map\(\(item\) => usEventProviderLabel\(item\.provider\)\)/);

  const translationHelpers = source.slice(
    source.indexOf("const US_EVENT_TITLE_ZH"),
    source.indexOf("const OVERVIEW_CONTRACTS")
  );
  const helpers = runInNewContext(
    `${transformSync(translationHelpers, { loader: "ts" }).code}; ({ usEventDisplayTitle, usEventProviderLabel })`,
    {}
  );
  assert.equal(helpers.usEventDisplayTitle({ title: "Consumer Price Index", provider: "BLS" }), "美国 CPI（消费者物价指数）");
  assert.equal(helpers.usEventDisplayTitle({ title: "Job Openings and Labor Turnover", provider: "BLS" }), "JOLTS 职位空缺（美国）");
  assert.equal(helpers.usEventDisplayTitle({ title: "Producer Price Index", provider: "BLS" }), "美国 PPI（生产者物价指数）");
  assert.equal(helpers.usEventDisplayTitle({ title: "FOMC 会议与利率决议", provider: "Federal Reserve" }), "美联储利率决策（美国）");
  assert.equal(helpers.usEventDisplayTitle({ title: "FOMC 会议（美国）", provider: "Federal Reserve" }), "FOMC 会议（美国）");
  assert.equal(helpers.usEventDisplayTitle({ title: "Unlisted Release", provider: "BLS" }), "Unlisted Release");
  assert.equal(helpers.usEventProviderLabel("BLS"), "美国劳工统计局");
  assert.equal(helpers.usEventProviderLabel("Federal Reserve"), "美联储");
  assert.equal(helpers.usEventProviderLabel(""), "官方来源");
  assert.equal(helpers.usEventProviderLabel("Unknown Agency"), "Unknown Agency");
});

test("a healthy background refresh does not raise a stale-snapshot warning", () => {
  assert.match(page, /const tickerStale = Boolean\(tickers\?\.data\?\.length && \(/);
  assert.match(page, /\["stale", "backing_off", "unavailable"\]/);
  assert.match(page, /\(tickerRefresh\?\.cacheAgeMs \?\? 0\) > 120_000/);
  assert.match(page, /\{tickerStale \? <Notice>合约行情暂时使用最近快照。<\/Notice> : null\}/);
  assert.doesNotMatch(page, /tickerCached/);
});
