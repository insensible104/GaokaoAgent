import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, "App.tsx"), "utf8");

assert.match(
  appSource,
  /delivery_profile:\s*data\.delivery_profile/,
  "the analyze request must send the user's structured recommendation profile"
);

assert.match(
  appSource,
  /<GameMatrixView\s+gameMatrix=\{result\.game_matrix\}\s+userProfile=\{deliveryProfile\}/,
  "the recommendation view must receive the resolved profile and its provenance"
);

console.log("structured profile request smoke test passed");
