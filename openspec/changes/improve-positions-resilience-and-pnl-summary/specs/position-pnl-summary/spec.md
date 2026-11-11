## ADDED Requirements

### Requirement: Current open-position floating P&L is summarized
The positions page SHALL present an explicitly labeled “未实现盈亏汇总” calculated from the sum of numeric OKX `upl` values for currently open positions. It SHALL also show positive, negative, and zero-P&L position counts, total margin, total notional USD, and the snapshot freshness/source state.

#### Scenario: Open positions contain both gains and losses
- **WHEN** the account response contains open positions with positive, negative, and zero `upl` values
- **THEN** the summary shows their open-position aggregate and each count without including filtered-out closed positions or non-numeric values

#### Scenario: The table is filtered
- **WHEN** the user searches or filters the displayed positions table
- **THEN** the floating P&L summary continues to represent all current open positions rather than only visible rows

### Requirement: P&L sign is visually distinguishable
The positions page SHALL render positive floating P&L and returns in green with an explicit plus sign, negative values in red, and zero or unavailable values with neutral styling. Scoped P&L styles MUST take precedence over generic table typography.

#### Scenario: A row has positive floating P&L
- **WHEN** a position has positive numeric `upl` or `uplRatio`
- **THEN** its value is shown with a plus sign and positive visual treatment

#### Scenario: A row has negative or zero floating P&L
- **WHEN** a position has negative, zero, or unavailable floating P&L data
- **THEN** negative values are red, while zero or unavailable values use neutral visual treatment and are not presented as a gain
