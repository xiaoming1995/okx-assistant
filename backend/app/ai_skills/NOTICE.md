# OKX Market Reading Profile attribution

The application-owned `okx-market-reading` Profile is a compact, read-only
adaptation of the capability boundary described by OKX's `okx-cex-market`
Skill. It does not vendor, install, invoke, or download the upstream `okx`
CLI or the upstream Skill document at runtime.

- Upstream repository: `https://github.com/okx/agent-skills`
- Upstream file: `skills/okx-cex-market/SKILL.md`
- Reviewed upstream version: `1.4.8`
- Reviewed upstream commit: `9c180cc1e9911a1ca44c0df5cc7509dba5bb7697`
- License: MIT

The local Profile permits only the dashboard's existing server-validated public
market evidence and prohibits account, trading, bot, credential, shell, and
CLI execution capabilities.
