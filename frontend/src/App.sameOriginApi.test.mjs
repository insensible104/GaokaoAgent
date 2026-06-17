import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, "App.tsx"), "utf8");
const deliverySource = fs.readFileSync(
  path.join(here, "components", "InternalDeliveryReview.tsx"),
  "utf8"
);
const portfolioSource = fs.readFileSync(
  path.join(here, "components", "DeliveryPortfolioReview.tsx"),
  "utf8"
);
const apiSource = fs.readFileSync(path.join(here, "lib", "api.ts"), "utf8");

for (const [name, source] of [
  ["App", appSource],
  ["InternalDeliveryReview", deliverySource],
  ["DeliveryPortfolioReview", portfolioSource],
]) {
  assert.match(
    source,
    /buildApiUrl\("/,
    `${name} should route API calls through the shared API URL helper`
  );
  assert.doesNotMatch(
    source,
    /: import\.meta\.env\.VITE_API_URL \|\| "http:\/\/localhost:8000";/,
    `${name} production build must not fall back to localhost`
  );
}

assert.match(apiSource, /import\.meta\.env\.VITE_API_URL/);
assert.match(apiSource, /if \(import\.meta\.env\.DEV\) return "http:\/\/localhost:8000";/);
assert.match(apiSource, /return "";/);

assert.doesNotMatch(
  appSource,
  /网络错误，请检查后端服务是否运行 \(http:\/\/localhost:8000\)/,
  "student-facing production errors should not prescribe a development-only host"
);

assert.match(
  appSource,
  /if \(admissionsOpportunityDemoRequested\)/,
  "dedicated admissions demo route should be public for the launch demo"
);

assert.match(
  appSource,
  /if \(externalPlanAuditDemoRequested\)/,
  "dedicated external plan audit demo route should be public for the launch demo"
);

console.log("same-origin API smoke test passed");
