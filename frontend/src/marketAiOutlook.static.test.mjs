import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("market AI outlook chart page only opens the dedicated report page", () => {
  const marketPageStart = source.indexOf("function MarketPage(");
  const aiPageStart = source.indexOf("function MarketAiOutlookPage(");
  assert.ok(marketPageStart > -1);
  assert.ok(aiPageStart > marketPageStart);
  const marketPageSource = source.slice(marketPageStart, aiPageStart);

  assert.match(marketPageSource, /AI看行情/);
  assert.match(marketPageSource, /onClick=\{\(\) => onOpenAiOutlook\?\.\(selected, bar\)\}/);
  assert.doesNotMatch(marketPageSource, /fetch\(`\$\{API_BASE\}\/api\/market\/ai-outlook`/);
  assert.doesNotMatch(marketPageSource, /MarketAiOutlookPanel/);
  assert.doesNotMatch(marketPageSource, /loadAiOutlook\(\)\.catch/);
  assert.doesNotMatch(marketPageSource, /loadAiOutlook\(\{ forceMacro: true \}\)\.catch/);
});

test("market AI outlook route is a first-class market page", () => {
  assert.match(source, /type MarketTab = "radar" \| "chart" \| "aiOutlook" \| "aiRecords" \| "stats" \| "announcements"/);
  assert.match(source, /parts\[1\] === "ai-outlook"[\s\S]*?\? "aiOutlook"/);
  assert.match(source, /route\.marketTab === "aiOutlook"[\s\S]*?params\.set\("inst", route\.selectedContract\)/);
  assert.match(source, /params\.set\("bar", normalizeRouteBar\(route\.selectedBar\)\)/);
  assert.match(source, /route\.marketTab === "aiOutlook" \? "\/market\/ai-outlook"/);
  assert.match(source, /label: "AI看行情"[\s\S]*?active: marketTab === "aiOutlook"/);
  assert.match(source, /<MarketContractWorkspace[\s\S]*?selected=\{selectedContract\}/);
  assert.match(source, /<MarketAiOutlookPage[\s\S]*?initialBar=\{selectedBar\}/);
  assert.match(source, /function MarketAiOutlookPage[\s\S]*?useMarketContractWorkspace\(\)/);
});

test("dedicated market AI outlook sends the active chart snapshot only on request", () => {
  const aiPageStart = source.indexOf("function MarketAiOutlookPage(");
  const statsPageStart = source.indexOf("function MarketStatsPage(");
  assert.ok(aiPageStart > -1);
  assert.ok(statsPageStart > aiPageStart);
  const aiPageSource = source.slice(aiPageStart, statsPageStart);

  assert.match(aiPageSource, /body: JSON\.stringify\(\{[\s\S]*?instId: selected,[\s\S]*?bar,[\s\S]*?limit: 120,[\s\S]*?snapshotId,[\s\S]*?forceAnalysis: Boolean\(options\?\.forceAnalysis\),[\s\S]*?forceMacro: Boolean\(options\?\.forceMacro\)[\s\S]*?\}\)/);
  assert.match(aiPageSource, /当前图表快照仍在加载/);
  assert.match(aiPageSource, /if \(!chartSnapshotFreshForAnalysis\(activeSnapshot\)\) \{\s*activeSnapshot = await refreshChartSnapshot\(true\);/);
  assert.match(aiPageSource, /if \(payload\.snapshotRequired\) \{\s*activeSnapshot = await refreshChartSnapshot\(true\);/);
  assert.match(source, /function chartSnapshotFreshForAnalysis\([\s\S]*?snapshot\.complete[\s\S]*?duration \* 3/);
  assert.match(aiPageSource, /onRefresh=\{\(\) => loadAiOutlook\(\{ forceAnalysis: Boolean\(aiOutlook\) \}\)\}/);
  assert.match(aiPageSource, /setAiOutlook\(null\);/);
  assert.match(aiPageSource, /setAiOutlookError\(""\);/);
  assert.doesNotMatch(aiPageSource, /loadAiOutlook\(\)\.catch/);
});

test("market AI outlook panel is a read-only chart report with conditional forecasts", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(panelSource, /仅供行情阅读参考 · 不会下单 · 不会影响自动交易/);
  assert.match(panelSource, /主图结构概览/);
  assert.match(panelSource, /数据状态/);
  assert.match(panelSource, /图表依据/);
  assert.match(panelSource, /后续观察/);
  assert.match(panelSource, /图表已有新数据/);
  assert.match(panelSource, /数据来源/);
  assert.match(panelSource, /补充数据与来源/);
  assert.match(panelSource, /条件推演/);
  assert.match(panelSource, /不是确定价格预测/);
  assert.match(panelSource, /className=\{`marketAiForecastGrid count-\$\{forecasts\.length\}`\}/);
  assert.match(panelSource, /marketAiForecastCardHeader/);
  assert.match(panelSource, /置信度 \{forecast\.confidence\}%/);
  assert.match(panelSource, /<em><span>重读<\/span>/);
  assert.match(panelSource, /marketAiForecasts\(outlook\)/);
});

test("market AI outlook presents optional public read-only profile provenance without a new action", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(source, /analysisProfile\?: \{/);
  assert.match(source, /profileVersion\?: number/);
  assert.match(panelSource, /const analysisProfile = outlook\?\.analysisProfile\?\.status === "active"/);
  assert.match(panelSource, /行情读取规则：公开行情只读/);
  assert.match(panelSource, /marketAiProfileProvenance/);
  assert.match(styles, /\.marketAiProfileProvenance\s*\{[\s\S]*?color: #66798e;/);
  assert.doesNotMatch(panelSource, /okx-cli|执行命令|创建订单/);
});

test("market AI outlook renders report-scoped decision and trading structure evidence", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(panelSource, /const decision = outlook\?\.decision;/);
  assert.match(panelSource, /const tradingStructure = outlook\?\.tradingStructure;/);
  assert.match(panelSource, /aria-label="决策参考"/);
  assert.match(panelSource, /marketAiDirectionLayerLabel\(decision\)/);
  assert.match(panelSource, /marketAiDecisionAssessmentLabel\(decision\.assessment\)/);
  assert.match(panelSource, /marketAiDataQualityLabel\(decision\.dataQuality\)/);
  assert.match(panelSource, /const confidenceExplanation = marketAiConfidenceExplanation\(outlook\)/);
  assert.match(panelSource, /const evidenceGaps = marketAiEvidenceGaps\(outlook\)/);
  assert.match(panelSource, /const periodProvenance = marketAiPeriodProvenance\(outlook\)/);
  assert.match(panelSource, /aria-label="证据充分度依据"/);
  assert.match(panelSource, /为什么是 \{confidenceExplanation\.referenceValue/);
  assert.match(panelSource, /不是涨跌概率/);
  assert.match(panelSource, /图表方向/);
  assert.match(panelSource, /方向确认/);
  assert.match(panelSource, /交易数据/);
  assert.match(panelSource, /aria-label="图表与交易结构周期"/);
  assert.match(panelSource, /aria-label="证据缺口"/);
  assert.match(panelSource, /确认门槛/);
  assert.match(panelSource, /当前缺口/);
  assert.match(panelSource, /marketAiConfidenceEvidenceValue\(item\)/);
  assert.match(panelSource, /关注条件/);
  assert.match(panelSource, /重评条件/);
  assert.match(panelSource, /交易结构依据/);
  assert.match(panelSource, /OKX 合约统计/);
  assert.match(panelSource, /marketAiStructureValue\(item\)/);
  assert.match(panelSource, /marketAiStructureStateLabel\(item\)/);
  assert.match(panelSource, /marketAiDirectionLayerExplanation\(decision\)/);
  assert.match(panelSource, /marketAiStructureLabel\(item\)/);
  assert.match(panelSource, /marketAiStructureExplanation\(item\)/);
  assert.match(panelSource, /const observationLevels = outlook\?\.observationLevels;/);
  assert.match(panelSource, /const confirmationLevels = marketAiConfirmationLevels\(observationLevels\);/);
  assert.match(panelSource, /aria-label="条件确认价"/);
  assert.match(panelSource, /confirmationLevels\.currentState\.label/);
  assert.match(panelSource, /candidate\.confirmationPrice/);
  assert.match(panelSource, /candidate\.priceMeaning/);
  assert.match(panelSource, /candidate\.requirements\?\.map/);
  assert.match(panelSource, /candidate\.missingEvidence\?\.length/);
  assert.match(panelSource, /本侧仍缺/);
  assert.match(panelSource, /candidate\.statusLabel/);
  assert.match(panelSource, /candidate\.invalidation/);
  assert.match(panelSource, /失效条件/);
  assert.match(panelSource, /手动刷新后重算确认价/);
  assert.match(panelSource, /仅供行情阅读参考 · 不会下单 · 不会影响自动交易/);
  assert.match(source, /function marketAiActionLabel[\s\S]*?wait_release"\) return "暂不形成方向"/);
  assert.match(source, /function marketAiActionExplanation[\s\S]*?当前仅观察，不作为买卖信号/);
  assert.match(source, /function marketAiDirectionLayerLabel[\s\S]*?短线略偏多 · 待确认/);
  assert.match(source, /function marketAiEvidenceGaps[\s\S]*?旧报告未附与门槛的差距/);
  assert.match(source, /function marketAiPeriodProvenance[\s\S]*?交易结构统计/);
  assert.match(source, /function marketAiStructureLabel[\s\S]*?市场总持仓增减/);
  assert.match(source, /function marketAiStructureStateLabel[\s\S]*?暂未获取 · 不参与本次判断/);
  assert.match(source, /function marketAiStructureExplanation[\s\S]*?不是 0，也不代表没有市场持仓/);
  assert.match(source, /function marketAiConfidenceExplanation[\s\S]*?不代表价格涨跌概率或收益结果/);
  assert.match(source, /function marketAiDataQualityLabel[\s\S]*?交易数据已获取/);
  assert.match(source, /confidenceExplanation\?: \{/);
  assert.match(source, /directionLayer\?: "confirmed" \| "weak_bias" \| "conflict" \| "neutral"/);
  assert.match(source, /evidenceGaps\?: Array<\{/);
  assert.match(source, /structureFallback\?: boolean/);
  assert.match(source, /observationLevels\?: \{/);
  assert.match(source, /candidates\?: Array<\{/);
  assert.match(source, /confirmationPrice\?: string/);
  const confirmationLevelSource = source.slice(source.indexOf("function marketAiConfirmationLevels"), source.indexOf("function marketAiOverallView"));
  assert.match(confirmationLevelSource, /当前：保持观望/);
  assert.match(confirmationLevelSource, /偏多候选/);
  assert.match(confirmationLevelSource, /偏空候选/);
  assert.match(confirmationLevelSource, /不是直接成交价/);
  assert.match(confirmationLevelSource, /恢复观望/);
  assert.match(source, /partialConfirmation\?: boolean/);
});

test("market AI outlook puts a deterministic scenario board before evidence details", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(source, /scenarioBoard\?: \{/);
  assert.match(source, /evidenceScore\?: number/);
  assert.match(source, /function marketAiScenarioBoard/);
  assert.match(panelSource, /const scenarioBoard = marketAiScenarioBoard\(outlook, confirmationLevels\);/);
  assert.match(panelSource, /const scenarioEvidenceScore = scenarioBoard\?\.evidenceScore/);
  assert.match(panelSource, /aria-label="场景化决策看板"/);
  assert.match(panelSource, /当前市场状态/);
  assert.match(panelSource, /场景证据度/);
  assert.match(panelSource, /完整确认暂受限/);
  assert.match(panelSource, /scenarioBoard\.candidates\?\.slice\(0, 2\)\.map/);
  assert.match(panelSource, /candidate\.confirmationPrice/);
  assert.match(panelSource, /条件仅用于阅读当前行情快照/);
  assert.match(panelSource, /<Disclosure className="marketAiEvidenceDetails"/);
  assert.match(panelSource, /查看证据详情、AI 文字解读与数据来源/);
  assert.doesNotMatch(panelSource.slice(0, panelSource.indexOf('aria-label="场景化决策看板"')), /证据充分度 \{marketAiConfidence\(outlook\)\}%/);
  assert.match(styles, /\.marketAiScenarioBoard\s*\{/);
  assert.match(styles, /\.marketAiScenarioCandidateGrid\s*\{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\)/);
  assert.match(styles, /\.marketAiEvidenceDetails > \.disclosureTrigger\s*\{/);
});

test("market AI outlook puts one direction-first outcome ahead of bilateral scenarios", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(source, /directionSummary\?: \{/);
  assert.match(source, /headline\?: "偏多观察" \| "偏空观察" \| "短线偏多（未确认）"/);
  assert.match(source, /function marketAiDirectionSummary/);
  assert.match(panelSource, /const directionSummary = marketAiDirectionSummary\(outlook, scenarioBoard\);/);
  assert.match(panelSource, /aria-label="主图周期方向读取"/);
  assert.match(panelSource, /主图方向/);
  assert.match(panelSource, /directionSummary\?\.confirmationPrice/);
  assert.match(panelSource, /directionSummary\?\.nextCondition/);
  assert.match(panelSource, /directionSummary\?\.readOnly/);
  assert.match(panelSource, /<Disclosure className="marketAiScenarioDetails"/);
  assert.match(panelSource, /查看双向条件与场景依据/);
  assert.match(styles, /\.marketAiDirectionSummary\s*\{/);
  assert.match(styles, /\.marketAiScenarioDetails > \.disclosureTrigger\s*\{/);
  assert.doesNotMatch(panelSource, /开多|开空|立即下单/);
});

test("market AI outlook keeps direction reading to a satisfied and missing condition", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(source, /metCondition\?: string/);
  assert.match(source, /missingCondition\?: string/);
  assert.match(panelSource, /marketAiDirectionSummaryMet/);
  assert.match(panelSource, /directionSummary\?\.metCondition/);
  assert.match(panelSource, /directionSummary\?\.missingCondition/);
  assert.match(panelSource, /directionSummary\?\.headline/);
  assert.match(panelSource, /directionSummary\?\.statusLabel/);
  assert.match(styles, /\.marketAiDirectionSummaryMet\s*\{/);
  assert.match(styles, /\.marketAiDirectionSummaryNext\s*\{/);
});

test("market AI outlook presents independent compact 15-minute, hourly, and daily readings", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(source, /multiTimeframeTrend\?: \{/);
  assert.match(source, /key\?: "15m" \| "1H" \| "1D"/);
  assert.match(source, /function marketAiMultiTimeframeTrend/);
  assert.match(panelSource, /const multiTimeframeTrend = marketAiMultiTimeframeTrend\(outlook\);/);
  assert.match(panelSource, /aria-label="多周期趋势"/);
  assert.match(panelSource, /各周期独立 K线快照/);
  assert.match(panelSource, /\(period\.evidence \?\? \[\]\)\.slice\(0, 2\)/);
  assert.match(panelSource, /确认后重读/);
  assert.match(panelSource, /不是下单或个人化投资建议/);
  assert.match(styles, /\.marketAiMultiTimeframeGrid\s*\{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
  assert.ok(
    styles.lastIndexOf(".marketAiMultiTimeframeGrid,") > styles.indexOf(".marketAiMultiTimeframeGrid {"),
    "the narrow-screen column override must follow the desktop grid rule"
  );
  const trendSection = panelSource.slice(panelSource.indexOf('aria-label="多周期趋势"'), panelSource.indexOf('className="marketAiScenarioDetails"'));
  assert.doesNotMatch(trendSection, /目标价|止损|仓位|杠杆/);
});

test("market AI outlook presents read-only priced plans and expiring old reports", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(source, /pricePlan\?: \{/);
  assert.match(panelSource, /aria-label="15分钟买卖价格计划"/);
  assert.match(panelSource, /做多买入/);
  assert.match(panelSource, /做空卖出/);
  assert.match(panelSource, /若已入场 · 止损/);
  assert.match(panelSource, /若已入场 · 止盈/);
  assert.match(panelSource, /入场观察期/);
  assert.match(panelSource, /分析时卖一价 · 预计做多买入/);
  assert.match(panelSource, /分析时买一价 · 预计做空卖出/);
  assert.match(panelSource, /报价时间/);
  assert.match(panelSource, /只有确认入场后，止盈和止损价才有意义/);
  assert.match(panelSource, /pricePlanExpired/);
  assert.match(panelSource, /计划已到有效期限，请刷新分析/);
  assert.match(panelSource, /上方 \{formatValue\(pricePlan\.upperReassess\)\}/);
  assert.match(panelSource, /下方 \{formatValue\(pricePlan\.lowerReassess\)\}/);
  assert.match(panelSource, /这份缓存报告没有价格计划/);
  assert.match(panelSource, /15分钟候选条件 · 只读观察/);
  assert.match(styles, /\.marketAiPricePlanPrices\s*\{[^}]*grid-template-columns: 1\.3fr repeat\(2, minmax\(0, 1fr\)\)/);
  assert.match(styles, /@media \(max-width: 767px\)\s*\{[\s\S]*?\.marketAiPricePlanPrices\s*\{ grid-template-columns: repeat\(2, minmax\(0, 1fr\)\); \}/);
});

test("market AI outlook distinguishes one primary chart period from its automatic three-period reading", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  const trendSource = source.slice(source.indexOf("function marketAiMultiTimeframeTrend("), source.indexOf("function marketAiOverallView("));
  const aiPageStart = source.indexOf("function MarketAiOutlookPage(");
  const statsPageStart = source.indexOf("function MarketStatsPage(");
  const aiPageSource = source.slice(aiPageStart, statsPageStart);

  assert.match(aiPageSource, /主图观察 .*K线 · 一次分析自动读取 15分钟 \/ 1小时 \/ 日线/);
  assert.match(aiPageSource, /className="marketAiBarControl"/);
  assert.match(aiPageSource, /aria-label="主图观察周期"/);
  assert.match(aiPageSource, /决定下一份报告主结论 · 切换后需重新分析/);
  assert.match(aiPageSource, /label="主图周期"/);
  assert.match(panelSource, /aria-label="一次分析范围"/);
  assert.match(panelSource, /自动读取三个独立周期/);
  assert.match(panelSource, /固定分析周期/);
  assert.match(panelSource, /\["15分钟", "1小时", "日线"\]\.map/);
  assert.match(panelSource, /开始一次分析后，系统会自动读取三个固定周期；无需分别点击。/);
  assert.match(panelSource, /下方展示本次报告中各周期的真实结果与数据状态。/);
  assert.match(trendSource, /available: false/);
  assert.match(trendSource, /旧报告未包含此周期数据。/);
  assert.match(trendSource, /不会用其他周期替代。/);
  assert.match(panelSource, /period\.available \? \([\s\S]*?period\.warning\) \|\| "该周期数据待获取。"/);
  assert.match(styles, /\.marketAiAnalysisScopePeriods\s*\{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(styles, /\.marketAiBarControl\s*\{[\s\S]*?gap: var\(--space-1\);/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.marketAiBarControl\s*\{[\s\S]*?width: 100%;/);
});

test("market AI outlook keeps layout rhythm and explains manual analysis loading", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(panelSource, /const initialAnalysisLoading = loading && !outlook;/);
  assert.match(panelSource, /const refreshingAnalysis = loading && Boolean\(outlook\);/);
  assert.match(panelSource, /aria-busy=\{loading\}/);
  assert.match(panelSource, /role="status" aria-live="polite"/);
  assert.match(panelSource, /正在一次性读取 15分钟、1小时和日线的独立 K线快照/);
  assert.match(panelSource, /正在更新行情快照与 15分钟、1小时、日线趋势 · 当前仍显示上一份报告/);
  assert.match(panelSource, /marketAiLoadingSkeleton/);
  assert.match(panelSource, /\["15m", "1H", "1D"\]\.map/);
  assert.match(panelSource, /initialAnalysisLoading \? \(/);
  assert.match(panelSource, /refreshingAnalysis \? "refreshing" : "initial"/);

  assert.match(styles, /\.marketAiOutlookPanel\s*\{[\s\S]*?--market-ai-space-label: var\(--space-1\);[\s\S]*?--market-ai-space-compact: var\(--space-2\);[\s\S]*?--market-ai-space-content: var\(--space-3\);[\s\S]*?--market-ai-space-section: var\(--space-4\);/);
  assert.match(styles, /\.marketAiScenarioBoard\s*\{[\s\S]*?margin: 0;[\s\S]*?gap: var\(--market-ai-space-section\);/);
  assert.match(styles, /\.marketAiMultiTimeframe\s*\{[\s\S]*?margin: 0;[\s\S]*?gap: var\(--market-ai-space-compact\);/);
  assert.match(styles, /\.marketAiScenarioDetails\s*\{[\s\S]*?margin: 0;[\s\S]*?padding-top: var\(--market-ai-space-section\);/);
  assert.match(styles, /\.marketAiMultiTimeframeGrid article\s*\{[\s\S]*?grid-template-rows: auto minmax\(0, 1fr\) auto;[\s\S]*?gap: var\(--market-ai-space-compact\);/);
  assert.match(styles, /\.marketAiLoadingSkeletonGrid\s*\{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.marketAiLoadingSpinner,[\s\S]*?animation: none;/);
});

test("market AI outlook keeps report context intact beside desktop controls", () => {
  const aiPageStart = source.indexOf("function MarketAiOutlookPage(");
  const statsPageStart = source.indexOf("function MarketStatsPage(");
  const aiPageSource = source.slice(aiPageStart, statsPageStart);

  assert.match(aiPageSource, /className="workspaceHeader marketAiWorkspaceHeader"/);
  assert.match(aiPageSource, /className="marketAiWorkspaceTitle"/);
  assert.match(aiPageSource, /className="workspaceActions marketAiWorkspaceActions"/);
  assert.match(styles, /\.marketAiWorkspaceHeader\s*\{[\s\S]*?flex: 0 0 auto;[\s\S]*?row-gap: var\(--space-3\);/);
  assert.match(styles, /\.marketAiWorkspaceTitle\s*\{[\s\S]*?flex: 1 1 360px;[\s\S]*?min-width: 360px;/);
  assert.match(styles, /\.marketAiWorkspaceTitle p\s*\{[\s\S]*?white-space: nowrap;/);
  assert.match(styles, /@media \(max-width: 1680px\) and \(min-width: 761px\)[\s\S]*?\.marketAiWorkspaceActions\s*\{[\s\S]*?flex-basis: 100%;/);
});

test("market AI outlook translates raw evidence into a readable chart report", () => {
  const panelSource = source.slice(source.indexOf("function MarketAiOutlookPanel"), source.indexOf("function accountSourceLabel"));
  assert.match(source, /function marketAiReadableText/);
  assert.match(source, /replace\(\/recent20High\/gi, "近20根最高价"\)/);
  assert.match(source, /replace\(\/recentAverage\/gi, "近期平均成交量"\)/);
  assert.match(source, /function marketAiChartSummary/);
  assert.match(source, /function marketAiChartOnlyText/);
  assert.match(source, /function marketAiForecasts/);
  assert.match(source, /return \["15m", "1h", "today"\]\.flatMap/);
  assert.match(source, /function marketAiPrimaryFacts/);
  assert.match(source, /\.slice\(0, 3\)/);
  assert.match(panelSource, /主图结构概览/);
  assert.match(panelSource, /图表依据/);
  assert.match(panelSource, /补充数据与来源/);
  assert.match(panelSource, /marketAiChartSummary\(outlook\)/);
  assert.match(panelSource, /<Disclosure className=\{`marketAiSupplement/);
  assert.doesNotMatch(panelSource, /recentAverage/);
  assert.doesNotMatch(panelSource, /contracting/);
});

test("market AI outlook uses content-sized responsive reading blocks", () => {
  assert.match(styles, /\.marketAiOutlookPanel\s*\{[\s\S]*?min-height: 0;[\s\S]*?overflow: visible;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiReading\s*\{[\s\S]*?grid-template-columns: minmax\(260px, 0\.8fr\) minmax\(0, 1\.5fr\);[\s\S]*?align-items: stretch;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiReading > \.marketAiConclusion,[\s\S]*?\.marketAiReading > \.marketAiEvidence\s*\{[\s\S]*?display: flex;[\s\S]*?flex-direction: column;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiFactList\s*\{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);[\s\S]*?\}/);
  assert.match(styles, /\.marketAiForecastGrid\.count-2\s*\{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);[\s\S]*?\}/);
  assert.match(styles, /\.marketAiForecastGrid\.count-3\s*\{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);[\s\S]*?\}/);
  assert.match(styles, /\.marketAiForecastGrid\s*\{[\s\S]*?align-items: stretch;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiForecastCard\s*\{[\s\S]*?display: flex;[\s\S]*?flex-direction: column;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiForecastCard > strong\s*\{[\s\S]*?min-height: calc\(2 \* 1\.35em\);[\s\S]*?margin: 6px 0 0;[\s\S]*?line-height: 1\.35;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiForecastCard > em\s*\{[\s\S]*?min-height: calc\(2 \* 1\.45em\);[\s\S]*?margin: auto 0 0;[\s\S]*?border-top: 1px solid #eef3f7;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiForecastCardHeader\s*\{[\s\S]*?justify-content: space-between;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiSupplementBody\s*\{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);[\s\S]*?\}/);
  assert.match(styles, /@media \(max-width: 1120px\)[\s\S]*?\.marketAiReading,[\s\S]*?grid-template-columns: 1fr;/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.marketAiFactList\s*\{[\s\S]*?grid-template-columns: 1fr;/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.marketAiForecastGrid,[\s\S]*?\.marketAiForecastGrid\.count-2,[\s\S]*?\.marketAiForecastGrid\.count-3\s*\{[\s\S]*?grid-template-columns: 1fr;/);
  assert.match(styles, /\.marketAiDecision\s*\{[\s\S]*?border-radius: 12px;[\s\S]*?padding: 14px;[\s\S]*?\}/);
  assert.match(styles, /\.marketAiStructureGrid\s*\{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);[\s\S]*?\}/);
  assert.match(styles, /\.marketAiConfirmationCandidateGrid\s*\{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);[\s\S]*?\}/);
  assert.match(styles, /\.marketAiConfirmationCandidateGrid article\.bullish\s*\{[\s\S]*?border-color: #9bd9b8/);
  assert.match(styles, /\.marketAiConfirmationCandidateGrid article\.bearish\s*\{[\s\S]*?border-color: #eab9c1/);
  assert.match(styles, /\.marketAiConfidenceStatusGrid, \.marketAiEvidenceGapGrid\s*\{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);/);
  assert.match(styles, /\.marketAiPeriodProvenance\s*\{[\s\S]*?border-left: 3px solid/);
  assert.match(styles, /\.marketAiCandidateGap\s*\{[\s\S]*?border-left: 3px solid/);
  assert.match(styles, /@media \(max-width: 1120px\)[\s\S]*?\.marketAiConfidenceStatusGrid, \.marketAiEvidenceGapGrid\s*\{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.marketAiDecisionHeader, \.marketAiStructureHeader, \.marketAiConfirmationLevelsHeader, \.marketAiConfidenceBasisHeader\s*\{[\s\S]*?flex-direction: column;[\s\S]*?\}/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.marketAiStructureGrid\s*\{[\s\S]*?grid-template-columns: 1fr;/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.marketAiConfirmationCandidateGrid\s*\{[\s\S]*?grid-template-columns: 1fr;/);
  assert.match(styles, /@media \(max-width: 760px\)[\s\S]*?\.marketAiConfidenceStatusGrid, \.marketAiEvidenceGapGrid\s*\{[\s\S]*?grid-template-columns: 1fr;/);
});
