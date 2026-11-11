## Context

The AI outlook reading area places the current conclusion beside chart evidence on desktop. Their outer grid row aligns, but their nested card content uses separate spacing and leaves the evidence module visually detached from the conclusion block.

## Goals / Non-Goals

**Goals:**

- Establish a shared desktop top edge and matched module height for the two primary reading modules.
- Make each module's header and body begin on predictable tracks while retaining all current content.
- Retain the narrow-screen single-column fallback.

**Non-Goals:**

- Change analysis wording, evidence selection, forecast logic, market data, or controls.
- Normalize text by clipping, truncating, or introducing artificial fixed heights that hide content.

## Decisions

- Use the existing reading grid as the shared alignment boundary and stretch both direct children. This directly governs the two modules that users compare.
- Use a flexible vertical module structure where a nested body fills available space. This preserves long copy while keeping short-copy modules visually balanced.
- Retain content-driven expansion beyond the baseline. A fixed card height was rejected because live analysis wording can vary.

## Risks / Trade-offs

- [Long content grows one module] → Preserve full content and let the shared grid row grow rather than truncating it.
- [Narrow screens cannot compare modules side by side] → Preserve the existing one-column media-query behavior.
