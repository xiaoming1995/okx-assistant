import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const styles = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

test("narrow layouts allow radar page content to flow instead of clipping", () => {
  const narrowLayoutRule = /@media \(max-width: 1200px\) \{[\s\S]*?\.announcementsPage,\s*\.radarPage \{[\s\S]*?overflow: visible;/;
  assert.match(styles, narrowLayoutRule);
});

test("strategy filters collapse with the same specificity as their desktop rule", () => {
  const tabletRule = /@media \(max-width: 1200px\) \{[\s\S]*?\.strategiesPage \.signalLogMinimalControls,[\s\S]*?grid-template-columns: 1fr;/;
  const mobileRule = /@media \(max-width: 760px\) \{[\s\S]*?\.strategiesPage \.signalLogMinimalControls \{[\s\S]*?grid-template-columns: 1fr;/;
  assert.match(styles, tabletRule);
  assert.match(styles, mobileRule);
});

test("strategy table keeps a stable horizontal scroll width on small screens", () => {
  assert.match(styles, /\.strategyDataTable \{\s*min-width: 980px;\s*\}/);
  assert.match(styles, /\.signalLogTableWrap \{[\s\S]*?overflow: auto;/);
});
