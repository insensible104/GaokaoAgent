import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, "..", "App.tsx"), "utf8");

assert.match(appSource, /AdmissionsOpportunityDemoCasePanel/);
assert.match(appSource, /components\/AdmissionsOpportunityDemoCasePanel/);
assert.match(appSource, /showAdmissionsOpportunityDemo/);
assert.match(appSource, /VITE_SHOW_ADMISSIONS_DEMO/);
assert.match(appSource, /admissionsOpportunityDemoRequested/);
assert.match(appSource, /admissions-opportunity-demo/);
assert.match(appSource, /demo"\) === "admissions-opportunity"/);
assert.match(appSource, /Admissions opportunity demo case/);
assert.match(appSource, /<AdmissionsOpportunityDemoCasePanel \/>/);

console.log("Admissions opportunity demo entry smoke test passed");
