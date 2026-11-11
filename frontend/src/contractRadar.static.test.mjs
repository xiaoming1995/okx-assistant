import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("contract radar page exposes the scan workflow", () => {
  assert.match(source, /function ContractRadarPage/);
  assert.match(source, /\/api\/market\/radar/);
  assert.match(source, /合约雷达/);
  assert.match(source, /开始扫描/);
  assert.match(source, /重新扫描/);
  assert.match(source, /设置条件后开始扫描/);
  assert.doesNotMatch(source, /应用筛选/);
  assert.doesNotMatch(source, /loadRadar\(false\)\.catch/);
});

test("contract radar page exposes filters and states", () => {
  assert.match(source, /settlement/);
  assert.match(source, /minVolume/);
  assert.match(source, /volatility/);
  assert.match(source, /risk/);
  assert.match(source, /没有符合条件的合约/);
  assert.match(source, /AI 大盘分析/);
  assert.match(source, /\/api\/market\/radar\/analysis/);
  assert.match(source, /analysisLoading \|\| analysisError \|\| analysis \? \(/);
  assert.doesNotMatch(source, /等待手动分析。扫描完成。点击“AI 分析”后/);
  assert.doesNotMatch(source, /checked=\{explain\}/);
});

test("contract radar defaults to a clear turnover window and does not surface transport internals", () => {
  assert.match(source, /useState<RadarSortKey>\("turnover_1h"\)/);
  assert.match(source, /sortBy,/);
  assert.match(source, /1小时成交额/);
  assert.match(source, /24小时成交额/);
  assert.match(source, /<SegmentedControl aria-label="候选排行方式" value=\{sortBy\} onChange=\{\(value\) => selectRadarSort\(value as RadarSortKey\)\}/);
  assert.match(source, /disabled=\{loading\}/);
  assert.match(source, /radarTurnoverCompact/);
  assert.match(source, /radarWarningText/);
  assert.match(source, /部分合约 K线暂时无法更新，已使用可用缓存或降级数据；可稍后重新扫描。/);
  assert.match(source, /radarSortGroup/);
  assert.match(source, /radarFeedback/);
  assert.match(source, /radarEvidenceDetails/);
  assert.match(source, /selectRadarSort\(value as RadarSortKey\)/);
  assert.doesNotMatch(source, /void loadRadar\(true, item\.key\)/);
  assert.match(source, /当前雷达快照不支持双口径本地切换，请重新扫描/);
  assert.match(source, /筛选条件已变更，点击重新扫描后生效/);
  assert.match(source, /aria-live="polite"/);
});

test("contract radar uses compact skeletons for the first scan and retains results during refresh", () => {
  assert.match(source, /正在扫描合约 · 正在筛选候选与 K线数据/);
  assert.match(source, /<DataLoadingSkeleton label="正在扫描合约候选" variant="radar-list" \/>/);
  assert.match(source, /<DataLoadingSkeleton label="正在读取候选合约详情" variant="radar-detail" \/>/);
  assert.match(source, /loading && !payload/);
  assert.match(source, /设置条件后开始扫描/);
  assert.match(source, /radarDetailEmpty/);
});

test("contract radar centers its no-scan list and detail guidance", () => {
  assert.match(styles, /\.radarListEmpty\s*\{[\s\S]*?flex:\s*1;[\s\S]*?place-content:\s*center;[\s\S]*?justify-items:\s*center;[\s\S]*?text-align:\s*center;/);
  assert.match(styles, /\.radarList\s*\{[\s\S]*?flex:\s*1;/);
  assert.match(styles, /\.radarDetailEmpty\s*\{[\s\S]*?align-content:\s*center;[\s\S]*?justify-items:\s*center;[\s\S]*?text-align:\s*center;/);
});

test("contract radar filters completed snapshots locally by volatility and turnover", () => {
  assert.match(source, /const \[resultVolatility, setResultVolatility\] = React\.useState\("all"\)/);
  assert.match(source, /const \[resultMinTurnover, setResultMinTurnover\] = React\.useState\(""\)/);
  assert.match(source, /const \[resultFiltersExpanded, setResultFiltersExpanded\] = React\.useState\(false\)/);
  assert.match(source, /const visibleRadarResults = React\.useMemo/);
  assert.match(source, /radarComparableTurnoverValue\(item\)/);
  assert.match(source, /aria-label="本次扫描结果筛选"/);
  assert.match(source, /payload && resultFiltersExpanded/);
  assert.match(source, /aria-expanded=\{resultFiltersExpanded\}/);
  assert.match(source, /aria-controls="radar-result-filters"/);
  assert.match(source, /扫描最小 24h 量/);
  assert.match(source, /已筛选/);
  assert.match(source, /本次扫描结果波动筛选/);
  assert.match(source, /本次扫描结果最小24小时成交额/);
  assert.match(source, /清除结果筛选/);
  assert.match(source, /\$\{visibleRadarResults\.length\}\/\$\{payload\?\.data\.length \?\? 0\} 个/);
  assert.match(source, /本次结果没有符合筛选的合约/);
  assert.match(styles, /\.radarResultFilters\s*\{[\s\S]*?grid-template-columns:[\s\S]*?border-bottom:[\s\S]*?padding:/);
  assert.match(styles, /\.radarResultFilter input,[\s\S]*?height:\s*28px/);
  assert.match(styles, /\.radarPageCompact \.radarResultFilterToggle\s*\{[\s\S]*?height:\s*28px/);
  assert.match(styles, /\.radarListPanel \.panelHeader\s*\{[\s\S]*?grid-template-columns:\s*minmax\(0, 1fr\) auto;[\s\S]*?gap:\s*var\(--space-1\);/);
  assert.match(styles, /\.radarListPanel \.panelHeader > div\s*\{[\s\S]*?grid-row:\s*1;[\s\S]*?white-space:\s*nowrap;/);
  assert.match(styles, /\.radarListPanel \.panelHeader > span\s*\{[\s\S]*?grid-row:\s*2;/);
});

test("contract radar page explains liquidity basis and tradability status", () => {
  assert.match(source, /type RadarLiquidity/);
  assert.match(source, /type RadarEntryAssessment/);
  assert.match(source, /type RadarMarketCondition/);
  assert.match(source, /radarLiquidityBasisLabel/);
  assert.match(source, /radarTradabilityLabel/);
  assert.match(source, /radarEntryLabel/);
  assert.match(source, /可玩/);
  assert.match(source, /仅观察/);
  assert.match(source, /流动性不足/);
  assert.match(source, /入手判断/);
  assert.match(source, /可入手观察/);
  assert.match(source, /等待放量/);
  assert.match(source, /24h 成交额/);
  assert.match(source, /24h 估算成交额/);
  assert.match(source, /可玩优先/);
  assert.match(source, /风险提醒/);
  assert.match(source, /暂未发现明显异常/);
  assert.match(source, /有几项需要注意/);
  assert.match(source, /风险较高，谨慎观察/);
  assert.doesNotMatch(source, /label="结构风险"/);
  assert.doesNotMatch(source, /riskPenalty\}分/);
  assert.match(source, /行情状态/);
  assert.match(source, /radarMarketConditionNote/);
});

test("contract radar shows selected-contract long-short shares and separate taker volumes", () => {
  assert.match(source, /function RadarFlowSnapshot/);
  assert.match(source, /useMarketStats\(selectedResult\?\.instId \?\? "", selectedResult\?\.bar \?\? "15m"\)/);
  assert.match(source, /账户比例/);
  assert.match(source, /多头账户/);
  assert.match(source, /空头账户/);
  assert.match(source, /主动成交量/);
  assert.match(source, /主动买入/);
  assert.match(source, /主动卖出/);
  assert.match(source, /const visibleWarnings = Array\.from\(new Set\(stats\.statsWarnings\)\)\.filter/);
  assert.match(source, /多空人数比\|主动买卖量\|交易统计/);
  assert.match(source, /部分数据待补齐/);
  assert.match(source, /数据暂不可用/);
  assert.match(source, /已显示上次数据/);
  assert.doesNotMatch(source, /warningCount[\s\S]*?部分数据暂不可用/);
  assert.match(source, /账户多空与主动成交是两套独立口径，不等同于开多、开空成交量/);
  assert.match(source, /aria-busy=\{stats\.marketStatsLoading\}/);
  assert.match(styles, /\.radarFlowGrid\s*\{[\s\S]*?grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\)/);
  assert.match(styles, /\.radarFlowLong strong\s*\{[\s\S]*?color:\s*var\(--color-success-strong\)/);
  assert.match(styles, /\.radarFlowShort strong\s*\{[\s\S]*?color:\s*var\(--color-danger-strong\)/);
});

test("contract radar page opens existing workflows with selected contract", () => {
  assert.match(source, /onOpenContract\(selectedResult\.instId, "market"\)/);
  assert.match(source, /onOpenContract\(selectedResult\.instId, "trade"\)/);
  assert.match(source, /onOpenContract\(selectedResult\.instId, "automation"\)/);
  assert.match(source, /initialInstId=\{selectedContract\}/);
});

test("main navigation is grouped into primary sections and secondary tabs", () => {
  assert.match(source, /type PrimarySection = "market" \| "trade" \| "automation" \| "account" \| "settings"/);
  assert.match(source, /<SectionTabs/);
  assert.match(source, /市场/);
  assert.match(source, /交易/);
  assert.match(source, /自动化/);
  assert.match(source, /账户/);
  assert.match(source, /设置/);
  assert.match(source, /行情图表/);
  assert.match(source, /AI 用量/);
});

test("strategy list can open the existing strategy editor", () => {
  assert.match(source, /function StrategyListPage\(\{/);
  assert.match(source, /onEditStrategy: \(strategyId: number\) => void/);
  assert.match(source, /initialEditStrategyId=\{strategyEditId\}/);
  assert.match(source, /onClick=\{\(\) => onEditStrategy\(strategy\.id\)\}/);
  assert.match(source, /<Pencil size=\{13\} \/>/);
  assert.match(source, /编辑/);
});

test("app route is synchronized with the URL hash", () => {
  assert.match(source, /type AppRouteState/);
  assert.match(source, /readAppRouteFromHash/);
  assert.match(source, /buildAppHash/);
  assert.match(source, /window\.location\.hash/);
  assert.match(source, /window\.history\.pushState/);
  assert.match(source, /window\.history\.replaceState/);
  assert.match(source, /hashchange/);
  assert.match(source, /popstate/);
  assert.match(source, /\/automation\/strategies/);
  assert.match(source, /\/automation\/signals\/\$\{route\.signalDetailId\}/);
  assert.match(source, /\/settings\/\$\{route\.settingsTab\}/);
});

test("automation strategies expose take-profit and stop-loss settings", () => {
  assert.match(source, /takeProfitPct/);
  assert.match(source, /stopLossPct/);
  assert.match(source, /止盈%/);
  assert.match(source, /止损%/);
  assert.match(source, /take_profit_pct/);
  assert.match(source, /stop_loss_pct/);
  assert.match(source, /automationActionLabel\(action\?: string\)/);
  assert.match(source, /take_profit/);
  assert.match(source, /stop_loss/);
});

test("automation strategy editor clarifies save and start state", () => {
  assert.match(source, /saveNotice/);
  assert.match(source, /保存并启动/);
  assert.match(source, /保存为暂停/);
  assert.match(source, /策略已保存，但仍处于暂停状态/);
  assert.match(source, /策略已保存并启动/);
  assert.match(source, /止盈止损只会随策略保存，不会自动平仓/);
  assert.match(source, /\/toggle/);
});

test("automation overview keeps decision and metrics in one compact block", () => {
  assert.match(source, /cleanInlineMetrics/);
  assert.match(source, /cleanInlineMetric/);
  assert.match(source, /signals\.slice\(0, 4\)/);
  assert.match(source, /当前结论/);
  assert.match(source, /自动交易关键指标/);
  assert.match(source, /\/api\/automation\/pause/);
  assert.match(source, /\/api\/automation\/resume/);
  assert.match(source, /\/api\/automation\/alerts/);
  assert.match(source, /最近告警/);
  assert.match(source, /风控快照/);
  assert.match(source, /执行步骤/);
  assert.match(source, /归档/);
  assert.match(source, /<section className="cleanAutomationGrid">\s*<div className="cleanAutomationColumn">[\s\S]*?title="启用检查"[\s\S]*?title="最近告警"[\s\S]*?<\/div>\s*<section className="cleanPanel">[\s\S]*?title="最近动作"/);
  assert.match(styles, /\.cleanAutomationColumn \{[\s\S]*?gap: var\(--space-4\);/);
  assert.doesNotMatch(styles, /\.automationAlertPanel \{\s*margin-top:/);
});
