import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("direct AI and trading-data entry default to USDT settled browsing", () => {
  assert.match(source, /initialFilter=\{marketWorkbenchInitialFilter \?\? \(marketTab === "chart" \? "watch" : "usdt"\)\}/);
  assert.match(source, /{ key: "usdt", label: "USDT本位" }/);
  assert.match(source, /{ key: "all", label: "全部" }/);
});

test("market instrument search filters the loaded list locally", () => {
  assert.match(source, /function useMarketInstrumentRows/);
  assert.match(source, /const filteredInstruments = React\.useMemo\(\(\) => \{/);
  assert.match(source, /const keyword = query\.trim\(\)\.toUpperCase\(\);/);
  assert.match(source, /instrumentMatchesKeyword\(item, keyword\)/);
  assert.match(source, /displaySymbol\.includes\(keyword\)/);
  assert.match(source, /assetName\.includes\(keyword\)/);
  assert.match(source, /fetch\(`\$\{API_BASE\}\/api\/instruments\?limit=500`\)/);
  assert.doesNotMatch(source, /query=\$\{encodeURIComponent\(query\)\}/);
});

test("market instrument list uses app style contract identity without a redundant legend", () => {
  assert.match(source, /const tokenDisplayNames: Record<string, string> = \{/);
  assert.match(source, /BTC: "Bitcoin"/);
  assert.match(source, /function instrumentDisplaySymbol/);
  assert.match(source, /function instrumentAssetName/);
  assert.match(source, /function instrumentContractTypeLabel/);
  assert.match(source, /function instrumentAvatarText/);
  assert.match(source, /function instrumentSettlementLabel/);
  assert.match(source, /function instrumentSummaryLabel/);
  assert.match(source, /instrumentDisplaySymbol\(item\.inst_id\)/);
  assert.match(source, /instrumentContractTypeLabel\(item, item\.inst_id\)/);
  assert.match(source, /instrumentAssetName\(item, item\.inst_id\)/);
  assert.match(source, /instrumentSettlementLabel\(item, item\.inst_id\)/);
  assert.match(source, /instrumentActivityLabel\(itemTicker, item\.inst_id\)/);
  assert.doesNotMatch(source, /className="listLegend"/);
  assert.match(source, /instrumentSummaryLabel\(item, item\.inst_id\)/);
  assert.doesNotMatch(source, /instrumentSettlementLabel\(item, item\.inst_id\)\} \· 面值/);
});

test("market instrument rail keeps concise local-followed controls and shared relevance sorting", () => {
  assert.match(source, /function compareInstrumentRelevance/);
  assert.match(source, /function MarketInstrumentRail/);
  assert.match(source, /sortMode: InstrumentSort/);
  assert.match(source, /compareInstrumentRelevance\(left, right, \{ selectedInstId: selected, sortMode, tickers \}\)/);
  assert.match(source, /compareInstrumentRelevance\(left, right, \{\s*selectedInstId: instId,\s*sortMode: "default",\s*tickers\s*\}\)/s);
  assert.match(source, /\{ key: "watch", label: "已关注" \}/);
  assert.match(source, /const primaryInstrumentFilters = instrumentFilters\.filter\(\(item\) => item\.key === "watch" \|\| item\.key === "all"\);/);
  assert.match(source, /const advancedInstrumentFilters = instrumentFilters\.filter\(\(item\) => item\.key !== "watch" && item\.key !== "all"\);/);
  assert.match(source, /meta=\{\`已关注 \$\{watchedCount\} · 全部 \$\{totalCount\}\`\}/);
  assert.match(source, /className="instrumentQuickControls"/);
  assert.match(source, /aria-label="更多合约范围"/);
  assert.match(source, /aria-label="合约排序方式"/);
  assert.match(source, /<Menu withinPortal position="bottom-start">/);
  assert.match(source, /<Menu\.Dropdown aria-label="更多合约范围">/);
  assert.match(source, /<Menu\.Dropdown aria-label="合约排序方式">/);
  assert.match(source, /rightSection=\{filter === item\.key \? <Check size=\{14\} \/> : null\}/);
  assert.match(source, /<UnstyledButton\s+type="button"\s+className="instrumentMain"/);
  assert.match(source, /<ActionIcon\s+type="button"\s+className="watchButton"/);
  assert.match(source, /<ScrollArea className="instrumentList" type="auto" scrollbarSize=\{8\}>/);
  assert.match(source, /watchedCount=\{instruments\.filter\(\(item\) => Boolean\(item\.watched\)\)\.length\}/);
  assert.match(source, /totalCount=\{instruments\.length\}/);
  assert.match(styles, /\.instrumentQuickControls\s*\{/);
  assert.match(styles, /\.instrumentQuickControls\s*\{\s*display: grid;\s*grid-template-columns: minmax\(0, 1fr\);/s);
  assert.match(styles, /\.instrumentControlMenus\s*\{\s*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/s);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.instrumentQuickControls\s*\{[\s\S]*?grid-template-columns: 1fr;/);
});

test("market workbench mounts one rail and keeps its state while chart, AI, and data views change", () => {
  assert.match(source, /function MarketContractWorkspace\(/);
  assert.equal((source.match(/<MarketInstrumentRail/g) ?? []).length, 1);
  assert.match(source, /const \[query, setQuery\] = React\.useState\(""\);/);
  assert.match(source, /const \[filter, setFilter\] = React\.useState<InstrumentFilter>\(initialFilter\);/);
  assert.match(source, /const \[sortMode, setSortMode\] = React\.useState<InstrumentSort>\("default"\);/);
  assert.match(source, /<MarketContractWorkspace[\s\S]*?selected=\{selectedContract\}[\s\S]*?onSelectContract=\{setSelectedContract\}/);
  assert.match(source, /marketTab === "chart" \|\| marketTab === "aiOutlook" \|\| marketTab === "stats"/);
  assert.match(source, /topics: \["market\.ticker"\]/);
});

test("market workbench can collapse its desktop rail without replacing shared rail state", () => {
  const workspaceStart = source.indexOf("function MarketContractWorkspace(");
  const chartStart = source.indexOf("function MarketPage(");
  const workspaceSource = source.slice(workspaceStart, chartStart);

  assert.match(source, /ChevronLeft/);
  assert.match(source, /ChevronRight/);
  assert.match(source, /className=\{`marketRail \$\{collapsed \? "collapsed" : ""\}`\}/);
  assert.match(source, /label="展开合约列表"/);
  assert.match(source, /label="收起合约列表"/);
  assert.match(workspaceSource, /const \[railCollapsed, setRailCollapsed\] = React\.useState\(false\);/);
  assert.match(workspaceSource, /className=\{`marketLayout marketContractWorkspace \$\{railCollapsed \? "marketRailCollapsed" : ""\}`\}/);
  assert.match(workspaceSource, /collapsed=\{railCollapsed\}/);
  assert.match(workspaceSource, /onToggleCollapsed=\{\(\) => setRailCollapsed\(\(current\) => !current\)\}/);
  assert.match(styles, /\.marketLayout\.marketRailCollapsed\s*\{\s*grid-template-columns: 48px minmax\(0, 1fr\);/s);
  assert.match(styles, /\.marketRail\.collapsed \.marketRailExpandedContent\s*\{\s*display: none;/s);
  assert.match(styles, /@media \(max-width: 1200px\)[\s\S]*?\.marketLayout\.marketRailCollapsed\s*\{\s*grid-template-columns: 1fr;/);
  assert.match(styles, /@media \(max-width: 1200px\)[\s\S]*?\.marketRail\.collapsed \.marketRailExpandedContent\s*\{\s*display: flex;/);
});

test("market workbench is the only contract-list and ticker snapshot source for its right-side views", () => {
  const workspaceStart = source.indexOf("function MarketContractWorkspace(");
  const chartStart = source.indexOf("function MarketPage(");
  const aiStart = source.indexOf("function MarketAiOutlookPage(");
  const statsStart = source.indexOf("function MarketStatsPage(");
  const tradeStart = source.indexOf("function TradingPage(");
  const workspaceSource = source.slice(workspaceStart, chartStart);
  const chartSource = source.slice(chartStart, aiStart);
  const aiSource = source.slice(aiStart, statsStart);
  const statsSource = source.slice(statsStart, tradeStart);

  assert.match(source, /const MarketContractWorkspaceContext = React\.createContext<MarketContractWorkspaceSnapshot \| null>\(null\);/);
  assert.match(source, /function useMarketContractWorkspace\(\)/);
  assert.match(workspaceSource, /const \[tickerUpdatedAt, setTickerUpdatedAt\] = React\.useState<number \| null>\(null\);/);
  assert.match(workspaceSource, /const tickerRealtime = useRealtimeFeed\(\{/);
  assert.match(workspaceSource, /topics: \["market\.ticker"\]/);
  assert.match(workspaceSource, /const chartRealtime = useRealtimeFeed\(\{/);
  assert.match(workspaceSource, /topics: \["market\.candles"\]/);
  assert.match(workspaceSource, /chartSnapshot/);
  assert.match(workspaceSource, /<MarketContractWorkspaceContext\.Provider value=\{snapshot\}>/);
  assert.match(chartSource, /useMarketContractWorkspace\(\)/);
  assert.match(chartSource, /chartCandles: candles/);
  assert.doesNotMatch(chartSource, /topics: \["market\.candles"\]/);
  assert.doesNotMatch(chartSource, /topics: \["market\.ticker"\]/);
  assert.match(aiSource, /useMarketContractWorkspace\(\)/);
  assert.match(statsSource, /useMarketContractWorkspace\(\)/);
  assert.doesNotMatch(aiSource, /useRealtimeFeed\(\{/);
  assert.doesNotMatch(statsSource, /useRealtimeFeed\(\{/);
  for (const pageSource of [chartSource, aiSource, statsSource]) {
    assert.doesNotMatch(pageSource, /const \[query, setQuery\]/);
    assert.doesNotMatch(pageSource, /const \[filter, setFilter\]/);
    assert.doesNotMatch(pageSource, /const \[sortMode, setSortMode\]/);
    assert.doesNotMatch(pageSource, /const \[instruments, setInstruments\]/);
    assert.doesNotMatch(pageSource, /const \[tickers, setTickers\]/);
  }
});

test("radar can carry a candidate into each market workbench view", () => {
  assert.match(source, /type RadarActionTarget = "market" \| "aiOutlook" \| "stats" \| "trade" \| "automation";/);
  assert.match(source, /const \[marketWorkbenchInitialFilter, setMarketWorkbenchInitialFilter\] = React\.useState<InstrumentFilter \| null>\(null\);/);
  assert.match(source, /target === "market"[\s\S]*?setMarketWorkbenchInitialFilter\("all"\)[\s\S]*?setMarketTab\("chart"\)/);
  assert.match(source, /target === "aiOutlook"[\s\S]*?setMarketWorkbenchInitialFilter\("all"\)[\s\S]*?setMarketTab\("aiOutlook"\)/);
  assert.match(source, /target === "stats"[\s\S]*?setMarketWorkbenchInitialFilter\("all"\)[\s\S]*?setMarketTab\("stats"\)/);
  assert.match(source, /setMarketWorkbenchInitialFilter\(null\);\s*setMarketTab\("aiOutlook"\)/);
  assert.match(source, /onOpenContract\(selectedResult\.instId, "aiOutlook"\)/);
  assert.match(source, /onOpenContract\(selectedResult\.instId, "stats"\)/);
});

test("market-facing daily changes use the UTC+8 day-open baseline consistently", () => {
  assert.match(source, /function tickerTodayChange\(ticker: Ticker \| null \| undefined\) \{\s*return tickerChangeFromBases\(ticker, \["sodUtc8"\]\);\s*\}/s);
  assert.match(source, /function tickerChangeFromBases\(ticker: Ticker \| null \| undefined, baseKeys: string\[\]\)/);
  assert.match(source, /\.find\(\(value\): value is number => value !== null && value !== 0\)/);
  assert.match(source, /const leftChange = tickerTodayChange\(leftTicker\)\.percent \?\? -Infinity;/);
  assert.match(source, /const itemChange = tickerTodayChange\(itemTicker\);/);
  assert.match(source, /const dayChange = tickerTodayChange\(selectedTicker\);/);
  assert.match(source, /今日涨跌（按 UTC\+8 日开盘价计算）/);
  assert.doesNotMatch(source, /function tickerChange\(/);
});

test("a rolling 24-hour calculation remains separate from the market daily calculation", () => {
  assert.match(source, /function tickerRolling24hChange\(ticker: Ticker \| null \| undefined\) \{\s*return tickerChangeFromBases\(ticker, \["open24h"\]\);\s*\}/s);
});

test("market percentage values are limited to two decimal places", () => {
  assert.match(source, /function formatSignedPercent\(value: number \| null\) \{\s*return formatSigned\(value, "%", 2\);\s*\}/s);
  assert.match(source, /formatSignedPercent\(itemChange\.percent\)/);
  assert.match(source, /formatSignedPercent\(dayChange\.percent\)/);
  assert.match(source, /formatSignedPercent\(detailCandlePercent\)/);
});
