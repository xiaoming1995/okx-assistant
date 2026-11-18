import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const pageStart = source.indexOf("function CleanAutomationPage(");
const pageEnd = source.indexOf("function StrategyListPage(");
assert.ok(pageStart >= 0 && pageEnd > pageStart, "should locate CleanAutomationPage source range");
const page = source.slice(pageStart, pageEnd);
const narrow = styles.slice(styles.lastIndexOf("@media (max-width: 760px)"));

test("empty-strategy overview states the real conclusion and offers a first-run path", () => {
  assert.match(page, /const hasStrategies = strategies\.length > 0/);
  assert.match(page, /const hasEnabledStrategy = strategies\.some/);
  assert.match(page, /\? "尚未创建策略"/);
  assert.match(page, /引擎正在运行，但当前没有策略会产生信号/);
  assert.match(page, /实盘始终隔离/);
  // 精简后：起步引导收进结论卡的一行提示，不再单独占一张大卡片。
  assert.match(page, /className="cleanDecisionHint"/);
  assert.match(page, /条策略都处于暂停，启用后才会产生信号/);
  assert.match(page, /还没有策略，先创建一条/);
  assert.match(page, /onClick=\{hasStrategies \? onOpenStrategies : resetForCreate\}/);
  assert.match(page, /\{hasStrategies \? "查看策略" : "创建策略"\}/);
});

test("risk checks are grouped and passed checks stay collapsed by default", () => {
  assert.match(page, /const blockingChecks = riskChecks\.filter/);
  assert.match(page, /const warningChecks = riskChecks\.filter/);
  assert.match(page, /const passedChecks = riskChecks\.filter/);
  assert.match(page, /renderRiskGroup\("阻塞项", blockingChecks\)/);
  assert.match(page, /renderRiskGroup\("需关注", warningChecks\)/);
  assert.match(page, /renderRiskGroup\("已通过", passedChecks\)/);
  assert.match(page, /aria-expanded=\{showPassedChecks\}/);
  assert.match(page, /showPassedChecks \? "收起" : "展开"/);
  assert.doesNotMatch(page, /visibleRiskChecks/);
});

