import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

const ordersSource = () =>
  source.slice(source.indexOf("function OrdersPage("), source.indexOf("function strategyInstrumentLabel("));

test("trade page is a workbench: ticket + live positions + pending orders in one view", () => {
  assert.match(source, /function TradingPage/);
  assert.doesNotMatch(source, /title="未成交订单"/);

  const tradeSource = source.slice(
    source.indexOf("function TradingPage("),
    source.indexOf("function OrdersPage(")
  );
  // 下单、持仓、挂单、账户概览集中在交易页一屏可见
  assert.match(tradeSource, /className="tradeWorkbenchOverview" aria-label="交易概览"/);
  assert.match(tradeSource, /className="tradePage tradePageWorkbench"/);
  assert.match(tradeSource, /className="tradeGrid tradeGridWorkbench"/);
  assert.match(tradeSource, /className="tradeWorkbenchSide"/);
  assert.match(tradeSource, /aria-label="当前持仓"/);
  assert.match(tradeSource, /aria-label="当前挂单"/);
  // 历史订单仍在独立订单页
  assert.doesNotMatch(tradeSource, /title="本地订单记录"/);
  assert.match(tradeSource, /onOpenOrders/);
});

test("order records live on their own page with its own data loading", () => {
  const orders = ordersSource();
  assert.match(orders, /eyebrow="订单"/);
  assert.match(orders, /title="订单记录"/);
  assert.match(orders, /title="本地订单记录"/);
  assert.match(orders, /new URLSearchParams\(\{[\s\S]*?limit: String\(orderPageSize\),[\s\S]*?offset: String/);
  assert.match(orders, /fetch\(`\$\{API_BASE\}\/api\/trading\/orders\?\$\{params\.toString\(\)\}`\)/);
  assert.match(orders, /payload\.paging/);
  assert.match(orders, /topics: \["orders"\]/);
  assert.match(orders, /switchEnvironment/);
  assert.match(orders, /onOpenTrade/);
});

test("trade grid keeps base two-column layout and stacks the workbench on narrow screens", () => {
  assert.match(styles, /\.tradeGrid \{[\s\S]*?grid-template-columns: minmax\(310px, 360px\) minmax\(0, 1fr\);[\s\S]*?grid-template-rows: minmax\(0, 1fr\);/);
  // 工作台：左侧下单 + 右侧持仓/挂单两列，窄屏纵向堆叠
  assert.match(styles, /\.tradeGrid\.tradeGridWorkbench \{[\s\S]*?grid-template-columns: minmax\(340px, 440px\) minmax\(0, 1fr\);/);
  assert.match(styles, /@media \(max-width: 1200px\) \{[\s\S]*?\.tradeGrid\.tradeGridWorkbench \{[\s\S]*?grid-template-columns: 1fr;/);
});

test("trade page scrolls as a whole so the ticket shows every field", () => {
  // 整页滚动，取消下单面板内部滚动条：底部「提交/保存」字段不再被截断
  assert.match(styles, /\.tradePage\.tradePageWorkbench \{[\s\S]*?overflow-y: auto;/);
  assert.match(styles, /\.tradeGrid\.tradeGridWorkbench \{[\s\S]*?grid-template-rows: auto;/);
  assert.match(styles, /\.tradeGrid\.tradeGridWorkbench > \.tradeTicket \{[\s\S]*?overflow: visible;/);
  // 右侧列表仍限高，避免长列表拖长整页
  assert.match(styles, /\.workbenchTableWrap \{[\s\S]*?max-height: 320px;/);
});

test("trade ticket stays compact: single-line market facts, short leverage bar, collapsed extras", () => {
  // 合约概览压为可换行的单行，不再固定两列网格
  assert.match(styles, /\.tradeFacts \{[\s\S]*?display: flex;[\s\S]*?flex-wrap: wrap;/);
  // 杠杆信息块压到紧凑控件高度（≤34px）
  assert.match(styles, /\.leverageMeta \{[\s\S]*?min-height: 34px;/);
});

test("trade workbench ticket fits one screen: leverage presets in a single row and tightened spacing", () => {
  // 8 个杠杆预设由两行压成一行（工作台作用域），是省掉纵向滚动的关键
  assert.match(styles, /\.tradePageWorkbench \.leveragePresets \{[\s\S]*?grid-template-columns: repeat\(8, minmax\(0, 1fr\)\);/);
  // 工作台缩小各区块堆叠间距与内边距
  assert.match(styles, /\.tradePageWorkbench \.tradeTicket \{[\s\S]*?gap: 4px;[\s\S]*?padding: 8px;/);
  assert.match(styles, /\.tradePageWorkbench \.tradeTicketSection \{[\s\S]*?gap: 4px;[\s\S]*?padding-top: 4px;/);
  assert.match(styles, /\.tradePage\.tradePageWorkbench \{[\s\S]*?padding: 12px/);
  // 合约选择器与杠杆信息条压到紧凑高度
  assert.match(styles, /\.tradePageWorkbench \.contractPickerButton \{[\s\S]*?min-height: 42px;/);
  assert.match(styles, /\.tradePageWorkbench \.leverageMeta \{[\s\S]*?min-height: 28px;/);
  // 移除常驻的「正在读取…」整行提示，status 初始为空，避免它挤占面板高度把提交按钮顶出视口
  assert.doesNotMatch(source, /正在读取交易账户、杠杆与行情数据/);
  assert.match(source, /const \[status, setStatus\] = React\.useState\(""\);/);
});

test("compact ticket keeps collapsed extras (preserved from prior behavior)", () => {
  // 数量单位并入「更多选项」折叠区，默认收起；数量标签仍显示当前单位
  assert.match(source, /收起更多选项/);
  assert.match(source, /\{advancedOrderTypeSelected \? "高级类型已选" : visibleAdvancedOrderTypes \? "收起更多选项" : "更多选项"\}/);
  assert.match(source, /<span>数量（\{quantityLabel\}）<\/span>/);
  // 折叠按钮保留 aria-expanded，符合可访问性
  assert.match(source, /className="inlineToggleButton"[\s\S]*?aria-expanded=\{visibleAdvancedOrderTypes\}/);
});

test("segmented controls keep Mantine native flex layout so the selected block is not distorted", () => {
  // 变形根因：.segmentedButtons 曾用 display:grid 覆盖 Mantine root，破坏 indicator 绝对定位参照，
  // 导致选中白块比按钮格窄、右边缘斜切、底部悬空露出灰底。移除 grid 覆盖，恢复原生 flex。
  const segmentedBlock = styles.slice(styles.indexOf(".segmentedButtons {"), styles.indexOf(".segmentedButtons button,"));
  assert.doesNotMatch(segmentedBlock, /display: grid/);
  assert.match(segmentedBlock, /min-width: 0;/);
  // 工作台选中态用 --sc-color 语义色：默认绿、做空(sell)红
  assert.match(styles, /\.tradePageWorkbench \.segmentedButtons \{[\s\S]*?--sc-color: var\(--color-success-soft\);/);
  assert.match(styles, /\.tradePageWorkbench \.segmentedButtons\.sell \{[\s\S]*?--sc-color: var\(--color-danger-soft\);/);
  // 点击选项后隐藏 radio 获得焦点会给 label 加 2px 主色 outline，在紧凑按钮上像变形脏边；工作台内去掉。
  assert.match(styles, /\.tradePageWorkbench \.segmentedButtons \.mantine-SegmentedControl-label \{[\s\S]*?outline: none !important;/);
  // 去掉 Mantine 默认 4px 内边距，让选中块整格铺满、四边不留灰缝。
  assert.match(styles, /\.tradePageWorkbench \.segmentedButtons \{[\s\S]*?padding: 0;/);
  assert.match(styles, /\.tradePageWorkbench \.segmentedButtons \{[\s\S]*?--sc-shadow: none;/);
  // indicator 用方角铺满整格，由 root 的 overflow:hidden 裁出外框圆角；
  // 不能继承外框圆角，否则选中右格(做空)时左边缘出现半圆缺口、像贴片浮起，与选中左格不一致。
  assert.match(styles, /\.tradePageWorkbench \.segmentedButtons \.mantine-SegmentedControl-indicator \{[\s\S]*?border-radius: 0;/);
});

test("direction and order-type segmented buttons drop cramped icons, keep text and title", () => {
  // 交易方向/常用类型的 14px 图标在紧凑按钮里被挤成乱码符号，改为纯文字 + 悬浮说明
  const sideBlock = source.slice(source.indexOf("const sideOptions"), source.indexOf("const leveragePresetOptions"));
  assert.doesNotMatch(sideBlock, /icon:/);
  assert.match(sideBlock, /label: "做多", title: "买入开多"/);
  assert.match(sideBlock, /label: "做空", title: "卖出开空"/);
  assert.match(sideBlock, /label: "限价", title: "按指定价格挂单"/);
  assert.match(sideBlock, /label: "市价", title: "按市场价格立即提交"/);
  // SegmentedField 仍保留 icon 的可选渲染能力，供其它确需图标的场景使用
  assert.match(source, /\{item\.icon \? <span className="segmentedIcon">/);
});

test("trade ticket makes leverage contract context explicit and keeps advanced order types collapsed", () => {
  assert.match(source, /const leverageContext = `\$\{instId\.toUpperCase\(\)\} · \$\{leverageScope\}`/);
  assert.match(source, /aria-label="当前合约杠杆"/);
  assert.match(source, /账户当前 \{leverageLoading \? "读取中" : leverageSummary\}/);
  assert.match(source, /primaryOrderTypeOptions/);
  assert.match(source, /advancedOrderTypeOptions/);
  assert.match(source, /高级类型/);
});

test("order page exposes server-backed search, contract and origin filters, and pagination", () => {
  const orders = ordersSource();
  assert.match(orders, /const \[orderSearch, setOrderSearch\]/);
  assert.match(orders, /params\.set\("q", orderSearch\.trim\(\)\)/);
  assert.match(orders, /params\.set\("instId", orderInstId\)/);
  assert.match(orders, /params\.set\("action", orderActionFilter\)/);
  assert.match(orders, /params\.set\("state", orderStateFilter\)/);
  assert.match(orders, /params\.set\("origin", orderOriginFilter\)/);
  assert.match(orders, /搜索合约 \/ 订单号 \/ 错误信息/);
  assert.match(orders, /aria-label="订单合约"/);
  assert.match(orders, /全部合约/);
  assert.match(orders, /setOrderPageIndex\(\(value\) => Math\.min\(orderPageCount, value \+ 1\)\)/);
  assert.match(styles, /\.ordersPanelPage \.tradeOrderControls \{[\s\S]*?grid-template-columns: minmax\(200px, 1fr\)/);
  assert.match(styles, /@media \(max-width: 1200px\) \{[\s\S]*?\.tradeOrderControls,[\s\S]*?grid-template-columns: 1fr;/);
});

test("order page renders live pending orders with a guarded cancel action", () => {
  const orders = ordersSource();
  assert.match(orders, /const \[pendingOrders, setPendingOrders\]/);
  assert.match(orders, /order\.state === "live" \|\| order\.state === "partially_filled"/);
  assert.match(orders, /aria-label="当前挂单"/);
  assert.match(orders, /title="当前挂单"/);
  assert.match(orders, /function cancelPendingOrder|const cancelPendingOrder = async/);
  assert.match(orders, /api\/trading\/orders\/cancel/);
  assert.match(orders, /confirmAction/);
  assert.match(orders, /撤销 \$\{order\.instId/);
  assert.match(orders, /disabled=\{isCanceling \|\| switching\}/);
  assert.match(styles, /\.pendingOrdersPanel \{/);
});

test("workbench overview reuses the account snapshot and quick actions are guarded", () => {
  const tradeSource = source.slice(
    source.indexOf("function TradingPage("),
    source.indexOf("function OrdersPage(")
  );
  // 概览直接复用 /api/account 的 positions + summary，无额外接口
  assert.match(tradeSource, /workbenchPositions = React\.useMemo\([\s\S]*?tradingAccount\?\.positions \?\? \[\]/);
  assert.match(tradeSource, /workbenchTotalEquity[\s\S]*?firstMetric\(tradingAccount\.summary/);
  assert.match(tradeSource, /label="未实现盈亏"/);
  // 就地撤单/平仓都需要二次确认 + 环境隔离
  assert.match(tradeSource, /const cancelWorkbenchOrder = async[\s\S]*?confirmAction/);
  assert.match(tradeSource, /api\/trading\/orders\/cancel/);
  assert.match(tradeSource, /const quickClosePosition = async[\s\S]*?confirmAction/);
  assert.match(tradeSource, /api\/trading\/positions\/close/);
  assert.match(tradeSource, /disabled=\{!closeOrder \|\| !tradeEnabled \|\| isClosing\}/);
  assert.match(tradeSource, /disabled=\{isCanceling\}/);
});

test("all trading write requests carry an explicit environment", () => {
  const tradeSource = source.slice(
    source.indexOf("function TradingPage("),
    source.indexOf("function OrdersPage(")
  );
  const orders = ordersSource();
  const positionsStart = source.indexOf("const closeOrder = positionCloseOrder(position)");
  const positionsSource = source.slice(positionsStart, positionsStart + 3000);

  assert.match(tradeSource, /environment: activeEnvironment[\s\S]*?clOrdId/);
  assert.match(orders, /environment: activeEnvironment/);
  assert.match(positionsSource, /environment: activeEnvironment/);
});

test("manual order submit uses a reusable idempotency key and blocks re-entry", () => {
  const tradeSource = source.slice(
    source.indexOf("function TradingPage("),
    source.indexOf("function OrdersPage(")
  );
  assert.match(source, /function makeClientOrderId\(\)/);
  assert.match(source, /OKXQ/);
  assert.match(source, /\.slice\(0, 32\)/);
  assert.match(tradeSource, /const submitOrder = async[\s\S]*?if \(submitting\) return;/);
  assert.match(tradeSource, /pendingClOrdIdRef\.current/);
  assert.match(tradeSource, /clOrdId/);
  assert.match(tradeSource, /pendingClOrdIdRef\.current = "";/);
});

test("trading account refresh is deduplicated with request sequence and throttle", () => {
  const tradeSource = source.slice(
    source.indexOf("function TradingPage("),
    source.indexOf("function OrdersPage(")
  );
  // 账户刷新有 seq 防竞态 + 节流，避免 WS 事件风暴放大 /api/account 调用
  assert.match(source, /const ACCOUNT_REFRESH_MIN_MS = 1500;/);
  assert.match(tradeSource, /const accountRequestSeqRef = React\.useRef\(0\)/);
  assert.match(tradeSource, /const accountLastFetchRef = React\.useRef\(0\)/);
  assert.match(tradeSource, /const loadTradingAccount = React\.useCallback\(async \(force = false, skipThrottle = false\)/);
  assert.match(tradeSource, /force && !skipThrottle && now - accountLastFetchRef\.current < ACCOUNT_REFRESH_MIN_MS/);
  assert.match(tradeSource, /requestSeq === accountRequestSeqRef\.current\) setTradingAccount/);
  // 关键操作（切环境/杠杆）跳过节流；WS 事件刷新不重复调用
  assert.match(tradeSource, /await loadTradingAccount\(true, true\)/);
  assert.match(tradeSource, /payload\.topic === "account" \|\| payload\.topic === "positions"\) loadTradingAccount\(true\)/);
  // onEvent 中 account.update 分支只更新状态提示，不再触发第二次刷新
  const onEventAccount = tradeSource.slice(
    tradeSource.indexOf('payload.type === "account.update" || payload.type === "position.update"')
  );
  assert.doesNotMatch(onEventAccount.slice(0, 260), /loadTradingAccount/);
});
