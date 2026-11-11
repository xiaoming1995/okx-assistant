import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");

test("market announcements are wired into market routing and tabs", () => {
  assert.match(source, /type MarketTab = "radar" \| "chart" \| "aiOutlook" \| "aiRecords" \| "stats" \| "announcements"/);
  assert.match(source, /parts\[1\] === "announcements"[\s\S]*?\? "announcements"/);
  assert.match(source, /key: "announcements"/);
  assert.match(source, /label: "公告"/);
  assert.match(source, /<AnnouncementsPage \/>/);
});

test("announcement page calls backend proxy endpoints", () => {
  assert.match(source, /function AnnouncementsPage/);
  assert.match(source, /fetch\(`\$\{API_BASE\}\/api\/announcements\/types`\)/);
  assert.match(source, /fetch\(`\$\{API_BASE\}\/api\/announcements\?\$\{params\.toString\(\)\}`\)/);
  assert.match(source, /params\.set\("annType", selectedType\)/);
  assert.match(source, /params\.set\("force", "true"\)/);
  assert.match(source, /language: "zh-CN"/);
});

test("announcement page displays publish times, links, and cache warnings", () => {
  assert.match(source, /announcementTypeLabel/);
  assert.match(source, /formatTime\(item\.businessPTime\)/);
  assert.match(source, /formatTime\(item\.pTime\)/);
  assert.match(source, /item\.url/);
  assert.match(source, /target="_blank"/);
  assert.match(source, /payload\?\.warning/);
  assert.match(source, /typesPayload\?\.warning/);
  assert.match(source, /announcement-types-default/);
  assert.match(source, /sourceLabel\(payload\?\.source \?\? typesPayload\?\.source\)/);
});

test("announcement category list keeps API enum values out of visible labels", () => {
  assert.match(source, /title=\{item\.annType \? `\$\{item\.annTypeDesc\} \(\$\{item\.annType\}\)` : item\.annTypeDesc\}/);
  assert.doesNotMatch(source, /<small>\{item\.annType\}<\/small>/);
  assert.doesNotMatch(source, /<small>all<\/small>/);
});
