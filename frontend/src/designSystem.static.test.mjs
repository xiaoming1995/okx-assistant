import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
const theme = readFileSync(new URL("./mantineTheme.ts", import.meta.url), "utf8");
const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");

test("typography tokens use one self-hosted ledger type family", () => {
  assert.match(styles, /--font-ui:[^\n]*"IBM Plex Sans"[^\n]*;/);
  assert.match(styles, /--font-num:[^\n]*"IBM Plex Mono"[^\n]*;/);
  assert.match(styles, /--type-display: 48px;/);
  assert.match(styles, /font-family: var\(--font-ui\);/);
  assert.match(styles, /code, kbd, samp, pre \{\s*font-family: var\(--font-num\);/);
  assert.match(styles, /@font-face \{\s*font-family: "IBM Plex Sans";[\s\S]*?url\("\/fonts\/ibm-plex-sans-variable\.woff2"\)/);
  assert.match(styles, /@font-face \{\s*font-family: "IBM Plex Mono";[\s\S]*?font-weight: 700;/);
  assert.doesNotMatch(styles, /fonts\.googleapis\.com|fonts\.gstatic\.com/);
  assert.match(html, /rel="preload" href="\/fonts\/ibm-plex-sans-variable\.woff2"/);
  assert.match(theme, /fontFamily: fontUi,/);
  assert.match(theme, /fontFamilyMonospace: fontNum,/);
  assert.match(theme, /fontFamily: fontUi,\s*fontWeight: "750"/);
});

test("mono type stays a hierarchy marker on primary numbers only", () => {
  assert.match(styles, /\.marketOverviewBigNumber \{\s*font-family: var\(--font-num\);\s*font-size: var\(--type-display\);/);
  assert.match(styles, /\.heroPriceBlock strong \{[^}]*font-family: var\(--font-num\);/);
  assert.match(styles, /\.miniMetric strong \{[^}]*font-family: var\(--font-num\);/);
  assert.match(styles, /\.marketOverviewBigNumber small \{[^}]*font-family: var\(--font-ui\);/);
  assert.match(styles, /\.marketOverviewBigNumber \{\s*font-size: 28px;\s*\}/);
  assert.doesNotMatch(styles, /\.heroPriceBlock strong \{[^}]*font-size: var\(--type-display\)/);
  const monoUses = [...styles.matchAll(/font-family: var\(--font-num\);/g)].length;
  assert.ok(monoUses <= 6, `--font-num must not become a global skin (found ${monoUses} declarations)`);
});

test("shared frontend foundation exposes the documented simple-workbench tokens", () => {
  assert.match(styles, /--space-1: 4px;[\s\S]*?--space-2: 8px;[\s\S]*?--space-3: 12px;[\s\S]*?--space-4: 16px;[\s\S]*?--space-5: 24px;[\s\S]*?--space-6: 32px;[\s\S]*?--space-7: 48px;/);
  assert.match(styles, /--control-height-sm: 28px;[\s\S]*?--control-height: 34px;[\s\S]*?--control-height-lg: 40px;/);
  assert.match(styles, /--motion-fast: 120ms;[\s\S]*?--motion-standard: 160ms;[\s\S]*?--z-popover: 12;/);
  assert.match(styles, /--text: var\(--color-text\);[\s\S]*?--panel: var\(--color-surface-muted\);[\s\S]*?--warning: var\(--color-warning\);/);
  assert.match(styles, /\.appShell \{[\s\S]*?background: var\(--color-bg\);/);
});

test("shared controls have restrained motion and keyboard feedback", () => {
  assert.match(styles, /button,[\s\S]*?\.disclosureTrigger \{[\s\S]*?transition:[\s\S]*?var\(--motion-fast\)/);
  assert.match(styles, /button:not\(:disabled\):active,[\s\S]*?transform: translateY\(1px\);/);
  assert.match(styles, /\.disclosureTrigger:focus-visible,[\s\S]*?box-shadow: var\(--focus-ring\);/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?transition-duration: 0\.01ms !important;/);
});

test("navigation and date selection expose their current state", () => {
  const sectionTabsSource = source.slice(source.indexOf("function SectionTabs"), source.indexOf("function App()"));
  assert.match(sectionTabsSource, /aria-current=\{item\.active \? "page" : undefined\}/);
  assert.match(source, /aria-current=\{section === "market" \? "page" : undefined\}/);
  const timelineSource = source.slice(source.indexOf("function UsMarketTimelinePage"), source.indexOf("function AnnouncementsPage"));
  assert.match(timelineSource, /aria-pressed=\{item === date\}/);
});

test("timeline overrides use the shared token vocabulary at normal and narrow widths", () => {
  assert.match(styles, /\.usTimelinePage \{\s*padding: var\(--space-5\) var\(--space-4\) var\(--space-7\);[\s\S]*?background: var\(--color-surface\);/);
  assert.match(styles, /\.usTimelineFilterGroup button \{[\s\S]*?min-height: var\(--control-height\);[\s\S]*?padding: 0 var\(--space-3\);/);
  assert.match(styles, /\.usEventCard > div \{[\s\S]*?border-radius: var\(--radius-panel\);[\s\S]*?padding: var\(--space-3\);/);
  assert.match(styles, /@media \(max-width: 680px\) \{[\s\S]*?\.usTimelinePage \{\s*padding: var\(--space-3\) var\(--space-4\) var\(--space-6\);/);
});

test("ledger layout migration stays scoped to the chart page and reuses tokens only", () => {
  const marker = "账本式版式迁移 · 第 1 页：行情图表";
  assert.ok(styles.includes(marker), "ledger migration block missing");
  const ledger = styles.slice(styles.indexOf(marker));

  // 单一纸面与贯穿全页的对齐轴
  assert.match(ledger, /\.marketChartMain \{\s*gap: 0;\s*padding: 0;[\s\S]*?background: var\(--color-surface\);/);
  assert.match(ledger, /padding-left: var\(--space-7\);\s*padding-right: var\(--space-7\);/);
  assert.match(ledger, /border-bottom: 1px solid var\(--color-border\);/);

  // 三档断点与矮屏既有紧凑优化
  assert.match(ledger, /@media \(max-width: 1200px\) \{[\s\S]*?padding-left: var\(--space-5\);/);
  assert.match(ledger, /@media \(max-width: 767px\) \{[\s\S]*?padding-left: var\(--space-4\);/);
  assert.match(ledger, /@media \(min-width: 1201px\) and \(max-height: 719px\)/);

  // 并排时一条竖线、纵向时一条横线，且保留驱动订单簿固定列宽的容器查询
  assert.match(ledger, /@container \(min-width: 960px\) \{[\s\S]*?border-left: 1px solid var\(--color-border\);/);
  assert.match(ledger, /@container \(max-width: 959px\) \{[\s\S]*?border-bottom: 1px solid var\(--color-border\);/);
  assert.match(styles, /@container \(min-width: 960px\) \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\) 280px;/);

  // 迁移不得外溢到其他页面，也不得引入新的硬编码颜色或间距
  assert.doesNotMatch(ledger, /^\s*\.(contractHero|chartPanel|marketOrderBook|marketChartToolbar|marketChartReading|heroPriceBlock|miniMetric|marketNoticeSlot|marketChartTopbar)\s*\{/m);
  assert.doesNotMatch(ledger, /#[0-9a-fA-F]{3,8}\b/);
  assert.doesNotMatch(ledger, /^\s+(?:padding|margin|gap|font-size|border-radius)(?:-[a-z]+)?:\s*\d+px\b/m);
});

test("AI outlook ledger migration converges the page shell without erasing semantic states", () => {
  const marker = "账本式版式迁移 · 第 2 页：AI 看行情";
  assert.ok(styles.includes(marker), "second ledger migration block missing");
  const ledger = styles.slice(styles.indexOf(marker));

  assert.match(ledger, /\.marketAiMain \{\s*gap: 0;\s*padding: 0;[\s\S]*?background: var\(--color-surface\);/);
  assert.match(ledger, /padding-left: var\(--space-7\);\s*padding-right: var\(--space-7\);/);
  assert.match(ledger, /border-bottom: 1px solid var\(--color-border\);/);
  assert.match(ledger, /\.marketAiMain > \.marketAiOutlookPanel\.fullPage \{/);
  assert.match(ledger, /\.marketAiMain \.heroTiles \{\s*grid-template-columns: repeat\(3, minmax\(0, 1fr\)\);\s*\}/);
  assert.match(ledger, /\.marketAiMain \.heroTiles > \.miniMetric:last-child \{\s*grid-column: span 2;\s*\}/);
  assert.match(ledger, /@media \(max-width: 767px\) \{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
  assert.doesNotMatch(ledger, /grid-template-columns:[^;]*\d+px/);
  assert.match(ledger, /@media \(max-width: 1200px\) \{[\s\S]*?padding-left: var\(--space-5\);/);
  assert.match(ledger, /@media \(max-width: 767px\) \{[\s\S]*?padding-left: var\(--space-4\);/);
  assert.match(ledger, /@media \(min-width: 1201px\) and \(max-height: 719px\)/);

  // 报告内部的语义卡片必须留在原样，账本式不抹涨跌底色与证据边框
  assert.doesNotMatch(ledger, /\.marketAi(Conclusion|Evidence|Reading|ForecastCard|ScenarioBoard)\b/);
  assert.doesNotMatch(ledger, /^\s*\.(contractHero|miniMetric|heroPriceBlock|marketAiOutlookPanel|marketAiWorkspaceHeader)\s*\{/m);
  assert.doesNotMatch(ledger, /#[0-9a-fA-F]{3,8}\b/);
  assert.doesNotMatch(ledger, /^\s+(?:padding|margin|gap|font-size|border-radius)(?:-[a-z]+)?:\s*\d+px\b/m);
});

const finalMigrationBlocks = [
  { marker: "账本式版式迁移 · 第 3 页：交易", root: "\\.tradePage\\.tradePageWorkbench" },
  { marker: "账本式版式迁移 · 第 4 页：自动化总览", root: "\\.automationPage\\.cleanAutomationPage" },
  { marker: "账本式版式迁移 · 第 5 页：持仓", root: "\\.positionsPage" }
];

function finalBlock(index) {
  const start = styles.indexOf(finalMigrationBlocks[index].marker);
  const end = index + 1 < finalMigrationBlocks.length
    ? styles.indexOf(finalMigrationBlocks[index + 1].marker)
    : styles.length;
  return styles.slice(start, end);
}

test("the last three high-frequency pages share one scoped ledger shell", () => {
  finalMigrationBlocks.forEach(({ marker, root }, i) => {
    assert.ok(styles.includes(marker), `${marker} missing`);
    const block = finalBlock(i);
    assert.match(block, new RegExp(`${root} \\{\\s*gap: 0;\\s*padding: 0;[\\s\\S]*?background: var\\(--color-surface\\);`));
    assert.match(block, /padding-left: var\(--space-7\);\s*padding-right: var\(--space-7\);/);
    assert.match(block, /border-bottom: 1px solid var\(--color-border\);/);
    // 语义警告条按轴缩进，保留自身状态底色与边框，不叠 48px 内边距
    assert.match(block, /> \.notice \{[\s\S]*?margin-left: var\(--space-7\);/);
    assert.match(block, /@media \(max-width: 1200px\) \{[\s\S]*?padding-left: var\(--space-5\);/);
    assert.match(block, /@media \(max-width: 767px\) \{[\s\S]*?padding-left: var\(--space-4\);/);
    assert.match(block, /@media \(min-width: 1201px\) and \(max-height: 719px\)/);
    assert.match(block, /\.miniMetric strong,[\s\S]*?text-align: right;/);
    assert.match(block, /@media \(max-width: 767px\) \{[\s\S]*?text-align: left;/);
    // 迁移不得外溢到其他页面，也不得引入新的硬编码颜色或间距
    assert.doesNotMatch(block, /^\s*\.(tradeWorkbenchOverview|tradeTicket|tradeGrid|workbenchPanel|cleanPanel|cleanDecisionPanel|cleanAutomationView|cleanAutomationGrid|signalLogMinimalPanel|positionSummary|miniMetric|notice)\s*\{/m);
    assert.doesNotMatch(block, /#[0-9a-fA-F]{3,8}\b/);
    assert.doesNotMatch(block, /^\s+(?:padding|margin|gap|font-size|border-radius)(?:-[a-z]+)?:\s*\d+px\b/m);
  });
});

test("final ledger migrations keep functional column widths and semantic states", () => {
  const [trade, automation, positions] = [0, 1, 2].map(finalBlock);

  // 交易：两栏竖线 / 纵向横线；440px 下单列宽与紧凑模式都不动
  assert.match(trade, /\.tradeWorkbenchSide \{\s*border-left: 1px solid var\(--color-border\);/);
  assert.match(trade, /@media \(max-width: 1200px\) \{[\s\S]*?border-bottom: 1px solid var\(--color-border\);/);
  assert.doesNotMatch(trade, /grid-template-columns/);

  // 自动化：结论语义卡片只加留白，不抹状态边框与底色；300px 右栏列宽不动
  assert.match(automation, /cleanDecisionPanel \{\s*margin-bottom: var\(--space-4\);\s*\}/);
  assert.doesNotMatch(automation, /cleanDecisionPanel \{[^}]*(?:border:|background:)/);
  assert.doesNotMatch(automation, /grid-template-columns/);
  assert.match(automation, /cleanAutomationGrid > \.cleanPanel \{\s*border-left: 1px solid var\(--color-border\);/);

  // 持仓：8 列表格与容器内横向滚动不改，只把面板内部重复内边距归零
  assert.doesNotMatch(positions, /positionDataTable/);
  assert.match(positions, /positionPnlSummary \{\s*flex: 0 0 auto;/);
  assert.match(positions, /\.signalLogTableWrap \{\s*padding-left: 0;\s*padding-right: 0;\s*\}/);
  assert.match(positions, /\.signalLogMinimalPanel > \.signalLogMinimalPanelHeader \{\s*background: transparent;\s*\}/);
});

const tailMigrationBlocks = [
  { marker: "账本式版式迁移 · 长尾 1：事件时间线", root: "\\.usTimelinePage" },
  { marker: "账本式版式迁移 · 长尾 2：OKX 公告", root: "\\.announcementsPage" },
  { marker: "账本式版式迁移 · 长尾 3：AI 配置 / 设置", root: "\\.llmPage" },
  { marker: "账本式版式迁移 · 长尾 4：AI 用量", root: "\\.usagePage" },
  { marker: "账本式版式迁移 · 长尾 5：信号详情", root: "\\.signalsPage\\.signalDetailPage" }
];

function tailBlock(index) {
  const start = styles.indexOf(tailMigrationBlocks[index].marker);
  // 后续步骤会继续在文件末尾追加区块，最后一个长尾区块必须截到下一个迁移注释，
  // 不能一路取到文件末尾，否则新增区块会被误算进第 4 步的断言。
  const rest = styles.slice(start + 1);
  const next = rest.search(/\/\* -+ 账本式版式迁移 · /);
  return next === -1 ? styles.slice(start) : styles.slice(start, start + 1 + next);
}

test("all five long-tail pages share one scoped ledger shell", () => {
  tailMigrationBlocks.forEach(({ marker, root }, i) => {
    assert.ok(styles.includes(marker), `${marker} missing`);
    const block = tailBlock(i);

    // 单一纸面、贯穿全页的对齐轴与页头分节线
    assert.match(block, new RegExp(`${root} \\{\\s*gap: 0;\\s*padding: 0;[\\s\\S]*?background: var\\(--color-surface\\);`));
    assert.match(block, /padding-left: var\(--space-7\);\s*padding-right: var\(--space-7\);/);
    assert.match(block, /border-bottom: 1px solid var\(--color-border\);/);
    assert.match(block, /> \.notice \{[\s\S]*?margin-left: var\(--space-7\);/);

    // 三档降级、矮屏让路与数字轴按断点切换
    assert.match(block, /@media \(max-width: 1200px\) \{[\s\S]*?padding-left: var\(--space-5\);/);
    assert.match(block, /@media \(max-width: 767px\) \{[\s\S]*?padding-left: var\(--space-4\);/);
    assert.match(block, /@media \(min-width: 1201px\) and \(max-height: 719px\)/);
    assert.match(block, /(?:\.miniMetric strong,|\.usEventValues b,|\.announcementTimes \{)[\s\S]*?text-align: right;/);
    assert.match(block, /@media \(max-width: 767px\) \{[\s\S]*?text-align: left;/);

    // 只写 scoped 选择器，不引入硬编码颜色或任意间距，也不外溢到未迁移页面
    assert.doesNotMatch(block, /^\s*\.(usTimelineHeader|usEventCard|announcementLayout|announcementTypePanel|announcementListPanel|llmGrid|llmConfigPanel|usageListPanel|signalLogMinimalPanel|signalDetailSummary|signalDetailFullPanel|panelHeader|notice)\s*\{/m);
    assert.doesNotMatch(block, /#[0-9a-fA-F]{3,8}\b/);
    assert.doesNotMatch(block, /^\s+(?:padding|margin|gap|font-size|border-radius)(?:-[a-z]+)?:\s*\d+px\b/m);
    assert.doesNotMatch(block, /\.(marketOverviewPage|radarPage|accountPage|earnPage|strategiesPage|ordersPage|tradingDataMain|marketAiRecordsPage)\b/);
  });
});

test("long-tail migrations keep functional column widths and semantic states", () => {
  const [timeline, announcements, settings, usage, detail] = [0, 1, 2, 3, 4].map(tailBlock);

  // 时间线：事件行退回账本行，政策决议的语义强调与 700px 阅读栏都不动
  assert.match(timeline, /\.usEventCard > div \{[\s\S]*?border-radius: 0;[\s\S]*?background: transparent;/);
  assert.match(timeline, /\.usEventCard\.primary > div \{[\s\S]*?border-left: 3px solid var\(--color-border-strong\);[\s\S]*?background: var\(--color-surface-muted\);/);
  assert.doesNotMatch(timeline, /^\s*(?:width|max-width):/m);

  // 公告与设置：功能性两栏竖线 / 纵向横线，列宽比例一律不改
  assert.match(announcements, /\.announcementTypePanel \{\s*border-right: 1px solid var\(--color-border\);/);
  assert.match(announcements, /@media \(max-width: 1200px\) \{[\s\S]*?border-bottom: 1px solid var\(--color-border\);/);
  assert.doesNotMatch(announcements, /grid-template-columns/);
  assert.match(settings, /\.llmStatusPanel \{\s*border-left: 1px solid var\(--color-border\);/);
  assert.match(settings, /@media \(max-width: 1200px\) \{[\s\S]*?border-top: 1px solid var\(--color-border\);/);
  assert.doesNotMatch(settings, /grid-template-columns/);
  assert.match(settings, /\.llmPage > \.notice \{/);

  // 用量：8 列表格列宽与容器内横向滚动不改，只归零面板内部重复内边距
  assert.doesNotMatch(usage, /usageDataTable/);
  assert.match(usage, /\.signalLogMinimalPanelHeader \{\s*padding-left: 0;[\s\S]*?background: transparent;/);
  assert.match(usage, /\.signalLogTableWrap,[\s\S]*?padding-right: 0;/);

  // 详情：涨跌语义强调卡片完整保留，只收敛外部分节
  assert.doesNotMatch(detail, /\.signalDetailHero\s*\{/);
  assert.match(detail, /\.signalDetailSummary \{[\s\S]*?border-bottom: 1px solid var\(--color-border\);/);
  // 六列汇总在窄档重排，长策略名、合约与时间不再被 ellipsis 吞掉
  assert.match(detail, /@media \(max-width: 1200px\) \{[\s\S]*?grid-template-columns: repeat\(2, minmax\(0, 1fr\)\);/);
  assert.match(detail, /@media \(max-width: 767px\) \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\);/);
});

test("the design guide records the completed fourth convergence step", () => {
  const guidelines = readFileSync(new URL("../../docs/frontend-design-guidelines.md", import.meta.url), "utf8");
  assert.match(guidelines, /第 4 步长尾页面收尾/);
  assert.match(guidelines, /第 8 节四步收敛全部完成/);
  tailMigrationBlocks.forEach(({ marker }) => {
    assert.ok(styles.includes(marker), `${marker} missing from styles`);
  });
});

test("the default landing page joins the ledger shell without losing radar semantics", () => {
  const marker = "账本式版式迁移 · 第 5 步：默认落地页 · 合约雷达";
  assert.ok(styles.includes(marker), "landing page migration block missing");
  const start = styles.indexOf(marker);
  const rest = styles.slice(start + 1);
  const next = rest.search(/\/\* -+ 账本式版式迁移 · /);
  const block = next === -1 ? styles.slice(start) : styles.slice(start, start + 1 + next);

  // 单一纸面、贯穿全页的对齐轴、三档降级与矮屏让路
  assert.match(block, /\.radarPage\.radarPageCompact \{\s*gap: 0;\s*padding: 0;[\s\S]*?background: var\(--color-surface\);/);
  assert.match(block, /padding-left: var\(--space-7\);\s*padding-right: var\(--space-7\);/);
  assert.match(block, /> \.notice \{[\s\S]*?margin-left: var\(--space-7\);/);
  assert.match(block, /border-bottom: 1px solid var\(--color-border\);/);
  assert.match(block, /@media \(max-width: 1200px\) \{[\s\S]*?padding-left: var\(--space-5\);/);
  assert.match(block, /@media \(max-width: 767px\) \{[\s\S]*?padding-left: var\(--space-4\);/);
  assert.match(block, /@media \(min-width: 1201px\) and \(max-height: 719px\)/);

  // 候选 / 详情两栏：并排一条竖线，≤1200 转纵向改横线，列宽与栅格比例不改
  assert.match(block, /\.radarListPanel \{\s*border-right: 1px solid var\(--color-border\);/);
  assert.match(block, /@media \(max-width: 1200px\) \{[\s\S]*?border-bottom: 1px solid var\(--color-border\);/);
  assert.doesNotMatch(block, /grid-template-columns/);

  // 涨跌 / 风险语义色、分析面板语义底色与选中标记都不被抹
  assert.doesNotMatch(block, /\.radarAnalysisPanel \{[^}]*(?:background|box-shadow):/);
  assert.doesNotMatch(block, /\.radarRowDir|\.radarScore \{[^}]*color:/);
  assert.match(block, /border-left: 3px solid transparent;/);
  assert.match(block, /\.radarRow\.selected \{\s*border-left-color: var\(--color-primary\);/);
  assert.match(block, /text-align: right;/);
  assert.match(block, /@media \(max-width: 767px\) \{[\s\S]*?text-align: left;/);

  // 只写 scoped 选择器，不引入硬编码颜色或任意间距，也不外溢到其它页面
  assert.doesNotMatch(block, /#[0-9a-fA-F]{3,8}\b/);
  assert.doesNotMatch(block, /^\s+(?:padding|margin|gap|font-size|border-radius)(?:-[a-z]+)?:\s*\d+px\b/m);
  assert.doesNotMatch(block, /^\s*\.(radarControls|radarLayout|panelHeader|notice|radarRow)\s*\{/m);
  assert.doesNotMatch(block, /\.(marketChartMain|marketAiMain|positionsPage|announcementsPage|llmPage|usagePage|usTimelinePage)\b/);
});

test("the design guide records the fifth step for the default landing page", () => {
  const guidelines = readFileSync(new URL("../../docs/frontend-design-guidelines.md", import.meta.url), "utf8");
  assert.match(guidelines, /第 5 步：默认落地页收敛/);
  assert.match(guidelines, /5\. 默认落地页：合约雷达/);
  assert.match(guidelines, /不改默认路由、不动 `main\.tsx`/);
  assert.ok(styles.includes("账本式版式迁移 · 第 5 步：默认落地页 · 合约雷达"));
});
