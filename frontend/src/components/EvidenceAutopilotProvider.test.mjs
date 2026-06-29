import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const providerPath = path.join(here, "..", "lib", "evidenceAutopilotProvider.ts");

assert.equal(fs.existsSync(providerPath), true, "provider contract module should exist");

function loadTsModule(source, requireMap = {}) {
  const output = ts.transpileModule(source, {
    compilerOptions: {
      esModuleInterop: true,
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (requireMap[specifier]) return requireMap[specifier];
    throw new Error(`Unexpected require: ${specifier}`);
  };
  new Function("require", "module", "exports", output)(localRequire, module, module.exports);
  return module.exports;
}

const provider = loadTsModule(fs.readFileSync(providerPath, "utf8"));

assert.equal(typeof provider.buildEvidenceAutopilotProviderRequest, "function");
assert.equal(typeof provider.buildEvidenceAutopilotOperatorReviewTask, "function");
assert.equal(typeof provider.isOperatorOnlyChannel, "function");

const searchTask = {
  taskId: "official-plan-charter",
  title: "官方招生计划与章程核验",
  channel: "official_pdf",
  query: "广东 2026 华南理工 智能制造 招生章程 PDF",
  requiredFields: ["来源链接", "发布日期", "原文摘录"],
  priority: "P0",
  complianceBoundary: "仅检索公开网页、公开 PDF 和可访问官方材料。",
};

const request = provider.buildEvidenceAutopilotProviderRequest({
  requestId: "req-official-1",
  targetLabel: "广东 2026 华南理工示例校 智能制造与数据工程",
  task: searchTask,
  maxResults: 3,
});

assert.deepEqual(request, {
  requestId: "req-official-1",
  taskId: "official-plan-charter",
  targetLabel: "广东 2026 华南理工示例校 智能制造与数据工程",
  channel: "official_pdf",
  query: "广东 2026 华南理工 智能制造 招生章程 PDF",
  requiredFields: ["来源链接", "发布日期", "原文摘录"],
  maxResults: 3,
});

const fakePublicProvider = {
  id: "snapshot-public",
  async search(providerRequest) {
    assert.equal(provider.isOperatorOnlyChannel(providerRequest.channel), false);
    return [
      {
        requestId: providerRequest.requestId,
        taskId: providerRequest.taskId,
        sourceTitle: "华南理工大学本科招生章程",
        sourceUrl: "https://example.edu/admission.pdf",
        sourceType: "official",
        excerpt: "智能制造与数据工程专业组计划数、选科要求与校区安排。",
        capturedAt: "2026-06-23T00:00:00.000Z",
        confidence: "high",
      },
    ];
  },
};

const [capture] = await fakePublicProvider.search(request);
assert.equal(capture.taskId, request.taskId);
assert.equal(capture.sourceType, "official");
assert.equal(capture.confidence, "high");
assert.equal(capture.excerpt.includes("专业组计划数"), true);
assert.equal(capture.sourceUrl.startsWith("https://"), true);

const operatorRequest = provider.buildEvidenceAutopilotProviderRequest({
  requestId: "req-wechat-1",
  targetLabel: request.targetLabel,
  task: {
    ...searchTask,
    taskId: "wechat-public-account",
    channel: "wechat_operator",
    query: "华南理工 智能制造 学院公众号 本科生 项目",
  },
});
const reviewTask = provider.buildEvidenceAutopilotOperatorReviewTask(operatorRequest);

assert.equal(provider.isOperatorOnlyChannel(operatorRequest.channel), true);
assert.equal(reviewTask.reviewOnly, true);
assert.equal(reviewTask.taskId, "wechat-public-account");
assert.equal(reviewTask.channel, "wechat_operator");
assert.equal(reviewTask.reason.includes("人工"), true);
assert.equal("status" in reviewTask, false, "operator review tasks must not masquerade as verified evidence");
assert.equal("excerpt" in reviewTask, false, "operator review tasks need captured excerpts before evidence promotion");

console.log("Evidence Autopilot provider contract test passed");
