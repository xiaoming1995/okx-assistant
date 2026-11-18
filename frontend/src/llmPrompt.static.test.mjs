import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const source = readFileSync(new URL("./main.tsx", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const backend = readFileSync(new URL("../../backend/app/main.py", import.meta.url), "utf8").replace(/\r\n/g, "\n");

const promptStart = source.indexOf("const defaultLlmSystemPrompt = [");
const promptEnd = source.indexOf("].join(\"\\n\");", promptStart);
assert.ok(promptStart >= 0 && promptEnd > promptStart, "should locate defaultLlmSystemPrompt source range");
const promptBlock = source.slice(promptStart, promptEnd);

test("frontend default system prompt carries the v3 market-first framework", () => {
  assert.match(promptBlock, /OKX 永续合约的交易信号分析师/);
  assert.match(promptBlock, /【分析框架】/);
  assert.match(promptBlock, /0\) 市场环境/);
  assert.match(promptBlock, /market_context/);
  assert.match(promptBlock, /risk-on\/mixed\/risk-off/);
  assert.match(promptBlock, /MA5\/MA20\/MA60/);
  assert.match(promptBlock, /量价配合/);
  assert.match(promptBlock, /【决策原则】/);
  assert.match(promptBlock, /环境优先/);
  assert.match(promptBlock, /赛道共振/);
  assert.match(promptBlock, /90 以上.*70-89.*50-69/s);
  assert.match(promptBlock, /【输出纪律】/);
  assert.match(promptBlock, /可验证的失效条件/);
});

test("backend prompt version and migration stay in place", () => {
  assert.match(backend, /LLM_PROMPT_VERSION = "signal-analysis-v3"/);
  assert.match(backend, /PREVIOUS_V2_LLM_SYSTEM_PROMPT = \(/);
  assert.match(backend, /LEGACY_LLM_SYSTEM_PROMPT, PREVIOUS_LLM_SYSTEM_PROMPT, PREVIOUS_V2_LLM_SYSTEM_PROMPT/);
  assert.match(backend, /"decision_guide": \[/);
  assert.match(backend, /证据充分度/);
  assert.match(backend, /含数值/);
});

test("user prompt injects market_context and market-first decision guide", () => {
  assert.match(backend, /"market_context": market_context_brief\(cached_market_context\(\)\)/);
  const guideStart = backend.indexOf('"decision_guide": [');
  const guideEnd = backend.indexOf('"expected_json_schema": {', guideStart);
  const guide = backend.slice(guideStart, guideEnd);
  assert.match(guide, /第 0 步定环境/);
  assert.match(guide, /market_context/);
  assert.match(guide, /趋势结构/);
  assert.match(guide, /动量与位置/);
  assert.match(guide, /量价/);
  assert.match(guide, /sentiment/);
  assert.match(guide, /环境与个币冲突/);
});
