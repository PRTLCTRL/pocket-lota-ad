import { Agent } from "@cursor/sdk";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const cwd = dirname(fileURLToPath(import.meta.url));
const prompt = readFileSync(join(cwd, "_lota-agent-prompt.md"), "utf8");
const apiKey = process.env.CURSOR_API_KEY;
if (!apiKey) {
  console.error("MISSING CURSOR_API_KEY");
  process.exit(1);
}

const result = await Agent.prompt(prompt, {
  apiKey,
  model: { id: "composer-2" },
  local: { cwd },
});
console.log(JSON.stringify({ status: result.status, result: result.result }, null, 2));