test("loading, error and empty states give Chinese reasons plus a recovery action", () => {
  assert.match(page, /<DataLoadingState label="正在检查启用条件" compact \/>/);
  assert.match(page, /启用检查未能完成，页面不会据此判断能否下单/);
  assert.match(page, /自动交易数据未能加载，页面内容可能不是最新/);
  assert.match(page, /\{loadError \? \(/);
  assert.match(page, /<strong>启用检查未完成<\/strong>/);
  // 无告警时整块不渲染，改成校验按条件渲染
  assert.match(page, /\{recentAlerts\.length \? \(/);
  assert.match(page, /还没有策略信号/);
  assert.match(page, /查看全部日志/);
  assert.doesNotMatch(page, /setRiskStatus\(error instanceof Error \? error\.message/);
  assert.doesNotMatch(page, /暂无未确认告警/);
  assert.doesNotMatch(page, /当前只会记录信号/);
});

test("onboarding styles reuse design tokens and reflow on narrow screens", () => {
  assert.match(styles, /\.automationOnboarding \{/);
  assert.match(styles, /\.automationOnboardingSteps \{/);
  assert.match(styles, /\.automationStepIndex \{/);
  assert.match(styles, /\.automationCheckGroupLabel \{/);
  assert.match(styles, /\.emptyRow\.compact\.automationEmptyState \{/);
  assert.match(styles, /\.automationOnboardingBody p \{[\s\S]*?var\(--color-text-soft\)/);
  assert.match(styles, /\.automationOnboardingSteps \{[\s\S]*?var\(--space-4\)/);
  assert.match(narrow, /\.automationOnboardingBody \{\n    align-items: stretch;\n    flex-direction: column;\n  \}/);
  assert.match(narrow, /\.automationOnboardingSteps \{\n    grid-template-columns: 1fr;\n  \}/);
});

test("strategy form supports multiple instruments and a daily position cap", () => {
  assert.match(source, /instIds: string\[\]/);
  assert.match(source, /dailyPositionPct: string/);
  assert.match(source, /instIds: \["BTC-USDT-SWAP"\]/);
  assert.match(source, /dailyPositionPct: "0"/);
  assert.match(source, /instIds: form\.instIds\.map/);
  assert.match(source, /dailyPositionPct: form\.dailyPositionPct/);
  assert.match(source, /function strategyInstrumentLabel/);
  assert.match(page, /合约 · 已选 \{form\.instIds\.length\}/);
  assert.match(page, /aria-label="常用合约快捷选择"/);
  assert.match(page, /aria-label="添加自定义合约代码"/);
  assert.match(page, /aria-pressed=\{form\.instIds\.includes\(item\)\}/);
  assert.match(page, /每日仓位%/);
  assert.match(page, /额度 = 模拟盘总权益 × 该百分比/);
  assert.match(page, /同策略多合约共享同一额度，0 表示不限制/);
  assert.doesNotMatch(page, /止盈止损只会随策略保存，不会自动平仓/);
});

test("instrument picker styles reuse tokens and support keyboard focus", () => {
  assert.match(styles, /\.automationInstrumentField \{/);
  assert.match(styles, /\.automationInstrumentChip\.selected/);
  assert.match(styles, /\.automationInstrumentChip:focus-visible/);
  assert.match(styles, /var\(--color-success-soft\)/);
  assert.match(styles, /prefers-reduced-motion: reduce/);
  assert.match(narrow, /\.automationInstrumentAddRow \{[\s\S]*?flex-direction: column;/);
});

test("single-order cap is derived from the fixed order size and hidden from the form", () => {
  // 恒等于 sz 的上限不再占用表单字段；提交时由 sz 派生，保持 API 契约不变。
  assert.match(source, /maxOrderContracts: form\.sz\.trim\(\) \|\| "1"/);
  assert.match(source, /maxOrderContracts\?: string/);
  assert.doesNotMatch(source, /maxOrderContracts: form\.maxOrderContracts/);
  assert.doesNotMatch(source, /maxOrderContracts: strategy\.max_order_contracts/);
  assert.doesNotMatch(source, /next\.maxOrderContracts = value/);
  assert.doesNotMatch(page, /<span>单笔上限<\/span>/);
});

test("daily position field echoes the simulated account amount", () => {
  assert.match(source, /type AutomationEquity = \{/);
  assert.match(page, /\/api\/automation\/equity/);
  assert.match(page, /const loadAutomationEquity = React\.useCallback/);
  assert.match(page, /if \(view !== "create"\) return;/);
  assert.match(page, /window\.setTimeout\(\(\) => \{ void loadAutomationEquity\(\); \}, 300\)/);
  assert.match(page, /模拟盘权益 \{automationEquity\?\.equity\} USDT/);
  assert.match(page, /可用 \{automationEquity\.availEq\}/);
  assert.match(page, /automationEquity\?\.source === "okx" \? "实时快照" : "缓存快照"/);
  assert.match(styles, /\.automationEquityMeta \{/);
  assert.match(page, /USDT\/日/);
  assert.match(page, /今日已用/);
  assert.match(page, /"刷新"/);
  assert.match(page, /aria-live="polite"/);
  assert.match(page, /equityHintTone/);
  assert.match(styles, /\.automationEquityHint \{/);
  assert.match(styles, /\.automationEquityHint\.warn/);
  assert.match(styles, /\.automationFooterWarn/);
});

test("take-profit and stop-loss fields state their price-change basis explicitly", () => {
  assert.match(source, /止盈%/);
  assert.match(source, /止损%/);
  assert.match(source, /止盈口径/);
  assert.match(source, /不乘杠杆/);
  assert.match(source, /默认不在 OKX 挂条件单/);
  assert.match(source, /交易所侧兜底开关/);
  assert.match(source, /0 表示关闭该项/);
});

test("signal period is explained and take-profit fields are gated by execution mode", () => {
  assert.match(source, /信号周期/);
  assert.match(source, /评估 1 次，单合约 ≤\$\{barCadence\.perDay\} 次\/天/);
  assert.match(source, /止盈止损不受周期影响，仍每 10 秒检查/);
  assert.match(source, /const exitsDisabled = form\.executionMode !== "simulated_auto"/);
  assert.match(source, /disabled=\{exitsDisabled\}/);
  assert.match(source, /只提醒模式：不下单、不自动平仓，止盈止损不生效/);
  assert.match(source, /1m 1440 \/ 5m 288 \/ 15m 96 \/ 1H 24/);
  assert.match(source, /const automationBarCadence: Record<string, \{ cadence: string; perDay: number \}>/);
  assert.match(source, /LLM 每根 K 线调用 1 次，当前 \$\{strategyContractCount\} 合约 ≈ \$\{dailyEvalLimit\} 次\/天/);
});

test("strategy form explains judgement, execution and daily cap semantics inline", () => {
  assert.match(page, /置信度低于 \$\{automationStatus\?\.llmMinConfidence \?\? 70\} 不下单/);
  assert.match(page, /MA\$\{form\.fastWindow\} 上穿 \/ 下穿 MA\$\{form\.slowWindow\} 出多 \/ 空/);
  assert.match(page, /窗口沿用已保存值/);
  assert.match(page, /风控通过后模拟盘自动下单，实盘永不自动执行/);
  assert.match(page, /只记录信号，不下单、不检查止盈止损/);
  assert.match(page, /已提交开仓的名义金额/);
  assert.match(page, /0 表示不限制，平仓不占用额度/);
  assert.match(source, /llmMinConfidence\?: number/);
});

test("hint-heavy strategy fields span the full form row instead of half a column", () => {
  assert.match(page, /className="fieldBlock automationNameField"/);
  assert.match(page, /className="fieldBlock automationBarField"/);
  assert.match(page, /className="fieldBlock automationDailyField"/);
  assert.match(styles, /\.cleanStrategyForm > \.automationNameField,[\s\S]{0,220}?grid-column: 1 \/ -1;/);
  assert.match(styles, /\.automationDailyField \.mantine-TextInput-root \{\s*max-width: 220px;/);
  assert.match(styles, /\.automationCapNote \{\s*line-height: 1\.55;\s*overflow-wrap: anywhere;/);
  assert.match(styles, /@media \(max-width: 900px\) \{\s*\.cleanStrategyForm \{\s*grid-template-columns: 1fr;/);
});

test("strategy editor scrolls instead of clipping its lower fields", () => {
  assert.match(page, /className="cleanAutomationView cleanAutomationEditor"/);
  assert.match(styles, /\.cleanAutomationEditor \{[\s\S]*?overflow-y: auto;[\s\S]*?scrollbar-gutter: stable;/);
  // 面板必须保持自然高度，否则被 flex 压缩后又被自身 overflow:hidden 裁掉下半截。
  assert.match(styles, /\.cleanAutomationEditor > \.cleanPanel \{\s*flex: 0 0 auto;/);
});

test("strategy form packs numeric fields into one row and pins the footer", () => {
  assert.match(page, /className="automationNumberRow"/);
  assert.match(styles, /\.automationNumberRow \{[\s\S]*?grid-template-columns: repeat\(4, minmax\(0, 1fr\)\);/);
  assert.match(styles, /@media \(max-width: 900px\) \{[\s\S]{0,240}?\.automationNumberRow \{\s*grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
  assert.match(styles, /\.automationRefreshLink \{[\s\S]*?color: var\(--color-muted-strong\);/);
  assert.match(page, /className="automationRefreshLink"/);
});

test("judgement, execution and period share one row to keep the editor short", () => {
  assert.match(page, /className="automationTripleRow"/);
  assert.match(styles, /\.automationTripleRow \{[\s\S]*?grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);/);
  assert.match(page, /className="fieldBlock automationBarField"/);
});

test("signal period options are shown in Chinese while values stay as okx bar codes", () => {
  assert.match(source, /const automationBarLabels: Record<string, string>/);
  assert.match(source, /"1H": "1 小时"/);
  assert.match(source, /\{ key: "1H", label: automationBarLabel\("1H"\) \}/);
  assert.match(source, /automationBarLabel\(strategy\.bar\)/);
  assert.match(source, /automationBarLabel\(signal\.bar\)/);
  assert.match(source, /automationBarLabel\(activeStrategy\.bar\)/);
});

test("strategy list and overview both expose a create entry", () => {
  assert.match(source, /const openStrategyCreator = React\.useCallback/);
  assert.match(source, /<StrategyListPage onBackToAutomation=\{\(\) => setAutomationTab\("overview"\)\} onEditStrategy=\{openStrategyEditor\} onCreateStrategy=\{openStrategyCreator\} \/>/);
  assert.match(source, /onCreateStrategy: \(\) => void;/);
  assert.match(source, /onClick=\{onCreateStrategy\}>/);
  assert.match(page, /onClick=\{resetForCreate\}>新建策略/);
  assert.match(source, /initialCreate=\{strategyCreateIntent\}/);
});

test("signal log formats times as hours:minutes:seconds with a day hint", () => {
  assert.match(source, /function formatClockSecond\(value\?: string \| number \| null\)/);
  assert.match(source, /const seconds = String\(date\.getSeconds\(\)\)\.padStart\(2, "0"\);/);
  assert.match(source, /return `\$\{hours\}:\$\{minutes\}:\$\{seconds\}`;/);
  assert.match(source, /function formatDayHint\(value\?: string \| number \| null\)/);
  assert.match(source, /<strong>\{formatClockSecond\(signal\.ts\)\}<\/strong>/);
  assert.match(source, /<small>\{hasValidDate \? formatDayHint\(signal\.ts\) : formatTime\(signal\.ts\)\}<\/small>/);
  assert.match(source, /if \(dayDiff === 0\) return "今天";/);
  assert.match(source, /if \(dayDiff === 1\) return "昨天";/);
});
