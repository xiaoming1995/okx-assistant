import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("shared frontend foundation exposes the documented simple-workbench tokens", () => {
  assert.match(styles, /--space-1: 4px;[\s\S]*?--space-2: 8px;[\s\S]*?--space-3: 12px;[\s\S]*?--space-4: 16px;[\s\S]*?--space-5: 24px;[\s\S]*?--space-6: 32px;[\s\S]*?--space-7: 48px;/);
  assert.match(styles, /--control-height-sm: 28px;[\s\S]*?--control-height: 34px;[\s\S]*?--control-height-lg: 40px;/);
  assert.match(styles, /--motion-fast: 120ms;[\s\S]*?--motion-standard: 160ms;[\s\S]*?--z-popover: 12;/);
  assert.match(styles, /--text: var\(--color-text\);[\s\S]*?--panel: var\(--color-surface-muted\);[\s\S]*?--warning: var\(--color-warning\);/);
  assert.match(styles, /\.appShell \{[\s\S]*?background: var\(--color-bg\);/);
});

test("shared controls have restrained motion and keyboard feedback", () => {
  assert.match(styles, /button,[\s\S]*?\.disclosureTrigger \{[\s\S]*?transition:[\s\S]*?var\(--motion-fast\)/);
  assert.match(styles, /button:not\(:disabled\):active,[\s\S]*?transform: translateY\(1px\);/);
  assert.match(styles, /\.disclosureTrigger:focus-visible,[\s\S]*?box-shadow: var\(--focus-ring\);/);
  assert.match(styles, /@media \(prefers-reduced-motion: reduce\) \{[\s\S]*?transition-duration: 0\.01ms !important;/);
});

test("navigation and date selection expose their current state", () => {
  const sectionTabsSource = source.slice(source.indexOf("function SectionTabs"), source.indexOf("function App()"));
  assert.match(sectionTabsSource, /aria-current=\{item\.active \? "page" : undefined\}/);
  assert.match(source, /aria-current=\{section === "market" \? "page" : undefined\}/);
  const timelineSource = source.slice(source.indexOf("function UsMarketTimelinePage"), source.indexOf("function AnnouncementsPage"));
  assert.match(timelineSource, /aria-pressed=\{item === date\}/);
});

test("timeline overrides use the shared token vocabulary at normal and narrow widths", () => {
  assert.match(styles, /\.usTimelinePage \{\s*padding: var\(--space-5\) var\(--space-4\) var\(--space-7\);[\s\S]*?background: var\(--color-surface\);/);
  assert.match(styles, /\.usTimelineFilterGroup button \{[\s\S]*?min-height: var\(--control-height\);[\s\S]*?padding: 0 var\(--space-3\);/);
  assert.match(styles, /\.usEventCard > div \{[\s\S]*?border-radius: var\(--radius-panel\);[\s\S]*?padding: var\(--space-3\);/);
  assert.match(styles, /@media \(max-width: 680px\) \{[\s\S]*?\.usTimelinePage \{\s*padding: var\(--space-3\) var\(--space-4\) var\(--space-6\);/);
});
