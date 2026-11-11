## 1. Design-system foundation

- [x] 1.1 Audit the frontend stylesheet and markup against the saved design guide; identify shared token, legacy-variable, and accessibility gaps without changing market, account, trade, or automation behavior.
- [x] 1.2 Add the documented global spacing, sizing, layer, motion, and compatibility color tokens to the shared stylesheet.
- [x] 1.3 Normalize shared buttons, tabs, icon buttons, selectable rows, cards, popovers, and focus/active/reduced-motion behavior to the simple tool-oriented visual contract.

## 2. Page and responsive conformance

- [x] 2.1 Normalize shared page padding, workspace headers, panels, controls, and feedback surfaces while preserving compact market/trading density and existing workbench ownership.
- [x] 2.2 Repair the US market timeline's legacy visual variables and align its controls, cards, and responsive states with the global token vocabulary.
- [x] 2.3 Add small accessibility attributes or feedback affordances where existing interactive markup lacks the documented state semantics, without changing product behavior.

## 3. Verification

- [x] 3.1 Add focused static regression coverage for global design tokens, simple interaction rules, timeline compatibility, and responsive/accessibility contracts.
- [x] 3.2 Run the frontend test suite, production build, and strict OpenSpec validation; resolve issues introduced by this change.
- [x] 3.3 Verify representative market, AI outlook, trade, automation, account, and timeline pages at desktop and narrow widths, including loading/empty/error or cache, focus, selected, and disabled states where present.

## 4. AI outlook layout follow-up

- [x] 4.1 Keep the AI report title and description intact beside status and period controls; let the controls move predictably before the description is compressed.
- [x] 4.2 Prevent the responsive AI report header from shrinking beneath the following summary card, so all actions remain visible.
