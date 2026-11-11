## Why

The readable AI market report now explains the current chart state clearly, but it no longer tells users what that state could imply over the next short interval. Users need a compact, traceable outlook that connects the current K-line snapshot to conditions worth watching, without presenting uncertain market movement as a guaranteed price prediction.

## What Changes

- Add a dedicated conditional forecast section for the next 15 minutes, next hour, and the current day when the AI response provides those horizons.
- Show each horizon as a concise direction, confidence, chart-based condition, and invalidation/reassessment cue.
- Keep the forecast bounded to the chart snapshot used for the report, clearly label it as an observation, and retain manual generation and read-only behavior.
- Preserve the compact current-conclusion and three-item chart-evidence flow; macro/source degradation remains secondary information.

## Capabilities

### New Capabilities

- `ai-outlook-conditional-forecast`: Present short-horizon, chart-grounded conditional forecasts in the manual AI market report.

### Modified Capabilities

<!-- No existing base capability specification covers the AI market report. -->

## Impact

- `frontend/src/main.tsx` AI market report rendering and its response-to-reader mapping helpers.
- `frontend/src/styles.css` forecast card layout and narrow-width behavior.
- `frontend/src/marketAiOutlook.static.test.mjs` presentation and safety-boundary coverage.
- No trading API, order execution, or automatic AI request behavior changes.
