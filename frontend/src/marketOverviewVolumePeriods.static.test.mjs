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

const volumeHelpers = () => {
  const snippet = source.slice(
    source.indexOf("const VOLUME_PERIOD_CONFIG"),
    source.indexOf("function MarketOverviewPage(")
  );
  return transformSync(snippet, { loader: "ts" }).code;
};

const aggregateVolumePeriod = runInNewContext(
  `${volumeHelpers()}; aggregateVolumePeriod`,
  { toNumber }
);

// 40 个交易日，每日 1 亿 USD；最后一天未收盘（confirm=0）。
function daily(days, { base = 100_000_000, partial = true } = {}) {
  return Array.from({ length: days }, (_, index) => {
    const day = new Date(Date.UTC(2026, 9, 1 + index));
    return {
      date: day.toISOString().slice(0, 10),
      ts: day.getTime(),
      volUsd: String(base),
      count: 40,
      confirm: partial && index === days - 1 ? "0" : "1"
    };
  });
}

test("period config uses real trading-day windows, never 24h multiplication", () => {
  assert.match(source, /const VOLUME_PERIOD_CONFIG: Record<VolumePeriod/);
  assert.match(source, /day: \{ label: "日", days: 1,/);
  assert.match(source, /week: \{ label: "周", days: 7,/);
  assert.match(source, /month: \{ label: "月", days: 30,/);
  assert.match(source, /year: \{ label: "年", days: 365,/);
  assert.match(source, /绝不能用 24h × 天数推算/);
  assert.doesNotMatch(source, /volUsd[^;]*\*\s*(7|30|365)/);
  assert.match(page, /aggregateVolumePeriod\(volumeHistory\?\.data\?\.daily, volumePeriod\)/);
  assert.match(page, /api\/market\/overview\/volume-history/);
  assert.match(page, /data=\{\[\{ value: "day", label: "日" \}/);
});

test("the unfinished daily candle is excluded so an intraday figure never fakes a crash", () => {
  const rows = daily(80);
  rows[rows.length - 1].volUsd = "1000000"; // 今日才过几分钟
  const day = aggregateVolumePeriod(rows, "day");
  assert.equal(day.current, 100_000_000); // 取最近一个已收盘交易日
  assert.equal(day.changePct, 0); // 与上一个完整日比较，不是 -99%
  assert.equal(day.endDate, rows[rows.length - 2].date);
  assert.equal(day.unfinishedToday?.date, rows[rows.length - 1].date);
  assert.equal(day.unfinishedToday?.value, 1000000);
  assert.match(page, /今日至今 \{formatCompact\(volumeStats\.unfinishedToday\.value\)\} USD/);
  assert.match(page, /未收盘，未计入上述周期与环比/);
});

test("every period sums real daily candles and compares with the previous equal window", () => {
  const rows = daily(80, { partial: false });
  const day = aggregateVolumePeriod(rows, "day");
  assert.equal(day.current, 100_000_000);
  assert.equal(day.coveredDays, 1);
  assert.equal(day.complete, true);
  assert.equal(day.hasPrevious, true);
  assert.equal(day.changePct, 0);
  assert.equal(day.unfinishedToday, null);
  assert.equal(day.trend.length, 14);

  const week = aggregateVolumePeriod(rows, "week");
  assert.equal(week.current, 700_000_000);
  assert.equal(week.coveredDays, 7);
  assert.equal(week.complete, true);
  assert.equal(week.trend.length, 12);

  const month = aggregateVolumePeriod(rows, "month");
  assert.equal(month.current, 3_000_000_000);
  assert.equal(month.coveredDays, 30);
  assert.equal(month.complete, true);
  assert.equal(month.trend.length, 3);

  const year = aggregateVolumePeriod(rows, "year");
  assert.equal(year.current, 8_000_000_000);
  assert.equal(year.coveredDays, 80);
  assert.equal(year.complete, false);
  assert.equal(year.hasPrevious, false);
  assert.equal(year.changePct, null);
});

test("a growing series produces a positive period-over-period change", () => {
  const rows = daily(14, { partial: false }).map((row, index) => ({ ...row, volUsd: String(100 + (index >= 7 ? 50 : 0)) }));
  const week = aggregateVolumePeriod(rows, "week");
  assert.equal(week.current, 1050);
  assert.equal(week.previous, 700);
  assert.ok(Math.abs(week.changePct - 50) < 1e-9);
});

test("incomplete periods are flagged instead of being extrapolated", () => {
  assert.match(page, /所选周期的历史日线不足，当前数值为已覆盖交易日的真实累计，未做任何外推补齐。/);
  assert.match(page, /!volumeStats\.complete/);
  assert.match(page, /数据仅覆盖 \$\{volumeStats\.coveredDays\}\/\$\{volumeStats\.days\} 天/);
  const empty = aggregateVolumePeriod([], "week");
  assert.equal(empty.current, null);
  assert.equal(empty.complete, false);
  assert.equal(empty.trend.length, 0);
  const nullish = aggregateVolumePeriod(null, "year");
  assert.equal(nullish.current, null);
  assert.equal(nullish.hasPrevious, false);
});

test("invalid rows are skipped and the two scopes are explicitly labelled as different", () => {
  const rows = [
    { date: "2026-10-01", ts: 1, volUsd: "invalid", count: 40, confirm: "1" },
    { date: "2026-10-02", ts: 2, volUsd: "-5", count: 40, confirm: "1" },
    { date: "2026-10-03", ts: 3, volUsd: "10", count: 40, confirm: "1" },
    { date: "2026-10-04", ts: 4, volUsd: "20", count: 40, confirm: "1" }
  ];
  const day = aggregateVolumePeriod(rows, "day");
  assert.equal(day.current, 20);
  assert.equal(day.totalDays, 2);
  assert.match(page, /官方 24h 全平台成交额/);
  assert.match(page, /不含现货与期权，与官方全平台 24h 总额不同/);
  assert.match(page, /OKX 1D 日线成交额（volumeQuote）累加/);
  assert.match(page, /覆盖约 \$\{volumeHistory\.data\.coveragePct\}% 合约成交额/);
});

test("trend bars and responsive layout have styles", () => {
  for (const selector of [
    ".marketOverviewVolumeTrend {",
    ".marketOverviewVolumeMeta {",
    ".marketOverviewVolumeHeader {",
    ".marketOverviewTrendCaption {"
  ]) {
    assert.ok(styles.includes(selector), `missing ${selector}`);
  }
  assert.match(styles, /\.marketOverviewVolumeTrend span:last-child \{/);
});

test("the previous window is highlighted on the trend and labelled with its real date range", () => {
  const volumeDays = { day: 1, week: 7, month: 30, year: 365 };
  const rows = daily(80, { partial: false });
  for (const [period, expectedBars] of Object.entries({ day: 1, week: 1, month: 1, year: 0 })) {
    const stats = aggregateVolumePeriod(rows, period);
    const flagged = stats.trend.filter((point) => point.isPrevious);
    assert.equal(flagged.length, expectedBars, `${period}: highlighted bars`);
    if (expectedBars) {
      const n = volumeDays[period];
      assert.equal(stats.hasPrevious, true);
      assert.equal(flagged[0].startDate, rows[rows.length - 2 * n].date);
      assert.equal(flagged[0].endDate, rows[rows.length - n - 1].date);
      assert.notEqual(stats.previousRange, stats.currentRange);
      assert.ok(stats.previousRange.length > 0 && stats.currentRange.length > 0);
    } else {
      assert.equal(stats.hasPrevious, false);
      assert.equal(stats.previousRange, "");
    }
  }
  assert.match(aggregateVolumePeriod(rows, "day").previousRange, /^\d{2}\/\d{2}$/);
  assert.match(aggregateVolumePeriod(rows, "week").previousRange, /^\d{2}\/\d{2}–\d{2}\/\d{2}$/);
  assert.match(page, /较上一周期（\{volumeStats\.previousRange\}）/);
  assert.match(page, /className=\{point\.isPrevious \? "marketOverviewVolumeTrendPrevious" : undefined\}/);
  assert.match(page, /className="marketOverviewVolumeLegend"/);
  assert.match(page, /上一周期 \{volumeStats\.previousRange\}/);
  assert.match(page, /volumeStats\.hasPrevious \?/);
  assert.match(styles, /\.marketOverviewVolumeTrend span\.marketOverviewVolumeTrendPrevious \{/);
  assert.match(styles, /\.marketOverviewLegendPrevious \{/);
  assert.match(styles, /\.marketOverviewLegendCurrent \{/);
});

test("a window that spans a calendar year keeps both years in its label", () => {
  const rows = daily(400, { partial: false });
  const year = aggregateVolumePeriod(rows, "year");
  assert.equal(year.hasPrevious, false);
  assert.match(year.currentRange, /^\d{4}\/\d{2}\/\d{2}–\d{4}\/\d{2}\/\d{2}$/);
  const years = [...year.currentRange.matchAll(/\d{4}/g)].map((match) => match[0]);
  assert.equal(years.length, 2);
  assert.notEqual(years[0], years[1]);
  assert.match(source, /跨年窗口必须带年份/);
});
