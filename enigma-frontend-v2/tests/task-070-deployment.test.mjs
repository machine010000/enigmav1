import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(path, import.meta.url), "utf8");

test("V2 owns its Vercel framework and build configuration", async () => {
  const config = JSON.parse(await read("../vercel.json"));
  assert.equal(config.framework, "nextjs");
  assert.equal(config.buildCommand, "npm run build");
  assert.equal(config.rewrites, undefined);
  assert.equal(config.routes, undefined);
});

test("repository-root Vercel config cannot route to the legacy frontend", async () => {
  const config = JSON.parse(await read("../../vercel.json"));
  const serialized = JSON.stringify(config);
  assert.doesNotMatch(serialized, /enigma-frontend/);
  assert.equal(config.routes, undefined);
  assert.equal(config.builds, undefined);
  assert.equal(config.env, undefined);
});

test("the freelancing route reaches Control Center and TASK-069 Chat", async () => {
  const page = await read("../app/app/freelancing/page.tsx");
  const shell = await read("../app/components/module-shell.tsx");
  const controlCenter = await read("../app/components/freelancing-control-center.tsx");
  assert.match(page, /<FreelancingShell\s*\/>/);
  assert.match(shell, /<FreelancingControlCenter\s*\/>/);
  assert.match(controlCenter, /<FreelancerChat\s*\/>/);
});

test("optional marketplace status failure does not block core Freelancer UI", async () => {
  const source = await read("../app/components/freelancing-control-center.tsx");
  assert.match(source, /const connectionRequest = apiRequest<Connection>/);
  assert.match(source, /\.catch\(\(error: unknown\)/);
  assert.match(source, /connectionRequest,/);
  assert.match(source, /Chat and manual intake remain available/);
  assert.match(source, /!workspace\.connectionError && !workspace\.connection\?\.configured/);
  assert.match(source, /if \(workspace\.error\) return/);
});
