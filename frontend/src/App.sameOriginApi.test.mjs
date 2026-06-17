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

for (const [name, source] of [
  ["App", appSource],
  ["InternalDeliveryReview", deliverySource],
]) {
  assert.match(
    source,
    /: import\.meta\.env\.VITE_API_URL \|\| "";/,
    `${name} production build should default to same-origin API requests`
  );
}

assert.doesNotMatch(
  appSource,
  /网络错误，请检查后端服务是否运行 \(http:\/\/localhost:8000\)/,
  "student-facing production errors should not prescribe a development-only host"
);

assert.match(
  appSource,
  /const showDedicatedAdmissionsOpportunityDemo\s*=\s*showAdmissionsOpportunityDemo && admissionsOpportunityDemoRequested;/,
  "production demo route must stay behind the explicit admissions demo gate"
);

assert.match(
  appSource,
  /if \(showDedicatedAdmissionsOpportunityDemo\)/,
  "dedicated admissions demo rendering should use the gated route flag"
);

console.log("same-origin API smoke test passed");
