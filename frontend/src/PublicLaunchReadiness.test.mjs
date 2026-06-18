import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..");

function read(relativePath) {
  const absolutePath = path.join(repoRoot, relativePath);
  assert.equal(fs.existsSync(absolutePath), true, `${relativePath} should exist`);
  return fs.readFileSync(absolutePath, "utf8");
}

const appSource = read("frontend/src/App.tsx");
const readme = read("README.md");
const compose = read("docker-compose.yml");
const rootEnvExample = read(".env.example");
const deployPs1 = read("scripts/deploy.ps1");
const deploySh = read("scripts/deploy.sh");
const pagesWorkflow = read(".github/workflows/deploy-pages.yml");
const viteConfig = read("frontend/vite.config.ts");

assert.match(appSource, /ExternalPlanAuditDemoPanel/);
assert.match(appSource, /external-plan-audit-demo/);
assert.match(appSource, /admissions-opportunity-demo/);
assert.match(appSource, /report-template-preview/);
assert.doesNotMatch(
  appSource,
  /showDedicatedAdmissionsOpportunityDemo\s*=\s*showAdmissionsOpportunityDemo && admissionsOpportunityDemoRequested/,
  "dedicated admissions demo route should be public in production"
);

assert.match(rootEnvExample, /LLM_PROVIDER=deepseek/);
assert.match(rootEnvExample, /DEEPSEEK_API_KEY=/);
assert.match(rootEnvExample, /TAVILY_API_KEY=/);
assert.match(rootEnvExample, /VITE_BASE_PATH=\/app\//);
assert.match(rootEnvExample, /VITE_API_URL=/);

assert.match(compose, /LLM_PROVIDER:\s*\$\{LLM_PROVIDER:-deepseek\}/);
assert.match(compose, /healthcheck:/);
assert.match(compose, /backend\/logs:\/app\/backend\/logs/);

assert.match(deployPs1, /docker compose up --build -d/);
assert.match(deployPs1, /http:\/\/localhost:8000\/app/);
assert.match(deploySh, /docker compose up --build -d/);
assert.match(deploySh, /http:\/\/localhost:8000\/app/);

assert.match(readme, /PathFinder Lite/);
assert.match(readme, /docker compose up --build/);
assert.match(readme, /http:\/\/localhost:8000\/app/);
assert.match(readme, /external-plan-audit-demo/);
assert.match(readme, /admissions-opportunity-demo/);
assert.match(readme, /report-template-preview/);

assert.match(viteConfig, /VITE_BASE_PATH/);
assert.match(viteConfig, /VITE_DEV_API_PROXY/);

assert.match(pagesWorkflow, /actions\/deploy-pages@v4/);
assert.match(pagesWorkflow, /VITE_BASE_PATH: \/GaokaoAgent\//);
assert.match(pagesWorkflow, /VITE_API_URL: \$\{\{ vars\.PUBLIC_API_URL \}\}/);
assert.match(pagesWorkflow, /cp frontend\/dist\/index\.html frontend\/dist\/404\.html/);
assert.match(pagesWorkflow, /frontend\/dist\/admissions-opportunity-demo/);
assert.match(pagesWorkflow, /frontend\/dist\/external-plan-audit-demo/);
assert.match(pagesWorkflow, /frontend\/dist\/report-template-preview/);

console.log("public launch readiness smoke test passed");
