## 1. Readable Report Data Model

- [x] 1.1 Inspect the current AI report response and define frontend-only helpers that turn summary, evidence, source, and warning fields into bounded reader-facing content.
- [x] 1.2 Translate recognized range, moving-average, volume, price, timestamp, and percentage evidence into Chinese labels and formatted values, with a safe fallback for unknown evidence.
- [x] 1.3 Classify snapshot reliability separately from supplementary macro/source degradation, including compact warning copy and inspectable detail.

## 2. AI Report Information Architecture

- [x] 2.1 Replace the equal-height four-card primary grid with a content-sized conclusion and evidence flow that exposes no more than three primary evidence items.
- [x] 2.2 Present observation/reassessment conditions and report-versus-chart freshness as readable secondary actions without automatic analysis.
- [x] 2.3 Move source metadata and external degradation details into a compact secondary section; preserve the read-only boundary and meaningful loading, error, cache, and incomplete states.
- [x] 2.4 Update desktop and narrow-width styles to eliminate horizontal clipping, raw-field overflow, and oversized unused card areas.

## 3. Verification

- [x] 3.1 Update frontend tests to assert Chinese evidence formatting, primary-card hierarchy, secondary warning behavior, and the manual-trigger boundary.
- [x] 3.2 Run frontend tests and production build, strict OpenSpec validation, and the relevant backend tests.
- [x] 3.3 Verify a rendered report in the browser on desktop and narrow width, distinguishing a usable chart report from external supplementary-data degradation.
