import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const packageJson = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const theme = readFileSync(new URL("./mantineTheme.ts", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("frontend uses one versioned Mantine UI foundation without a runtime component CDN", () => {
  assert.match(packageJson.dependencies["@mantine/core"], /^\^9\./);
  assert.match(packageJson.dependencies["@mantine/hooks"], /^\^9\./);
  assert.match(packageJson.dependencies["@mantine/notifications"], /^\^9\./);
  assert.match(packageJson.dependencies["@mantine/dates"], /^\^9\./);
  for (const packageName of ["antd", "@mui/material", "@chakra-ui/react", "radix-ui"]) {
    assert.equal(packageJson.dependencies[packageName], undefined, `${packageName} must not become a second general-purpose UI library`);
  }
  assert.doesNotMatch(source, /https?:\/\/[^"']+(?:mantine|antd|material-ui|chakra)[^"']*/i);
  assert.match(source, /<MantineProvider theme=\{mantineTheme\}/);
  assert.match(source, /<Notifications position="bottom-right" limit=\{3\}/);
});

test("functional icons use one Mantine-compatible Phosphor set", () => {
  assert.ok(packageJson.dependencies["@phosphor-icons/react"]);
  assert.equal(packageJson.dependencies["lucide-react"], undefined);
  assert.match(source, /from "@phosphor-icons\/react"/);
  assert.doesNotMatch(source, /from "lucide-react"/);
  assert.match(source, /<IconContext\.Provider value=\{\{ weight: "regular", "aria-hidden": true \}\}>/);
  assert.match(source, /StarIcon as Star/);
  assert.match(source, /<Star size=\{16\} weight=\{item\.watched \? "fill" : "regular"\} \/>/);
  assert.match(source, /<ActionIcon\s+type="button"\s+className="watchButton"[\s\S]*?aria-label=/);
});

test("Mantine theme preserves the dashboard compact simple-tool contract", () => {
  assert.match(theme, /primaryColor: "workspace"/);
  assert.match(theme, /radius: \{ xs: "4px", sm: "8px"/);
  assert.match(theme, /spacing: \{ xs: "4px", sm: "8px", md: "12px", lg: "16px", xl: "24px" \}/);
  assert.match(theme, /fontFamilyMonospace/);
  assert.match(theme, /focusRing: "auto"/);
  assert.match(theme, /respectReducedMotion: true/);
  for (const component of ["Button", "ActionIcon", "TextInput", "Select", "Tabs", "Badge", "Alert", "Paper", "Menu", "Popover", "Modal", "Drawer", "Skeleton", "Table"]) {
    assert.match(theme, new RegExp(`\\n    ${component}: \\{`));
  }
});

test("shared shell, feedback, and market rail use Mantine patterns", () => {
  assert.match(source, /<AppShell header=\{\{ height: \{ base: 96, sm: 60 \} \}\}/);
  assert.match(source, /<Tabs[\s\S]*?aria-label="二级导航"/);
  assert.match(source, /<Alert[\s\S]*?role=\{tone === "danger" \? "alert" : "status"\}/);
  assert.match(source, /<Loader size="xs"/);
  assert.match(source, /<Skeleton className="dataLoadingSkeletonLine"/);
  assert.match(source, /<TextInput[\s\S]*?placeholder="搜索 BTC \/ ETH \/ USDT"/);
  assert.match(source, /<SegmentedControl[\s\S]*?aria-label="常用合约范围"/);
  assert.match(source, /<Menu withinPortal position="bottom-start">/);
  assert.match(source, /<UnstyledButton\s+type="button"\s+className="instrumentMain"/);
  assert.match(source, /<ActionIcon\s+type="button"\s+className="watchButton"/);
  assert.match(source, /<SegmentedControl\s+className="bars"\s+aria-label="K线周期"/);
  assert.match(source, /<Badge className=\{`statusPill \$\{tickerRealtime\.connected/);
  assert.match(source, /function PageHeader\(/);
  assert.doesNotMatch(source, /<(?:div|header) className="workspaceHeader"/);
  assert.match(styles, /\.workspaceHeader \{\s*display: flex;\s*flex: 0 0 auto;/);
  for (const title of ["行情图表", "交易数据", "OKX 公告", "OKX 交易环境", "自动交易策略", "LLM 信号分析", "LLM Token 用量"]) {
    assert.match(source, new RegExp(`<PageHeader[^>]+title="${title}"`));
  }
  assert.match(source, /function DataTable\(/);
  assert.match(source, /function SelectableTableRow\([\s\S]*?<Table\.Tr[\s\S]*?tabIndex=\{0\}[\s\S]*?event\.key !== "Enter" && event\.key !== " "/);
  assert.match(source, /<SelectableTableRow key=\{signal\.id\}/);
  assert.match(source, /<SelectableTableRow onSelect=\{\(\) => setSelectedUsageId/);
  assert.match(source, /function EmptyState\([\s\S]*?<Paper className=\{`emptyRow/);
  assert.doesNotMatch(source, /<div className="emptyRow/);
  assert.match(source, /<EmptyState className="radarListEmpty">/);
  assert.match(source, /<EmptyState className="radarDetailEmpty">/);
  assert.match(source, /<Badge className=\{`signalLogInlineChip/);
  assert.match(source, /<Badge className=\{`signalLogActionTag/);
  assert.doesNotMatch(source, /<span className=\{?`?"?(?:statusPill|signalLogInlineChip|signalLogActionTag|signalLogDecisionTag|cleanTag)/);
  assert.match(source, /function SegmentedField\([\s\S]*?<SegmentedControl/);
  assert.match(source, /<DataTable className="minimalDataTable positionDataTable">/);
  assert.match(source, /<DataTable className="orderHistoryTable">/);
  assert.doesNotMatch(source, /className="orderRow/);
  assert.match(source, /<\/DataTable>\s*\{orderEvents\.length === 0 \? <EmptyState>/);
});

test("visible controls and trade confirmations use the shared UI foundation", () => {
  assert.doesNotMatch(source, /<(?:button|select|textarea)\b/);
  assert.doesNotMatch(source, /<input\b/);
  assert.match(source, /<DateInput className="usTimelineDateControl"/);
  assert.match(source, /<DatesProvider settings=\{\{ locale: "zh-cn", firstDayOfWeek: 1 \}\}/);
  assert.doesNotMatch(source, /type="date"/);
  assert.doesNotMatch(styles, /\.usTimeline(?:MonthPicker|Today|DateInput)\b/);
  assert.doesNotMatch(source, /<(?:details|summary)\b/);
  assert.match(source, /function Disclosure\([\s\S]*?<Collapse expanded=\{opened\}>/);
  assert.match(source, /<Popover\.Dropdown><SegmentedControl className="usTimelineFilterGroup" aria-label="事件状态"/);
  assert.doesNotMatch(source, /<span className=\{?`?"?statusPill/);
  assert.doesNotMatch(source, /window\.confirm\(/);
  assert.match(source, /<ConfirmActionProvider><App \/><\/ConfirmActionProvider>/);
  assert.match(source, /<Modal[\s\S]*?closeOnClickOutside=\{false\}/);
  assert.match(source, /await confirmAction\(`确认提交平仓订单/);
  assert.match(source, /await confirmAction\(`确认提交 \$\{targetLabel\}订单/);
});

test("padded Mantine panels retain their stylesheet insets and centered summary content", () => {
  const paperTags = [...source.matchAll(/<Paper\b[^>]*>/g)].map(([tag]) => tag);
  for (const panel of [
    "contractHero", "marketAiOutlookPanel", "tradingStatsPanel", "tradingStatsDetail",
    "radarControls", "radarAnalysisPanel", "radarDetailPanel"
  ]) {
    const matchingTags = paperTags.filter((tag) => tag.includes(panel));
    assert.ok(matchingTags.length > 0, `${panel} must render through Paper`);
    for (const tag of matchingTags) {
      assert.doesNotMatch(tag, /\bp=\{0\}/, `${panel} must not override its CSS padding`);
    }
  }
  assert.match(styles, /\.contractTitle \{\s*display: flex;\s*flex-direction: column;\s*justify-content: center;/);
  assert.match(styles, /\.miniMetric \{\s*min-width: 0;\s*display: flex;\s*flex-direction: column;\s*justify-content: center;/);
});

test("compact controls and semantic feedback retain the shared accessibility contract", () => {
  for (const token of ["--control-height-sm: 28px", "--control-height: 34px", "--control-height-lg: 40px"]) {
    assert.ok(styles.includes(token), `${token} must remain defined`);
  }
  assert.match(source, /function Notice\([\s\S]*?<Alert[\s\S]*?role=\{tone === "danger" \? "alert" : "status"\}/);
  assert.match(source, /function DataLoadingState\([\s\S]*?role="status" aria-live="polite"/);
  assert.match(source, /function EmptyState\([\s\S]*?role="status"/);
  assert.match(source, /<Badge className=\{`signalLogDecisionTag/);
  assert.match(styles, /\[tabindex\]:focus-visible\s*\{[\s\S]*?box-shadow: var\(--focus-ring\)/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\)[\s\S]*?\.dataLoadingSkeletonLine\s*\{\s*animation: none;/);
});

test("retained refresh and dense row selection do not erase existing information", () => {
  assert.match(source, /chartLoading && candles\.length > 0 \? <DataLoadingState label="K线快照更新中，正在保留当前图表"/);
  assert.match(source, /loading && payload \? <DataLoadingState label="公告列表更新中，已保留当前内容"/);
  assert.match(source, /accountRefreshing && !accountInitialLoading \? <DataLoadingState label="账户数据更新中，已保留当前内容"/);
  assert.match(source, /function SelectableTableRow\([\s\S]*?aria-selected=\{selected\}[\s\S]*?event\.key !== "Enter" && event\.key !== " "/);
  assert.match(styles, /\.minimalDataTable tbody tr\[aria-selected="true"\]\s*\{\s*background: var\(--color-bg-soft\);\s*box-shadow: inset 3px 0 0 var\(--color-primary\)/);
});

test("obsolete route-local control and card selectors stay retired", () => {
  for (const obsolete of ["usageRow", "usageDetailHero", "signalLogItem", "signalLogOpen", "strategyCard", "strategyTableRow", "positionRow", "assetRow", "instrumentControlPopover", "marketAiObservationLevelGrid"]) {
    assert.doesNotMatch(styles, new RegExp(`\\.${obsolete}\\b`), `${obsolete} should not return after the Mantine migration`);
  }
});
