## 1. Profile Contract and Attribution

- [x] 1.1 Add a fixed, locally validated `okx-market-reading` Profile with pinned upstream attribution, MIT notice, allowed evidence, prohibited capabilities, and canonical content hash.
- [x] 1.2 Add focused backend tests proving Profile validation, stable metadata/hash, and the absence of CLI/runtime-download behavior.

## 2. AI Outlook Integration and Audit

- [x] 2.1 Compile the Profile into immutable AI outlook prompt context ahead of untrusted market and macro evidence, while retaining the existing JSON and fallback safeguards.
- [x] 2.2 Include Profile identity/version/hash in prompt and report cache identity, and attach `analysisProfile` metadata to normal, cached, and fallback responses.
- [x] 2.3 Persist Profile identity/version/hash with attempted AI outlook usage records through a database migration and database API update.
- [x] 2.4 Add backend coverage for prompt integration, cache invalidation, fallback provenance, and usage-record metadata.

## 3. AI Outlook Provenance UI

- [x] 3.1 Extend AI outlook response types and render compact, optional Profile provenance in the existing source/reference area without creating an execution control.
- [x] 3.2 Add static frontend coverage for Profile provenance, backwards compatibility, and retained-report refresh behavior.

## 4. Verification

- [x] 4.1 Run focused backend and frontend tests, the frontend production build, and strict OpenSpec validation.
- [x] 4.2 Verify the running AI outlook at desktop and narrow widths for first load, available Profile report, retained refresh, fallback/cache, disabled action, and keyboard focus states.
