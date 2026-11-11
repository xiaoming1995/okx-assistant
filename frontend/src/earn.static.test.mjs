import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8");

function sectionSource(start, end) {
  const startIndex = source.indexOf(start);
  const endIndex = source.indexOf(end);
  assert.notEqual(startIndex, -1, `missing ${start}`);
  assert.notEqual(endIndex, -1, `missing ${end}`);
  return source.slice(startIndex, endIndex);
}

test("account navigation exposes the on-chain earn workspace", () => {
  assert.match(source, /type AccountTab = "positions" \| "account" \| "earn"/);
  assert.match(source, /parts\[1\] === "earn"/);
  assert.match(source, /label: "链上赚币"/);
  assert.match(source, /<EarnPage \/>/);
  assert.match(source, /OKX On-chain Earn/);
});

test("earn page loads all read-only backend endpoints", () => {
  assert.match(source, /function EarnPage\(\)/);
  assert.match(source, /Promise\.allSettled/);
  assert.match(source, /protocolTypeFilter/);
  assert.match(source, /全部协议/);
  assert.match(source, /staking/);
  assert.match(source, /\/api\/earn\/offers/);
  assert.match(source, /\/api\/earn\/orders\/active/);
  assert.match(source, /\/api\/earn\/orders\/history/);
  assert.match(source, /\/api\/earn\/eth/);
  assert.match(source, /\/api\/earn\/sol/);
  assert.match(source, /force", "true"/);
});

test("earn page renders expected product, order, staking, and APY sections", () => {
  assert.match(source, /链上赚币项目/);
  assert.match(source, /活跃订单/);
  assert.match(source, /历史订单/);
  assert.match(source, /\$\{asset\} 质押/);
  assert.match(source, /earnInvestRangeText/);
  assert.match(source, /预估年化/);
  assert.match(source, /可投范围/);
  assert.match(source, /申购赎回记录/);
  assert.match(source, /APY 历史/);
});

test("earn page exposes section-scoped warning and empty states", () => {
  assert.match(source, /warnings\.slice\(0, 3\)/);
  assert.match(source, /offers\?\.configured === false/);
  assert.match(source, /activeOrders\?\.configured === false/);
  assert.match(source, /history\?\.configured === false/);
  assert.match(source, /data\?\.configured === false/);
  assert.match(source, /暂无符合条件的链上赚币项目/);
  assert.match(source, /暂无活跃链上赚币订单/);
  assert.match(source, /暂无链上赚币历史订单/);
});

test("Earn rejects failed responses, retains prior snapshots, and tolerates absent APY points", () => {
  assert.match(source, /const readEarnEndpoint = async \(url: string\) => \{[\s\S]*?if \(!response\.ok\) throw new Error\("链上赚币接口暂不可用"\)/);
  assert.match(source, /if \(offerResult\.status === "fulfilled"\) setOffers\(offerResult\.value\)/);
  assert.match(source, /if \(ethResult\.status === "fulfilled"\) setEth\(ethResult\.value\)/);
  assert.match(source, /failed === requests\.length \? hadSnapshot \? "更新失败，已保留现有内容" : "链上赚币数据暂不可用"/);
  assert.match(source, /const apyPoints = data\?\.apyPoints \?\? \[\]/);
  assert.match(source, /unavailable \? <EmptyState compact>质押年化数据暂不可用<\/EmptyState> : data && apyPoints\.length === 0/);
  assert.match(source, /!offers && loadError \? \([\s\S]*?链上赚币项目暂不可用/);
});

test("earn workspace stays read-only in the first version", () => {
  assert.match(source, /不提交申购、赎回或撤销请求/);
  assert.doesNotMatch(source, /\/api\/earn\/purchase/);
  assert.doesNotMatch(source, /\/api\/earn\/redeem/);
  assert.doesNotMatch(source, /\/api\/earn\/cancel/);
  assert.doesNotMatch(source, /确认申购|立即申购|确认赎回|自动申购|推荐申购|建议申购|强烈申购/);
});

test("earn data is not wired into radar, automation, or LLM action surfaces", () => {
  const radarSource = sectionSource("function ContractRadarPage", "function MarketPage");
  const automationSource = sectionSource("function CleanAutomationPage", "function StrategyListPage");
  const llmUsageSource = sectionSource("function LlmUsagePage", "function EarnPage");
  assert.doesNotMatch(radarSource, /\/api\/earn|EarnPage|链上赚币/);
  assert.doesNotMatch(automationSource, /\/api\/earn|EarnPage|链上赚币/);
  assert.doesNotMatch(llmUsageSource, /\/api\/earn|EarnPage|链上赚币/);
});
