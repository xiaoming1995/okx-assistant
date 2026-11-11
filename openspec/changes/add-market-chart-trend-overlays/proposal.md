## Why

当前行情图表已能可靠接收并聚焦近期 K 线，但蜡烛与成交量缺少趋势参照物；用户难以快速分辨价格相对短、中、长周期趋势的位置与转折。参考图所展示的 MA 叠加、当前价格锚点和区间极值，使价格波动的方向与幅度可以在一次浏览中读懂。

## What Changes

- 在行情图表主价格区域默认叠加 MA5、MA10、MA20 三条移动平均线，并以稳定、可区分的黄、玫红、青蓝颜色及同色图例表达。
- 将新合约或周期首次进入时的近期视图调整为约 48 根 K 线，完整已加载历史仍可拖动和缩放查看。
- 在图表可见区间提供当前价格锚点、当前未收盘 K 线的收线倒计时，以及最高价/最低价标注，帮助快速识别波动范围。
- 保持十字光标检查器与均线图例一致：未选中历史蜡烛时显示最新数据，选中历史蜡烛时显示该时间点的 OHLC 与可用均线值。
- 保持现有成交量同步、数据降级提示、手动查看历史不被实时推送打断、`最新`返回控制和 TradingView 归属链接。

## Capabilities

### New Capabilities

- `market-chart-trend-overlays`: 为只读市场 K 线提供可解释的移动平均趋势叠加、价格时间锚点、区间极值标注与近期视图阅读体验。

### Modified Capabilities

- None.

## Impact

- Affected frontend: `frontend/src/main.tsx`, `frontend/src/styles.css`, and focused market-chart tests.
- Uses the installed `lightweight-charts` line and candlestick series; no new backend route, persistence, market-data source, or third-party dependency is required.
- Maintains the market page as observational/read-only: no forecasts, automated signals, recommendations, order-entry controls, or position data are added.
