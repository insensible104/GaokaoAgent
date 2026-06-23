import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const templatePath = path.join(here, "PathFinderReportTemplate.tsx");
const source = fs.readFileSync(templatePath, "utf8");

for (const token of [
  "DeepOpportunityReportPage",
  "buildDeepOpportunityCard",
  "exampleDeepOpportunityInput",
  "buildEvidenceAutopilotRun",
  "buildEvidenceAutopilotSnapshotProviderResults",
  "buildEvidenceAutopilotRealCaseProviderResults",
  "realCaseFixture.claimBoundary",
  "auditable opportunity hypothesis",
  "Real Case v0",
  "深度机会证据页",
  "Evidence Autopilot",
  "机会雷达",
  "P0 门槛",
  "反证命中",
  "短期录取",
  "中期升学",
  "长期职业",
  "sourceExcerpt",
  "量化定位",
  "科研资源",
  "师资与论文",
  "本科生可获得性",
  "真实就业",
  "升学路径",
  "反证与降权",
  "证据缺口",
  "下一步采集",
]) {
  assert(source.includes(token), `report template should include deep opportunity token: ${token}`);
}

console.log("PathFinder deep opportunity report smoke test passed");
