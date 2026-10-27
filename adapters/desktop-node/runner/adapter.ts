/**
 * boar-eval desktop-node adapter: EvalRequest jsonl in, one EvalTrace per request out, from BOAR's REAL answer engine
 * (`createAnswerer`, src/routing/answer.ts) running in Node. Derived from rnd/kiln/exp-06-desktop-answerer/runner/answerer.ts
 * (same wiring, same node-llama-cpp engine and sampler, same shims), so exp-06 runs are reproducible here.
 *
 * Layout on the mini (setup.sh): <tree> = <runner>/kiln/be-<sha8>[-<arm>] holds the engine's src/ at a commit
 * (`git archive`, optionally + an arm patch) plus COMMIT / ARM / PATCH_SHA256; this runner lives in <tree>/be/.
 * Zero edits to engine source: only native modules are swapped (app-shims/: expo-sqlite, expo-file-system, llama.rn
 * embeddings, ram-monitor = SIMULATED RAM, react-native Platform = simulated platform), and generation goes to
 * node-llama-cpp through the AnswerEngine dependency.
 *
 * retrieval.raw = what deps.retrieve returned (the engine's single retrieve dependency, wrapped here) BEFORE the
 * engine's gates (onTopic, compressContext, source gates); kept = the AnswerResult's final sources; dropped = raw − kept.
 *
 *   be/node_modules/.bin/tsx be/adapter.ts --requests be/runs/<runId>/requests.jsonl --out be/runs/<runId>/traces.jsonl
 *     [--ids a,b] [--threads 4] [--gpu] [--timeout-ms 120000] [--corpus essential|bundled] [--places a.sqlite,b.sqlite]
 *     [--token-events-max 64] [--event-source-text] [--backend node|server --server-bin <llama-server>] [--deep-model <id>] [--dump-prompts f.jsonl]
 * --backend server: generation through a pinned llama-server over HTTP/SSE (makeServerEngine) instead of in-process
 * node-llama-cpp; the default ("node") is unchanged. Spec: rnd/research/anvil/specs/adapter-llama-server-backend.md.
 * Every request in a file must share one config (commit, arm, model, settings, kit, device, seed, temperature).
 */
import { execFile, execFileSync, spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFileSync, createReadStream, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import os from "node:os";
import { EvalRequest, EvalTrace, PROTOCOL_VERSION } from "./protocol";
import {
  answerContext,
  capTokenEvents,
  invalidateTiming,
  parseShard,
  citedTitles,
  droppedOf,
  mapEvent,
  round1,
  shownTitles,
  sourceRef,
  taskOf,
  warningCodes,
  type ChunkLike,
  type SourceRef,
  type TraceEvent,
} from "./trace";
import { gateEnabled, gateTop, renderChatML, topProbs } from "./gate";
import { applyData, budgetExceeded, modelGuard, newHiddenState, newStreamState, nodeChatOptions, nodeHidden, parsePsRss, requestFor, rssSampler, serverVersion, sseData } from "./server";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..");
const HOME = os.homedir();
const SHARED_MODELS = process.env.BOAR_SHARED_MODELS ?? join(HOME, "boar/shared-models");
const PACK_DIRS = (process.env.BOAR_EVAL_PACK_DIRS ?? `${HOME}/boar/shared-data/packs:${HOME}/boar/shared-data/crypto`).split(":");

// ---------------------------------------------------------------- args + requests (before any app import: shims read env)
const argv = process.argv.slice(2);
const get = (k: string, d?: string) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : d);
const cli = {
  requests: get("--requests"),
  out: get("--out"),
  ids: get("--ids")?.split(",").filter(Boolean),
  threads: Number(get("--threads", "4")),
  gpu: argv.includes("--gpu"),
  timeoutMs: Number(get("--timeout-ms", "120000")),
  corpus: get("--corpus", "essential") as "bundled" | "essential",
  places: get("--places")?.split(",").filter(Boolean) ?? [],
  tokenEventsMax: Number(get("--token-events-max", process.env.BOAR_EVAL_TOKEN_EVENTS_MAX ?? "64")),
  /** Keep each source's passage text (as placed in the prompt) in `sources` events: exact key-in-context. Off by default. */
  eventSourceText: argv.includes("--event-source-text"),
  backend: get("--backend", "node") as "node" | "server",
  serverBin: get("--server-bin"),
  deepModel: get("--deep-model"),
  /** jsonl of every generate's input ({itemId, messages | prompt, nPredict}): the deep arm's bmoe memory probe replays them. */
  dumpPrompts: get("--dump-prompts"),
  /** --installed a,b (node backend): every listed model is installed and no model is the user's pick, so the engine
   *  chooses as the app would (rankAnswerModels); the adapter loads whichever GGUF the engine asks for. */
  installed: get("--installed")?.split(",").filter(Boolean),
  /** --backend server only: an already running llama-server (parallel.sh starts one with -np N for all shards). */
  serverUrl: get("--server-url"),
  /** "i/N": run only requests k with k % N == i (parallel L1 mode). N > 1 nulls the latency fields (shared CPU). */
  shard: get("--shard"),
};
if (!cli.requests || !cli.out) throw new Error("--requests and --out are required");
if (cli.backend !== "node" && cli.backend !== "server") throw new Error(`--backend must be node or server, got ${cli.backend}`);
if (cli.backend === "server" && !cli.serverBin) throw new Error("--backend server needs --server-bin <llama-server>");
if (cli.deepModel && cli.backend !== "server") throw new Error("--deep-model needs --backend server (the backend holds the deep model)");
if (cli.installed && (cli.backend !== "node" || cli.deepModel)) throw new Error("--installed works with the node backend only, without --deep-model");
if (cli.serverUrl && cli.backend !== "server") throw new Error("--server-url needs --backend server");
const shard = cli.shard ? parseShard(cli.shard) : null;
/**
 * BOAR_ITEM_LOCATIONS=<json [{id, lat, lon}]> (VENUEGPS, runner-only): a per-item device fix for items whose EvalItem has
 * no context lat/lon, handed to the engine exactly where the app's GPS would be (geoProvidersFrom getCurrentPoint /
 * getLocationFix) in the app's Point shape (src/services/location.pure.ts: lat, lon, accuracyM, ageS; a fresh fix,
 * ageS 0). Unset (default): nothing changes.
 */
const ITEM_LOCATIONS: Map<string, { lat: number; lon: number }> | null = process.env.BOAR_ITEM_LOCATIONS
  ? new Map((JSON.parse(readFileSync(process.env.BOAR_ITEM_LOCATIONS, "utf8")) as { id: string; lat: number; lon: number }[])
      .map((r) => [r.id, { lat: Number(r.lat), lon: Number(r.lon) }]))
  : null;
/** Several items share the machine at once: latency fields are not comparable, so traces carry them as null. */
const PARALLEL = !!shard && shard.n > 1;

function fail(msg: string): never {
  console.error(`[desktop-node] FATAL: ${msg}`);
  process.exit(1);
}

let requests: EvalRequest[] = readFileSync(cli.requests, "utf8")
  .split("\n")
  .map((l, i) => [l, i] as const)
  .filter(([l]) => l.trim())
  .map(([l, i]) => {
    const r = EvalRequest.safeParse(JSON.parse(l));
    if (!r.success) fail(`requests line ${i + 1}: ${r.error.issues.map((x) => `${x.path.join(".")}: ${x.message}`).join("; ")}`);
    return r.data;
  });
if (cli.ids) {
  const missing = cli.ids.filter((id) => !requests.some((r) => r.item.id === id));
  if (missing.length) fail(`--ids not in the requests: ${missing.join(",")}`);
  requests = requests.filter((r) => cli.ids!.includes(r.item.id));
}
if (shard) {
  requests = requests.filter((_, k) => k % shard.n === shard.i);
  // A shard can be empty when there are fewer items than workers: write an empty file, nothing to run.
  if (!requests.length) { mkdirSync(dirname(cli.out!), { recursive: true }); writeFileSync(cli.out!, ""); console.log(JSON.stringify({ done: 0, shard: cli.shard })); process.exit(0); }
}
if (!requests.length) fail("no requests");
const sig = (r: EvalRequest) => JSON.stringify({ runId: r.runId, config: r.config, seed: r.seed, temperature: r.temperature ?? null });
if (requests.some((r) => sig(r) !== sig(requests[0]))) fail("all requests in one file must share runId, config, seed and temperature");
const R0 = requests[0];
const config = R0.config;

// The tree this runner sits in must be the engine the requests ask for.
const treeCommit = readFileSync(join(ROOT, "COMMIT"), "utf8").trim();
const treeArm = existsSync(join(ROOT, "ARM")) ? readFileSync(join(ROOT, "ARM"), "utf8").trim() : "main";
const patchSha = existsSync(join(ROOT, "PATCH_SHA256")) ? readFileSync(join(ROOT, "PATCH_SHA256"), "utf8").trim() : null;
if (!treeCommit.startsWith(config.commit)) fail(`requests ask for commit ${config.commit}, this tree is ${treeCommit}`);
// A config-only variant of an unpatched tree ("main~persona-p2": same engine, other settings) runs on that tree.
const armOk = treeArm === config.arm || (!patchSha && config.arm.startsWith(`${treeArm}~`));
if (!armOk) fail(`requests ask for arm "${config.arm}", this tree is arm "${treeArm}"`);

process.env.BOAR_EVAL_RAM_BYTES = String(Math.round(config.device.ramGb * 1024 ** 3));
process.env.BOAR_EVAL_PLATFORM = config.device.platform;
process.env.BOAR_APP_GPU = cli.gpu ? "1" : process.env.BOAR_APP_GPU ?? "1"; // embeddings: Metal is fine (not timed)

// ---------------------------------------------------------------- models (sha256 = HF LFS oid)
const MODELS: Record<string, { file: string; sha256: string }> = {
  "qwen2.5-1.5b-instruct-q4km": { file: "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf", sha256: "1adf0b11065d8ad2e8123ea110d1ec956dab4ab038eab665614adba04b6c3370" },
  "qwen3-4b-instruct-2507-q4km": { file: "Qwen3-4B-Instruct-2507-Q4_K_M.gguf", sha256: "3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597" },
  // THINK4B: the thinking twin of the Android default (unsloth/Qwen3-4B-Thinking-2507-GGUF @ f40adb104d, Apache-2.0; rnd/kiln/MODELS.md).
  // Its template always opens <think>; the fast tier's budget (FAST_THINKING_BUDGET) is enforced by llama-server (--backend server).
  "qwen3-4b-thinking-2507-q4km": { file: "Qwen3-4B-Thinking-2507-Q4_K_M.gguf", sha256: "ddd52e18200baab281c5c46f70d544ce4d4fe4846eab1608f2fff48a64554212" },
  // Anvil card gemma4-e4b-reader-android; sha256 = the app catalog's (manifest.ts gemma-4-e4b-it-q4_0).
  "gemma-4-e4b-it-q4_0": { file: "gemma-4-E4B-it-qat-Q4_0.gguf", sha256: "676c35070db6dbe52f93e9c864ee0fba4eddea94b9c875d9cb10daff453fbaee" },
  // Anvil card maple-20b-a1b-fast-reader (QUEUE #15): deepgrove/maple-preview-GGUF @ f5466f918e. Arch `maple` needs
  // llama.cpp b11010+, so --backend server only (node-llama-cpp 3.21.1 cannot load it).
  "maple-preview-tq2_0-head-q4k": { file: "maple-preview-TQ2_0-head-Q4_K.gguf", sha256: "221f792cc9760d27a34f449b4229e258fa968a63bd4213993e45d9c0bb477a9e" },
  // Anvil card deep-tier-streamed-moe §6b (S1 option 6): unsloth/Qwen3.6-35B-A3B-GGUF @ a483e9e6cb (ADR 0001 §10).
  // `qwen35moe` arch: --backend server; used as --deep-model.
  "qwen3.6-35b-a3b-ud-q2kxl": { file: "Qwen3.6-35B-A3B-UD-Q2_K_XL.gguf", sha256: "96b9c0af5c77a4ecaabe3983175112b5ece763261c1ece12b2494b692a70dad7" },
  // QUANTCEIL (2026-10-12): the same repo/revision at UD-IQ3_XXS (13.2 GB, ~3.1 bpw) to measure what the 2-bit quant costs the deep tier.
  "qwen3.6-35b-a3b-ud-iq3xxs": { file: "Qwen3.6-35B-A3B-UD-IQ3_XXS.gguf", sha256: "9c964e657212fea1f24905dd7b0a89b82fd807d19fab0b41da14251b07b88fbe" },
  // GEMMATHINK: unsloth/gemma-4-26B-A4B-it-GGUF (rnd/kiln/MODELS.md; MOESCREEN-gemma4). --backend server, --deep-model only;
  // its template thinks only with enable_thinking=true (BOAR_THINK_KWARG=1 in server.ts).
  "gemma-4-26b-a4b-ud-q2kxl": { file: "gemma-4-26B-A4B-it-UD-Q2_K_XL.gguf", sha256: "2a1d26dfe6ea00a467940a5728316af6edb366bbdba950d65b85d232392fb658" },
  // BONSAI2 (2026-10-15): prism-ml/Ternary-Bonsai-2-4B-gguf @ 8d655716 (Apache-2.0; base Qwen3.5-4B, ternary PTQ1_0).
  // PTQ1_0 loads only in PrismML's llama.cpp fork (prism-b10777-e3de715): --backend server --server-bin <fork>; fast tier,
  // thinking OFF via the engine's enable_thinking:false (chat_template_kwargs, server.ts).
  "bonsai2-4b-ptq1_0": { file: "bonsai2/Ternary-Bonsai-2-4B-PTQ1_0.gguf", sha256: "56711263ec9a9ffeaa74a3a0e58dece8127cf9268404746c721113ca76994d60" },
  // BONSAI2-2B (2026-10-15): prism-ml/Ternary-Bonsai-2-2B-gguf @ 683f7be2 (Apache-2.0; base Qwen3.5-2B, ternary PTQ1_0); lite-tier measurement, same path as the 4B.
  "bonsai2-2b-ptq1_0": { file: "bonsai2/Ternary-Bonsai-2-2B-PTQ1_0.gguf", sha256: "36061ad406df8a4903a6db005be350c50fabfaf717f9ef0acf4b76adcd9929fa" },
  // LITE2 (2026-10-15): unsloth/Qwen3-1.7B-GGUF @ d7f544ee (Apache-2.0; hybrid-thinking Qwen3-1.7B, Q4_K_M; the official Qwen repo ships Q8_0 only).
  // Stock llama.cpp (b11010); lite-tier control for the ternary 2B; thinking OFF (BOAR_SERVER_EXTRA_ARGS="--reasoning off" + the engine's enable_thinking:false).
  "qwen3-1.7b-q4km": { file: "lite/Qwen3-1.7B-Q4_K_M.gguf", sha256: "b139949c5bd74937ad8ed8c8cf3d9ffb1e99c866c823204dc42c0d91fa181897" },
};
/**
 * Models under test that the engine tree's catalog (src/models/manifest.ts) does not list yet: the adapter supplies the
 * entry the app would have, shaped like the Android default (Qwen3-4B's: answerTier "default", roles general + fast,
 * chat template). Used only when the tree lacks the id; recorded as versions["catalog.entry"] = "adapter".
 */
// parallel.sh asks which GGUF the requests' config generates with, to start the shared llama-server on it.
if (argv.includes("--print-model")) {
  const m = MODELS[cli.deepModel ?? config.modelId];
  if (!m) fail(`no model entry for ${cli.deepModel ?? config.modelId}`);
  console.log(join(SHARED_MODELS, m.file));
  process.exit(0);
}

const ADAPTER_CATALOG: Record<string, Record<string, unknown>> = {
  // BONSAI2: shaped like the Android default (roles general + fast, answerTier default), so the fast tier picks it.
  "bonsai2-4b-ptq1_0": {
    id: "bonsai2-4b-ptq1_0", kind: "llm", label: "Ternary-Bonsai-2-4B (PTQ1_0)",
    filename: "models/bonsai2-4b-ptq1_0.gguf", sizeBytes: 949549920, answerTier: "default",
    capabilities: { roles: ["general", "fast"], usesChatTemplate: true },
  },
  "bonsai2-2b-ptq1_0": {
    id: "bonsai2-2b-ptq1_0", kind: "llm", label: "Ternary-Bonsai-2-2B (PTQ1_0)",
    filename: "models/bonsai2-2b-ptq1_0.gguf", sizeBytes: 429183456, answerTier: "default",
    capabilities: { roles: ["general", "fast"], usesChatTemplate: true },
  },
  // LITE2: same shape as the BONSAI2 entries (roles general + fast, answerTier default), so the fast tier picks it.
  "qwen3-1.7b-q4km": {
    id: "qwen3-1.7b-q4km", kind: "llm", label: "Qwen3-1.7B (Q4_K_M)",
    filename: "models/qwen3-1.7b-q4km.gguf", sizeBytes: 1107409472, answerTier: "default",
    capabilities: { roles: ["general", "fast"], usesChatTemplate: true },
  },
  // THINK4B: shaped like the Android default (roles general + fast, answerTier default), so the fast tier picks it.
  "qwen3-4b-thinking-2507-q4km": {
    id: "qwen3-4b-thinking-2507-q4km", kind: "llm", label: "Qwen3-4B-Thinking-2507 (Q4_K_M)",
    filename: "models/qwen3-4b-thinking-2507-q4km.gguf", sizeBytes: 2497281152, answerTier: "default",
    capabilities: { roles: ["general", "fast"], usesChatTemplate: true },
  },
  "maple-preview-tq2_0-head-q4k": {
    id: "maple-preview-tq2_0-head-q4k", kind: "llm", label: "Maple-Preview 20B-A1B (TQ2_0, Q4_K head)",
    filename: "models/maple-preview-tq2_0-head-q4k.gguf", sizeBytes: 5901782560, answerTier: "default",
    capabilities: { roles: ["general", "fast"], usesChatTemplate: true },
  },
  // The deep tier's model (card §6b): role "reasoning" only, so it is never the fast pick nor a verifier.
  "qwen3.6-35b-a3b-ud-q2kxl": {
    id: "qwen3.6-35b-a3b-ud-q2kxl", kind: "llm", label: "Qwen3.6-35B-A3B (UD-Q2_K_XL)",
    filename: "models/qwen3.6-35b-a3b-ud-q2kxl.gguf", sizeBytes: 12290628576,
    capabilities: { roles: ["reasoning"], usesChatTemplate: true },
  },
  "qwen3.6-35b-a3b-ud-iq3xxs": {
    id: "qwen3.6-35b-a3b-ud-iq3xxs", kind: "llm", label: "Qwen3.6-35B-A3B (UD-IQ3_XXS)",
    filename: "models/qwen3.6-35b-a3b-ud-iq3xxs.gguf", sizeBytes: 13211155424,
    capabilities: { roles: ["reasoning"], usesChatTemplate: true },
  },
  "gemma-4-26b-a4b-ud-q2kxl": {
    id: "gemma-4-26b-a4b-ud-q2kxl", kind: "llm", label: "Gemma 4 26B-A4B (UD-Q2_K_XL)",
    filename: "models/gemma-4-26b-a4b-ud-q2kxl.gguf", sizeBytes: 10546934240,
    capabilities: { roles: ["reasoning"], usesChatTemplate: true },
  },
};
const EMBED_FILE = "bge-small-en-v1.5-q8_0.gguf";
const EMBED_SHA256 = "ec38e8da142596baa913124ae50550de284b6916bf59577ef2f0cb9660c2f514";

async function sha256File(path: string) {
  const h = createHash("sha256");
  for await (const c of createReadStream(path)) h.update(c as Buffer);
  return h.digest("hex");
}

/** A kit PackRef -> the pack file on this host (<id>.sqlite in BOAR_EVAL_PACK_DIRS), sha256-checked. */
async function resolveKit() {
  const files: string[] = [];
  for (const ref of config.kit) {
    const path = PACK_DIRS.map((d) => join(d, `${ref.id}.sqlite`)).find((p) => existsSync(p));
    if (!path) fail(`kit pack ${ref.id}: no ${ref.id}.sqlite in ${PACK_DIRS.join(", ")}`);
    const got = await sha256File(path);
    if (got !== ref.sha256) fail(`kit pack ${ref.id}: ${path} has sha256 ${got}, the request pins ${ref.sha256}`);
    files.push(path);
  }
  return files;
}

// ---------------------------------------------------------------- shims + app retrieval (exp-06 setupAppRetrieval)
async function setupAppRetrieval(packFiles: string[]) {
  const { registerHooks } = await import("node:module");
  const shim = (f: string) => new URL(`./app-shims/${f}`, import.meta.url).href;
  const SHIMS: Record<string, string> = {
    "expo-sqlite": shim("expo-sqlite.mjs"), "expo-file-system": shim("expo-file-system.mjs"),
    "expo-file-system/legacy": shim("expo-file-system.mjs"), "llama.rn": shim("llama-rn.mjs"),
    "react-native": shim("react-native.mjs"), "ram-monitor": shim("ram-monitor.mjs"),
  };
  (registerHooks as any)({
    resolve: (spec: string, ctx: any, next: any) => {
      if (SHIMS[spec]) return { url: SHIMS[spec], shortCircuit: true };
      // MP4B: orchestrator.ts's direct retrieve import goes through a re-export that logs it (app-shims/orchestrator-retrieve.mjs);
      // the shim's "boar-eval:tree-retrieve" is the tree's own module. Nothing else imports orchestrator.ts in the runner.
      if (spec === "boar-eval:tree-retrieve") return { url: pathToFileURL(join(ROOT, "src/rag/retrieve.ts")).href, shortCircuit: true };
      if (/^\.\.\/rag\/retrieve(\.ts)?$/.test(spec) && String(ctx?.parentURL ?? "").endsWith("/src/services/orchestrator.ts"))
        return { url: shim("orchestrator-retrieve.mjs"), shortCircuit: true };
      try {
        return next(spec, ctx);
      } catch (e) {
        if (/^[./]/.test(spec)) throw e;
        return next(spec, { ...ctx, parentURL: import.meta.url });
      }
    },
  });
  const { symlinkSync, rmSync } = await import("node:fs");
  const code = ["src/rag/seedCorpus.ts", "src/rag/db.ts", "src/rag/retrieve.ts", "src/rag/packs.ts", "src/models/manifest.ts"]
    .map((f) => (existsSync(join(ROOT, f)) ? readFileSync(join(ROOT, f), "utf8") : "")).join("\n");
  const key = createHash("sha256").update(code).update(cli.corpus).update(packFiles.join(",")).update(cli.places.join(",")).digest("hex").slice(0, 16)
    + (shard ? `-w${shard.i}` : ""); // each parallel worker seeds its own app dir (no shared SQLite / symlink races)
  const appDir = join(HERE, ".cache", "appdir", key);
  process.env.BOAR_APP_DIR = appDir;
  mkdirSync(join(appDir, "corpus"), { recursive: true });
  const manifest: any = await import(join(ROOT, "src/models/manifest.ts"));
  const catalog: any[] = [...(manifest.MODEL_CATALOG ?? []), ...(manifest.CORPUS_CATALOG ?? [])];
  const link = (src: string, rel: string) => {
    const dst = join(appDir, rel);
    mkdirSync(dirname(dst), { recursive: true });
    rmSync(dst, { force: true });
    symlinkSync(src, dst);
  };
  const emb = catalog.find((m) => m.kind === "embedding" && m.required);
  link(join(SHARED_MODELS, EMBED_FILE), emb.filename);
  if (cli.corpus === "essential") for (const id of ["corpus-standard", "corpus-full"]) {
    const entry = catalog.find((m) => m.id === id);
    if (!entry) fail(`catalog has no ${id}`);
    link(join(ROOT, "assets/corpus", `${id}.json`), entry.filename);
  }
  for (const m of ["src/rag/cryptoPack.ts", "src/rag/preparedness.ts"]) if (existsSync(join(ROOT, m))) await import(join(ROOT, m));
  for (const p of packFiles) {
    const id = p.split("/").pop()!.replace(/\.sqlite$/, "");
    const filename = catalog.find((m) => m.id === id)?.filename ?? `corpus/${id}.sqlite`;
    link(p, filename);
  }
  for (const p of cli.places) link(p, join("poi", p.split("/").pop()!));
  const { embeddingEngine } = await import(join(ROOT, "src/rag/embed.ts"));
  await embeddingEngine.load(emb.filename);
  const { seedKnowledgeBaseIfEmpty } = await import(join(ROOT, "src/rag/seedCorpus.ts"));
  await seedKnowledgeBaseIfEmpty();
  const lex: any = await import(join(ROOT, "src/rag/ptLexiconAsset.ts"));
  if (!Object.keys(lex.ptLexicon() ?? {}).length) fail("LEXICON-NOT-LOADED: the app's PT lexicon did not load");
  let geo: any = null;
  const point: { current: { lat: number; lon: number; accuracyM: number; ageS?: number } | null } = { current: null };
  if (existsSync(join(ROOT, "src/routing/geoWiring.ts")) && existsSync(join(ROOT, "src/rag/pois.ts"))) {
    const { geoProvidersFrom } = await import(join(ROOT, "src/routing/geoWiring.ts"));
    const pois = await import(join(ROOT, "src/rag/pois.ts"));
    const regions = existsSync(join(ROOT, "src/rag/poiRegions.ts")) ? await import(join(ROOT, "src/rag/poiRegions.ts")) : { POI_REGIONS: [] };
    const fix = async () => point.current ?? { error: "unavailable" as const };
    geo = geoProvidersFrom({
      installedPoiPacks: pois.installedPoiPacks, getCurrentPoint: fix, getLocationFix: fix,
      resolvePlace: pois.resolvePlace, searchPois: pois.searchPois,
      cities: () => (regions.POI_REGIONS ?? []).flatMap((r: any) => r.cities ?? []),
    });
  }
  return { geo, point, catalog };
}

// ---------------------------------------------------------------- AnswerEngine on node-llama-cpp (exp-06, unchanged sampler)
interface Generation {
  promptTokens: number; promptMs: number; predictedTokens: number; predictedMs: number; firstTextMs: number; timedOut: boolean; temperature: number;
  /** Hidden reasoning: always on the server backend (reasoning_content chunks + peak RSS); on the node backend only when a
   *  thought budget was active and thought segments appeared or a positive budget was set. firstReasoningMs: ms since generate. */
  hidden?: { startedAt: number; reasoningTokens: number; firstReasoningMs: number | null; visibleText: boolean; budgetExceeded: boolean; peakRssBytes: number | null };
}

async function makeEngine(modelPath: string, fileName: string, seed: number, temp: number | undefined, onGeneration: (g: Generation) => void) {
  const { getLlama, LlamaChatSession, LlamaCompletion, resolveChatWrapper } = await import("node-llama-cpp");
  const llama = await getLlama({ gpu: cli.gpu ? "auto" : false });
  const t0 = performance.now();
  const model = await llama.loadModel({ modelPath, gpuLayers: cli.gpu ? "auto" : 0, useMlock: false });
  const loadMs = performance.now() - t0;
  const hasTemplate = model.fileInfo.metadata?.tokenizer?.chat_template != null;
  // A template with a thinking switch (exp-07 debug).
  const thinkingTemplate = /enable_thinking/.test(String((model as any).fileInfo?.metadata?.tokenizer?.chat_template ?? ""));
  let abort: AbortController | null = null;
  const engine = {
    loadMs,
    async load() { return { fit: null, warning: null } as any; },
    async stop() { abort?.abort(); },
    getModelInfo: () => ({ filename: fileName }),
    hasEmbeddedChatTemplate: () => hasTemplate,
    async estimateFit() { return null; },
    setAnswerPrefix() { /* the app prefills its fixed prefix in llama.rn's KV; not emulated (fresh context per answer) */ },
    // Route gate (GATEFID; engine src/routing/routeGate.ts): top-N next-token probabilities after the messages (see gate.ts). Opt-in.
    async nextTokenProbs(messages: { role: string; content: string }[], opts: { modelFilename: string; nProbs: number }) {
      if (opts.modelFilename !== fileName || !String(model.fileInfo.metadata?.tokenizer?.chat_template ?? "").includes("<|im_start|>")) return null;
      const tokens = model.tokenize(renderChatML(messages), true);
      const ctx = await model.createContext({ contextSize: Math.max(2048, tokens.length + 16), threads: cli.threads, seed });
      try {
        const out = await ctx.getSequence().controlledEvaluate(tokens.map((t: any, i: number) =>
          i === tokens.length - 1 ? [t, { generateNext: { probabilities: true, token: true, options: { temperature: 0 } } }] : t) as any);
        const probs: Map<number, number> = (out as any)[tokens.length - 1]?.next?.probabilities ?? new Map();
        return { promptTokens: tokens.length, probs: topProbs(probs, opts.nProbs, (t) => model.detokenize([t], true)) };
      } finally {
        await ctx.dispose();
      }
    },
    async generate(o: any): Promise<string> {
      const ctx = await model.createContext({ contextSize: Math.max(2048, o.nCtx ?? 4096), threads: cli.threads, seed });
      const seq = ctx.getSequence();
      abort = new AbortController();
      const timer = setTimeout(() => abort?.abort(), o.timeoutMs ?? cli.timeoutMs);
      const start = performance.now();
      let first: number | null = null, firstText: number | null = null, tokens = 0, promptTokens = 0;
      const temperature = temp ?? o.temperature ?? 0.7;
      const sampling = { temperature, topK: 40, topP: 0.95, minP: 0.05, seed,
                         maxTokens: (o.nPredict ?? 512) + (o.enableThinking === false ? 0 : o.thinkingBudget ?? 0),
                         signal: abort.signal, stopOnAbortSignal: true,
                         onToken: (t: readonly unknown[]) => {
                           if (first === null) { first = performance.now(); promptTokens = Math.max(0, seq.contextTokens.length - t.length); }
                           tokens += t.length;
                         } };
      let text = "";
      const hiddenSt = newHiddenState();
      try {
        if (hasTemplate && o.messages) {
          const msgs = o.messages as { role: string; content: string }[];
          const system = msgs.find((m) => m.role === "system")?.content ?? "";
          const user = [...msgs].reverse().find((m) => m.role === "user")!.content;
          const history = msgs.filter((m) => m.role !== "system").slice(0, -1).map((m) =>
            m.role === "user" ? { type: "user" as const, text: m.content } : { type: "model" as const, response: [m.content] });
          // enableThinking:false -> "discourage" only for a template that has a thinking switch (thinkingTemplate above).
          const wrapper = resolveChatWrapper(model, o.enableThinking === false && thinkingTemplate
            ? { customWrapperSettings: { qwen: { thoughts: "discourage" }, jinjaTemplate: { additionalRenderParameters: { enable_thinking: false } } } } as any : {});
          const session = new LlamaChatSession({ contextSequence: seq, systemPrompt: system, ...(wrapper ? { chatWrapper: wrapper } : {}) });
          if (history.length) session.setChatHistory([{ type: "system", text: system }, ...history] as any);
          // The thought budget is what actually stops thinking on 3.21.1 (render params alone do not; see server.ts nodeBudgets).
          text = await session.prompt(user, nodeChatOptions(o, sampling, hiddenSt, () => performance.now() - start,
            (c: string) => { if (firstText === null && c.trim()) firstText = performance.now(); o.onToken?.(c); }) as any);
        } else {
          const completion = new LlamaCompletion({ contextSequence: seq });
          text = await completion.generateCompletion(o.prompt ?? "", { ...sampling, customStopTriggers: o.stop ?? ["\nUser:", "\nQuestion:"],
            onTextChunk: (c: string) => { if (firstText === null && c.trim()) firstText = performance.now(); o.onToken?.(c); } } as any);
        }
      } catch (e) {
        if (!abort.signal.aborted) throw e;
      } finally {
        clearTimeout(timer);
        await ctx.dispose();
      }
      const end = performance.now();
      const promptMs = (first ?? end) - start;
      const h = hasTemplate && o.messages ? nodeHidden(o, hiddenSt) : null;
      const g: Generation = { promptTokens, promptMs, predictedTokens: tokens, predictedMs: end - (first ?? end), firstTextMs: (firstText ?? end) - start,
                              timedOut: abort.signal.aborted, temperature,
                              ...(h ? { hidden: { ...h, startedAt: start, visibleText: firstText !== null, peakRssBytes: null } } : {}) };
      onGeneration(g);
      o.onTimings?.({ promptTokens, promptMs, predictedTokens: tokens, predictedMs: g.predictedMs, cachedTokens: 0 });
      return text;
    },
  };
  return engine;
}

// ---------------------------------------------------------------- AnswerEngine on llama-server (--backend server)
const freePort = () => new Promise<number>((res, rej) => {
  const s = createServer();
  s.once("error", rej);
  s.listen(0, "127.0.0.1", () => {
    const p = (s.address() as any).port;
    s.close(() => res(p));
  });
});

async function makeServerEngine(modelPath: string, fileName: string, seed: number, temp: number | undefined, onGeneration: (g: Generation) => void) {
  const bin = resolve(cli.serverBin!.replace(/^~(?=\/)/, HOME));
  if (!existsSync(bin)) fail(`--server-bin ${bin} does not exist`);
  const v = spawnSync(bin, ["--version"], { encoding: "utf8" }); // prints on stderr
  const versionText = `${v.stdout ?? ""}${v.stderr ?? ""}`;
  let tag: string | null = null;
  try {
    tag = execFileSync("git", ["-C", join(dirname(bin), "../.."), "describe", "--tags", "--exact-match"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim() || null;
  } catch { /* not a tagged checkout */ }
  const version = serverVersion(versionText, tag);
  const external = cli.serverUrl?.replace(/\/$/, "");
  const port = external ? 0 : await freePort();
  const base = external ?? `http://127.0.0.1:${port}`;
  const args = ["-m", modelPath, "-t", String(cli.threads), "-tb", String(cli.threads), "-c", process.env.BOAR_SERVER_CTX ?? "4096", "-ngl", "0", "-np", "1", "--jinja",
                "--no-webui", "--cache-ram", "0", "--reasoning-format", "deepseek", "--host", "127.0.0.1", "--port", String(port),
                ...(process.env.BOAR_KV_TYPE ? ["--cache-type-k", process.env.BOAR_KV_TYPE, "--cache-type-v", process.env.BOAR_KV_TYPE] : []), // KVQ8 arm: KV cache type (unset = llama-server default f16)
                // BONSAI2: extra llama-server args, whitespace-split, appended last (unset = byte-identical args); recorded in versions["server.extra_args"].
                ...(process.env.BOAR_SERVER_EXTRA_ARGS ? process.env.BOAR_SERVER_EXTRA_ARGS.trim().split(/\s+/) : [])];
  const logPath = `${cli.out!.replace(/\.jsonl$/, "")}.server.log`;
  mkdirSync(dirname(logPath), { recursive: true });
  writeFileSync(logPath, `${bin} ${args.join(" ")}\n`);
  const t0 = performance.now();
  // --server-url: the server belongs to parallel.sh (started once for every shard); this process never spawns or kills it.
  const proc = external ? null : spawn(bin, args, { stdio: ["ignore", "pipe", "pipe"] });
  if (external) writeFileSync(logPath, `external llama-server ${external} (see parallel.sh's server log)\n`);
  proc?.stdout!.on("data", (d) => appendFileSync(logPath, d));
  proc?.stderr!.on("data", (d) => appendFileSync(logPath, d));
  let exited = false;
  proc?.on("exit", () => (exited = true));
  const kill = () => { if (proc && !exited) try { proc.kill("SIGTERM"); } catch { /* gone */ } };
  process.on("exit", kill);
  for (const sig of ["SIGINT", "SIGTERM", "SIGHUP"] as const) process.once(sig, () => { kill(); process.exit(130); });
  for (;;) {
    if (exited) fail(`llama-server exited during load, see ${logPath}`);
    if (performance.now() - t0 > 600_000) { kill(); fail("llama-server not healthy after 600 s"); }
    try {
      if ((await fetch(`${base}/health`)).status === 200) break;
    } catch { /* not listening yet */ }
    await new Promise((r) => setTimeout(r, 100));
  }
  const loadMs = performance.now() - t0;
  const props: any = await (await fetch(`${base}/props`)).json().catch(() => ({}));
  const hasTemplate = typeof props?.chat_template === "string" && props.chat_template.length > 0;
  // An external server must hold this run's GGUF (the sha256 check above covers the file, this covers what is loaded).
  if (external && !String(props?.model_path ?? "").endsWith(`/${fileName}`) && String(props?.model_path ?? "").split("/").pop() !== modelPath.split("/").pop())
    fail(`--server-url ${external} serves ${props?.model_path ?? "?"}, expected ${modelPath}`);
  const rss = rssSampler(() => new Promise((res) => (proc ? execFile("ps", ["-o", "rss=", "-p", String(proc.pid)], (e, out) => res(e ? null : parsePsRss(out))) : res(null))));
  await rss.sample();
  const idleRssBytes = rss.runPeakBytes;
  let abort: AbortController | null = null;
  const engine = {
    loadMs,
    backend: "llama-server" as const,
    /** Stop the server (the child's pipes would otherwise keep Node alive). */
    async close() {
      kill();
      if (proc && !exited) await new Promise((r) => proc.once("exit", r));
    },
    version,
    idleRssBytes,
    get peakRssBytes() { return rss.runPeakBytes; },
    async load() { return { fit: null, warning: null } as any; },
    async stop() { abort?.abort(); },
    getModelInfo: () => ({ filename: fileName }),
    hasEmbeddedChatTemplate: () => hasTemplate,
    async estimateFit() { return null; },
    setAnswerPrefix() { /* not emulated (cache_prompt false = fresh prefill per answer, as the node path) */ },
    async generate(o: any): Promise<string> {
      const { path, body } = requestFor(hasTemplate ? o : { ...o, messages: undefined }, temp, seed);
      const temperature = body.temperature as number;
      abort = new AbortController();
      const timer = setTimeout(() => abort?.abort(), o.timeoutMs ?? cli.timeoutMs);
      const st = newStreamState();
      const start = performance.now();
      rss.start();
      try {
        const res = await fetch(base + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: abort.signal });
        // A template/server error fails the item loudly (no silent fallback).
        if (!res.ok || !res.body) throw new Error(`llama-server ${path} HTTP ${res.status}: ${(await res.text().catch(() => "")).slice(0, 500)}`);
        const dec = new TextDecoder();
        let buf = "";
        for await (const chunk of res.body as any as AsyncIterable<Uint8Array>) {
          buf += dec.decode(chunk, { stream: true });
          const { datas, rest } = sseData(buf);
          buf = rest;
          for (const d of datas) applyData(st, d, performance.now() - start, (c) => o.onToken?.(c));
          if (st.done) break;
        }
        if (buf.trim()) for (const d of sseData(buf + "\n").datas) applyData(st, d, performance.now() - start, (c) => o.onToken?.(c));
      } catch (e) {
        if (!abort.signal.aborted) throw e;
      } finally {
        clearTimeout(timer);
      }
      const peakRssBytes = await rss.stop();
      const end = performance.now() - start;
      const t = st.timings;
      const g: Generation = {
        promptTokens: t?.promptTokens ?? 0,
        promptMs: t?.promptMs ?? (st.firstReasoningMs ?? st.firstTextMs ?? end),
        predictedTokens: t?.predictedTokens ?? st.reasoningTokens,
        predictedMs: t?.predictedMs ?? end - (st.firstReasoningMs ?? st.firstTextMs ?? end),
        firstTextMs: st.firstTextMs ?? end,
        timedOut: abort.signal.aborted,
        temperature,
        hidden: { startedAt: start, reasoningTokens: st.reasoningTokens, firstReasoningMs: st.firstReasoningMs, visibleText: st.firstTextMs !== null,
                  budgetExceeded: budgetExceeded(st.reasoningTokens, o.thinkingBudget, o.enableThinking), peakRssBytes },
      };
      onGeneration(g);
      o.onTimings?.({ promptTokens: g.promptTokens, promptMs: g.promptMs, predictedTokens: g.predictedTokens, predictedMs: g.predictedMs, cachedTokens: 0 });
      return st.content;
    },
  };
  return engine;
}

// ---------------------------------------------------------------- several installed models on node-llama-cpp (--installed)
/** The AnswerEngine the app has: nothing loaded until the engine asks; load(filename) brings that model in (each one
 *  loaded once and kept, as the desktop has RAM for both); generate runs on the loaded one. */
async function makeMultiEngine(models: { id: string; filename: string; path: string }[], seed: number, temp: number | undefined,
                               onGeneration: (g: Generation) => void, onUse: (id: string) => void) {
  const loaded = new Map<string, Awaited<ReturnType<typeof makeEngine>>>();
  let current: string | null = null;
  const byFile = new Map(models.map((m) => [m.filename, m]));
  const facade = {
    loadMs: 0,
    async load(filename: string) {
      const m = byFile.get(filename);
      if (!m) throw new Error(`--installed: the engine asked for ${filename}, which is not installed`);
      if (!loaded.has(filename)) {
        const e = await makeEngine(m.path, filename, seed, temp, onGeneration);
        loaded.set(filename, e);
        facade.loadMs += e.loadMs;
      }
      current = filename;
      return { fit: null, warning: null } as any;
    },
    async stop() { if (current) await loaded.get(current)?.stop(); },
    getModelInfo: () => (current ? { filename: current } : null),
    hasEmbeddedChatTemplate: () => (current ? loaded.get(current)!.hasEmbeddedChatTemplate() : true),
    async estimateFit() { return null; },
    setAnswerPrefix() { /* not emulated, as in makeEngine */ },
    // Route gate (GATEFID): on the model the engine names, loaded here if needed (the app keeps it resident).
    async nextTokenProbs(messages: { role: string; content: string }[], opts: { modelFilename: string; nProbs: number }) {
      if (!byFile.has(opts.modelFilename)) return null;
      await facade.load(opts.modelFilename);
      return loaded.get(opts.modelFilename)!.nextTokenProbs(messages, opts);
    },
    async generate(o: any): Promise<string> {
      if (!current) throw new Error("--installed: generate before any load");
      onUse(byFile.get(current)!.id);
      if (cli.dumpPrompts)
        appendFileSync(cli.dumpPrompts, JSON.stringify({ itemId: "", model: byFile.get(current)!.id, ...(o.messages ? { messages: o.messages } : { prompt: o.prompt }) }) + "\n");
      return loaded.get(current)!.generate(o);
    },
  };
  return facade;
}

function packageVersion(dir: string, name: string) {
  try {
    return JSON.parse(readFileSync(join(dir, "node_modules", name, "package.json"), "utf8")).version as string;
  } catch {
    return "unknown";
  }
}

// ---------------------------------------------------------------- main
async function main() {
  const spec = MODELS[config.modelId];
  if (!spec) fail(`unknown modelId ${config.modelId} (known: ${Object.keys(MODELS).join(", ")})`);
  const modelPath = join(SHARED_MODELS, spec.file);
  // --deep-model: the backend holds the deep model's GGUF (the fast model is installed for the engine, never loaded).
  const deepSpec = cli.deepModel ? MODELS[cli.deepModel] : null;
  if (cli.deepModel && !deepSpec) fail(`unknown --deep-model ${cli.deepModel} (known: ${Object.keys(MODELS).join(", ")})`);
  const genPath = deepSpec ? join(SHARED_MODELS, deepSpec.file) : modelPath;
  const checks: (readonly [string, string])[] = [[genPath, (deepSpec ?? spec).sha256], [join(SHARED_MODELS, EMBED_FILE), EMBED_SHA256]];
  if (cli.installed) {
    if (!cli.installed.includes(config.modelId)) fail(`--installed must include the config's modelId ${config.modelId}`);
    for (const id of cli.installed) {
      if (!MODELS[id]) fail(`--installed: unknown model ${id}`);
      if (id !== config.modelId) checks.push([join(SHARED_MODELS, MODELS[id].file), MODELS[id].sha256]);
    }
  }
  for (const [p, h] of checks) {
    const got = await sha256File(p);
    if (got !== h) fail(`sha256 mismatch ${p}: ${got}`);
  }
  const packFiles = await resolveKit();
  const t0 = performance.now();
  const env = await setupAppRetrieval(packFiles);
  const setupMs = performance.now() - t0;
  const A: any = await import(join(ROOT, "src/routing/answer.ts"));
  const pure: any = await import(join(ROOT, "src/rag/pure.ts"));
  const Rt: any = await import(join(ROOT, "src/rag/retrieve.ts"));
  const PL: any = await import(join(ROOT, "src/rag/ptLexicon.ts"));
  const PLA: any = await import(join(ROOT, "src/rag/ptLexiconAsset.ts"));
  const LE: any = await import(join(ROOT, "src/inference/LlamaEngine.ts"));
  const PERS: any = await import(join(ROOT, "src/constants/personalities.ts"));
  // The answer persona, as the chat passes it (ChatScreen: the saved personality's systemPrompt + styleReminder).
  // settings.personalityId: one of the tree's own PERSONALITIES; settings.personaSystemPrompt (+ personaStyleReminder):
  // a literal override (a persona under test). Default: the app's DEFAULT_PERSONALITY_ID ("succinct"). Neither key
  // reaches the engine's answer settings.
  const { personalityId, personaSystemPrompt, personaStyleReminder, ...answerSettings } = config.settings as Record<string, any>;
  if (personalityId !== undefined && personaSystemPrompt !== undefined) fail("settings: personalityId and personaSystemPrompt are exclusive");
  let persona: { id: string; systemPrompt: string; styleReminder?: string };
  if (personaSystemPrompt !== undefined) {
    persona = { id: "literal", systemPrompt: String(personaSystemPrompt), ...(personaStyleReminder !== undefined ? { styleReminder: String(personaStyleReminder) } : {}) };
  } else {
    const id = personalityId ?? PERS.DEFAULT_PERSONALITY_ID ?? "succinct";
    if (!(PERS.PERSONALITIES ?? []).some((p: any) => p.id === id)) fail(`settings.personalityId "${id}" is not one of this tree's personalities`);
    const p = PERS.getPersonality(id);
    persona = { id, systemPrompt: p.systemPrompt, ...(p.styleReminder !== undefined ? { styleReminder: p.styleReminder } : {}) };
  }
  const personaSha = createHash("sha256").update(JSON.stringify([persona.systemPrompt, persona.styleReminder ?? null])).digest("hex");
  const treeEntry = env.catalog.find((m: any) => m.id === config.modelId);
  const entry: any = treeEntry ?? ADAPTER_CATALOG[config.modelId];
  if (!entry) fail(`model ${config.modelId} not in this tree's catalog`);
  const deepTreeEntry = cli.deepModel ? env.catalog.find((m: any) => m.id === cli.deepModel) : undefined;
  const deepEntry: any = cli.deepModel ? deepTreeEntry ?? ADAPTER_CATALOG[cli.deepModel] : null;
  if (cli.deepModel && !deepEntry) fail(`deep model ${cli.deepModel} not in this tree's catalog`);
  if (cli.deepModel && answerSettings.deepModelId !== cli.deepModel)
    fail(`--deep-model ${cli.deepModel} needs settings.deepModelId = "${cli.deepModel}" (got ${JSON.stringify(answerSettings.deepModelId)})`);

  // Per-request recorders, reset before each answer.
  let started = 0;
  let currentItem = "";
  let events: TraceEvent[] = [];
  let raw: SourceRef[] = [];
  let gens: Generation[] = [];
  /** Per item: multi-pass runs (MP4B) and the ms of every retrieve after the engine's first (DEEPITER follow-ups) or inside multi-pass. */
  let multipassRuns = 0;
  let retrieveCalls = 0;
  let extraRetrieveMs: number[] = [];
  const at = () => round1(performance.now() - started);

  const server = cli.backend === "server";
  let currentModelId: string | null = null;
  const onGeneration = (g: Generation) => {
    gens.push(g);
    events.push({ tMs: at(), type: "other", kind: "generation", origin: "adapter", promptTokens: g.promptTokens, outputTokens: g.predictedTokens,
                  prefillMs: round1(g.promptMs), decodeMs: round1(g.predictedMs), temperature: g.temperature, timedOut: g.timedOut,
                  ...(g.hidden ? { reasoningTokens: g.hidden.reasoningTokens, firstTextMs: round1(g.firstTextMs),
                                   firstReasoningMs: g.hidden.firstReasoningMs === null ? null : round1(g.hidden.firstReasoningMs),
                                   thinkingBudgetExceeded: g.hidden.budgetExceeded } : {}),
                  ...(cli.installed ? { modelId: currentModelId } : {}) });
  };
  // --installed: the catalog entries of every installed model (tree catalog first, then the adapter's).
  const installedEntries: any[] = (cli.installed ?? []).map((id) => {
    const e = env.catalog.find((m: any) => m.id === id) ?? ADAPTER_CATALOG[id];
    if (!e) fail(`--installed: ${id} not in this tree's catalog`);
    return e;
  });
  const engine: Awaited<ReturnType<typeof makeEngine>> & Partial<Awaited<ReturnType<typeof makeServerEngine>>> = cli.installed
    ? (await makeMultiEngine(installedEntries.map((e) => ({ id: e.id, filename: e.filename, path: join(SHARED_MODELS, MODELS[e.id].file) })),
                             R0.seed, R0.temperature, onGeneration, (id) => (currentModelId = id))) as any
    : await (server ? makeServerEngine : makeEngine)(genPath, (deepEntry ?? entry).filename, R0.seed, R0.temperature, onGeneration);
  const llm = { id: entry.id, label: entry.label, filename: entry.filename, sizeBytes: entry.sizeBytes ?? 0,
                roles: deepEntry ? ["fast"] : entry.capabilities?.roles ?? ["fast"], isDefault: true, answerTier: entry.answerTier };
  // --deep-model (card deep-tier-streamed-moe §6b): two installed LLMs, the fast one active (never loaded: the backend
  // holds the deep one), the deep one explicit in settings.deepModelId -> resolveDeepModel takes it with no speed check,
  // estimateFit null keeps it usable, alwaysComplete sends planAnswer to the deep branch (k 6 / 400 ctx / 200 / no think).
  const deepLlm = deepEntry
    ? { id: deepEntry.id, label: deepEntry.label, filename: deepEntry.filename, sizeBytes: deepEntry.sizeBytes ?? 0,
        roles: ["reasoning"], isDefault: false, answerTier: deepEntry.answerTier }
    : null;
  // Guard: a generate may only run on the model the backend holds (a fast or verifier call would silently use it).
  // Not with --installed: there the adapter loads whichever installed model the engine asks for.
  const guard = modelGuard((deepEntry ?? entry).filename, (deepEntry ?? entry).id);
  if (!cli.installed) {
    const load0 = engine.load.bind(engine);
    const gen0 = engine.generate.bind(engine);
    engine.load = (async (filename: string, opts?: any) => { guard.onLoad(filename, opts?.meta?.modelId); return load0(); }) as any;
    engine.getModelInfo = () => ({ filename: guard.loadedFilename });
    engine.generate = async (o: any) => {
      const v = guard.check();
      if (v) throw new Error(v);
      if (cli.dumpPrompts)
        appendFileSync(cli.dumpPrompts, JSON.stringify({ itemId: currentItem, ...(o.messages ? { messages: o.messages } : { prompt: o.prompt }),
                                                         nPredict: o.nPredict ?? null, enableThinking: o.enableThinking ?? null }) + "\n");
      return gen0(o);
    };
  }
  // Sonar exp-30 (health11): learned emergency detector. Desktop stand-in for llama.rn: a llama-server built from
  // llama.rn's vendored llama.cpp (b11010 + converter patch), pooling mean, -np 1; the head runs in JS (emergencyHead.ts).
  // BOAR_DETECTOR=mmbert|e5, BOAR_DETECTOR_URL, BOAR_DETECTOR_HEAD (json), BOAR_DETECTOR_THR. Unset -> lexical (health10).
  let emergencyScore: ((q: string, turns: string[]) => Promise<{ p: number; fire: boolean } | null>) | undefined;
  if (process.env.BOAR_DETECTOR) {
    const EH: any = await import(join(ROOT, "src/routing/emergencyHead.ts"));
    const head = JSON.parse(readFileSync(process.env.BOAR_DETECTOR_HEAD!, "utf8"));
    const url = process.env.BOAR_DETECTOR_URL!, thr = process.env.BOAR_DETECTOR_THR ? Number(process.env.BOAR_DETECTOR_THR) : EH.DETECTOR_THRESHOLD;
    const embed = async (content: string, norm: number): Promise<number[]> => {
      const r = await fetch(`${url}/embedding`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ content, embd_normalize: norm }) });
      if (!r.ok) throw new Error(`detector ${r.status}`);
      const j: any = await r.json(); const e = Array.isArray(j) ? j[0].embedding : j.embedding;
      return Array.isArray(e[0]) ? e[0] : e;
    };
    const countTokens = async (content: string): Promise<number> => {
      const r = await fetch(`${url}/tokenize`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ content, add_special: false }) });
      if (!r.ok) throw new Error(`detector tokenize ${r.status}`);
      return ((await r.json()) as any).tokens.length;
    };
    // Any failure throws -> answer.ts catches -> null -> the lexical predicate (fail safe, never "not emergency").
    emergencyScore = async (q, turns) => {
      const text = await EH.detectorText(turns, q, countTokens);
      const p = head.kind === "mmbert-cls"
        ? EH.mmbertProbability(head, await embed(text, -1))
        : EH.e5Probability(head, await embed(`query: ${q.replace(/\s+/g, " ").trim()}`, 2), await embed(`query: ${text}`, 2));
      return { p, fire: p >= thr };
    };
  }

  // Route gate (GATEFID): only with BOAR_ROUTE_GATE=1 and an engine that offers it; one other/route-gate event per call.
  const gate0 = (engine as any).nextTokenProbs?.bind(engine);
  if (gate0 && gateEnabled())
    (engine as any).nextTokenProbs = async (messages: any[], opts: any) => {
      if (!cli.installed && guard.check()) return null;
      const t = performance.now();
      const r = await gate0(messages, opts);
      events.push({ tMs: at(), type: "other", kind: "route-gate", origin: "adapter", promptTokens: r?.promptTokens ?? null, top: gateTop(r?.probs), ms: round1(performance.now() - t) } as any);
      return r?.probs ?? null;
    };
  else delete (engine as any).nextTokenProbs;
  // MP4B: settings.alwaysComplete with no deep model -> planAnswer's multi-pass (decompose -> research x n -> synthesize) runs
  // the tree's own runDeepResearch (src/services/orchestrator.ts, imported, not copied). It generates through the tree's
  // llamaEngine singleton: its generate / hasEmbeddedChatTemplate are set, as instance properties, to this runner's engine
  // (model guard, generation events and the sampler included). Its direct retrieve calls are logged through the resolve hook
  // above (retrieve events with via "multipass"). Any other config: the stub below, as before.
  const multipassWired = answerSettings.alwaysComplete === true && !deepEntry;
  let runMultipass: (...a: any[]) => Promise<any> = async () => { throw new Error("multipass is not wired in the desktop-node adapter (alwaysComplete=false)"); };
  if (multipassWired) {
    LE.llamaEngine.generate = async (o: any) => {
      const n = gens.length;
      const text = await engine.generate(o);
      // LlamaEngine calls onTimeout when its timer stops a stage; the runner's engine aborts the same way, so tell the orchestrator.
      if (gens.length > n && gens.at(-1)!.timedOut) o.onTimeout?.();
      return text;
    };
    LE.llamaEngine.hasEmbeddedChatTemplate = () => engine.hasEmbeddedChatTemplate();
    (globalThis as any).__boarEvalOrchestratorRetrieve = async (real: (q: string, k: number, ...r: any[]) => Promise<ChunkLike[]>, q: string, k: number, ...rest: any[]) => {
      const t = performance.now();
      try {
        const chunks = await real(q, k, ...rest);
        raw.push(...chunks.map(sourceRef));
        events.push({ tMs: at(), type: "retrieve", origin: "adapter", via: "multipass", query: q, k, n: chunks.length, ms: round1(performance.now() - t),
                      sources: chunks.map(sourceRef) } as any);
        extraRetrieveMs.push(performance.now() - t);
        return chunks;
      } catch (e: any) {
        events.push({ tMs: at(), type: "retrieve", origin: "adapter", via: "multipass", query: q, k, n: 0, ms: round1(performance.now() - t), error: String(e?.message ?? e) } as any);
        throw e;
      }
    };
    const MP: any = await import(join(ROOT, "src/services/orchestrator.ts"));
    runMultipass = async (...a: any[]) => { multipassRuns++; return MP.runDeepResearch(...a); };
  }
  const records: any[] = [];
  const answerer = A.createAnswerer({
    engine,
    // The engine's only retrieval dependency, wrapped: what it returns here is retrieval.raw (before any gate).
    retrieve: async (q: string, k: number, o?: unknown) => {
      const t = performance.now();
      try {
        const chunks: ChunkLike[] = await Rt.retrieve(q, k, o); // o: optional retrieve opts (VITALPACK-ADD: {packs}); ignored by older trees
        raw.push(...chunks.map(sourceRef));
        events.push({ tMs: at(), type: "retrieve", origin: "adapter", query: q, k, n: chunks.length, ms: round1(performance.now() - t),
                      sources: chunks.map(sourceRef) });
        if (retrieveCalls++ > 0) extraRetrieveMs.push(performance.now() - t);
        return chunks;
      } catch (e: any) {
        events.push({ tMs: at(), type: "retrieve", origin: "adapter", query: q, k, n: 0, ms: round1(performance.now() - t), error: String(e?.message ?? e) });
        throw e;
      }
    },
    knowledgeReady: async () => {},
    englishNames: (q: string) => PL.englishNamesIn(q, PLA.ptLexicon()),
    getSettings: async () => ({ quickFirst: true, alwaysComplete: false, largeModelConfirmedIds: [], loadCrashedIds: [], ...answerSettings }),
    listInstalledLlms: async () =>
      cli.installed
        ? installedEntries.map((e) => ({ id: e.id, label: e.label, filename: e.filename, sizeBytes: e.sizeBytes ?? 0,
                                         roles: e.capabilities?.roles ?? ["fast"], isDefault: e.id === config.modelId, answerTier: e.answerTier }))
        : deepLlm ? [llm, deepLlm] : [llm],
    // --installed: no saved pick, so the engine's default rule chooses (selectAnswerModel -> pickDefaultAnswerModel).
    getActiveModelId: async () => (cli.installed ? null : llm.id),
    runMultipass,
    assemblePrompt: pure.assemblePrompt,
    assembleChatMessages: pure.assembleChatMessages,
    answerPrefix: pure.answerPromptPrefix,
    now: () => performance.now(),
    contextSize: LE.defaultContextSize,
    deviceRamBytes: () => Number(process.env.BOAR_EVAL_RAM_BYTES),
    getGeoProviders: () => env.geo,
    getModelSpeeds: async () => new Map(),
    recordExecution: async (r: any) => { records.push(r); },
    memoryBytes: () => process.memoryUsage().rss,
    ...(emergencyScore ? { emergencyScore } : {}),
  });
  const ctx = { systemPrompt: persona.systemPrompt, styleReminder: persona.styleReminder, maxTokens: 512 };

  const adapterSha = createHash("sha256").update(readFileSync(fileURLToPath(import.meta.url))).update(readFileSync(join(HERE, "trace.ts")))
    .update(existsSync(join(HERE, "server.ts")) ? readFileSync(join(HERE, "server.ts")) : "").digest("hex").slice(0, 12);
  const versions: Record<string, string> = {
    "node-llama-cpp": packageVersion(HERE, "node-llama-cpp"),
    ...(server ? { "llama-server": engine.version! } : {}),
    node: process.version,
    engine: treeCommit,
    adapter: `desktop-node@${adapterSha}`,
    protocol: PROTOCOL_VERSION,
    "model.sha256": spec.sha256,
    ...(cli.installed ? { installed: cli.installed.join(","), "installed.sha256": cli.installed.map((id) => MODELS[id].sha256.slice(0, 12)).join(",") } : {}),
    ...(treeEntry ? {} : { "catalog.entry": "adapter" }),
    ...(deepEntry ? { "deep.model": deepEntry.id, "deep.model.sha256": deepSpec!.sha256, ...(deepTreeEntry ? {} : { "deep.catalog.entry": "adapter" }) } : {}),
    "embedding.sha256": EMBED_SHA256,
    corpus: cli.corpus,
    persona: persona.id,
    "persona.sha256": personaSha,
    ...(patchSha ? { "engine.patch.sha256": patchSha } : {}),
    ...(process.env.BOAR_READ_KEEPANS === "1" ? { "engine.read_keepans": "1", "engine.read_keepans_tokens": String(Number(process.env.BOAR_READ_KEEPANS_TOKENS || 250)) } : {}),
    ...(process.env.BOAR_READ_GROUND === "1" ? { "engine.read_ground": "1", "engine.read_ground_bar": process.env.BOAR_READ_GROUND_BAR ?? "0.6" } : {}),
    ...(process.env.BOAR_SAMPLER_JSON ? { "sampler.override": process.env.BOAR_SAMPLER_JSON } : {}),
    ...(process.env.BOAR_READ_SEQ ? { "engine.read_seq": process.env.BOAR_READ_SEQ } : {}),
    ...(server && process.env.BOAR_SERVER_EXTRA_ARGS ? { "server.extra_args": process.env.BOAR_SERVER_EXTRA_ARGS.trim() } : {}),
    ...(cli.places.length ? { places: cli.places.map((p) => p.split("/").pop()).join(",") } : {}),
    ...(ITEM_LOCATIONS ? { "item.locations.sha256": createHash("sha256").update(readFileSync(process.env.BOAR_ITEM_LOCATIONS!)).digest("hex") } : {}),
    ...(shard ? { parallel: String(shard.n), "parallel.timing": PARALLEL ? "invalid (null; raw in other/timing-raw)" : "valid" } : {}),
  };
  const host = `${os.cpus()[0]?.model} cpu x${cli.threads} (${os.platform()} ${os.release()}, ${cli.gpu ? "gpu" : "cpu"} generation${server ? ", llama-server" : ""})`;

  mkdirSync(dirname(cli.out!), { recursive: true });
  writeFileSync(cli.out!, "");
  const runStart = performance.now();
  let errors = 0;
  for (const req of requests) {
    const q = req.item;
    env.point.current = q.context?.lat !== undefined && q.context?.lon !== undefined ? { lat: q.context.lat, lon: q.context.lon, accuracyM: 20 } : null;
    events = [];
    raw = [];
    gens = [];
    multipassRuns = 0;
    retrieveCalls = 0;
    extraRetrieveMs = [];
    records.length = 0;
    let cited: number[] | undefined;
    let err: { code: string; message: string } | null = null;
    let res: any;
    started = performance.now();
    currentItem = q.id;
    if (q.history) events.push({ tMs: 0, type: "other", kind: "history", origin: "adapter", turns: q.history.turns.length });
    const injected = !env.point.current ? ITEM_LOCATIONS?.get(q.id) : undefined;
    if (injected) {
      env.point.current = { lat: injected.lat, lon: injected.lon, accuracyM: 20, ageS: 0 };
      events.push({ tMs: 0, type: "other", kind: "item-location", origin: "adapter", accuracyM: 20, ageS: 0 } as any);
    }
    const sqlCalls: Map<string, number> | undefined = (globalThis as any).__boarSqlCalls;
    if (process.env.BOAR_EVAL_SQL_COUNT === "1") sqlCalls?.clear();
    try {
      res = await answerer.answer({ query: q.question }, (e: any) => {
        events.push(mapEvent(e, at(), cli.eventSourceText));
        if (e.type === "done") {
          if (Array.isArray(e.cited)) cited = e.cited;
          if (e.error) err = { code: String(e.error.code ?? "unknown"), message: String(e.error.message ?? "") };
        }
      }, answerContext(ctx, q)).done;
    } catch (e: any) {
      err = { code: "exception", message: String(e?.stack ?? e?.message ?? e) };
    }
    // BOAR_EVAL_SQL_COUNT=1: this item's async SQLite calls per database file (expo-sqlite shim), for bridge-call arms (P-8).
    if (process.env.BOAR_EVAL_SQL_COUNT === "1" && sqlCalls) {
      const byDb = Object.fromEntries([...sqlCalls].sort());
      events.push({ tMs: at(), type: "other", kind: "sql-calls", origin: "adapter", byDb, total: [...sqlCalls.values()].reduce((a, b) => a + b, 0) });
    }
    // A generate refused by the model guard fails the item, whatever the engine made of the error.
    const guardViolations = guard.take();
    if (guardViolations.length) err = { code: "adapter:model-guard", message: guardViolations.join("; ") };
    const total = performance.now() - started;
    const gen = gens.at(-1);
    // Passage level, as returned (no dedupe): several passages of one article share title + section.
    const kept: SourceRef[] = (res?.sources ?? []).map(sourceRef);
    const reasonCodes: string[] = res?.receipt?.reasonCodes ?? [];
    const warnings = warningCodes(events);
    if (gens.some((g) => g.timedOut)) warnings.push("adapter:generation-timeout");
    if (PARALLEL) warnings.push("adapter:parallel-timing-invalid");
    const trace = {
      protocol: PROTOCOL_VERSION,
      runId: req.runId,
      itemId: q.id,
      question: q.question,
      engine: { commit: treeCommit, arm: treeArm, dirty: !!patchSha },
      runtime: {
        adapter: "desktop-node",
        ...(server ? { backend: "llama-server" } : {}),
        host,
        model: config.modelId,
        sampler: { seed: req.seed, ...(gen ? { temperature: gen.temperature } : req.temperature !== undefined ? { temperature: req.temperature } : {}) },
        versions,
        loadAvg1m: +os.loadavg()[0].toFixed(2),
      },
      config,
      route: { task: taskOf(reasonCodes), tier: res?.tier ?? null, outcome: res?.outcome ?? null, reasonCodes,
               ...(server || gens.some((g) => g.hidden) ? { thinkingBudgetExceeded: gens.some((g) => g.hidden?.budgetExceeded) } : {}),
               // Only for always-complete configs (the only ones where multi-pass can run): other traces are unchanged.
               ...(answerSettings.alwaysComplete === true ? { mode: multipassRuns > 0 ? ("multipass" as const) : ("single" as const) } : {}) },
      retrieval: { raw, kept, dropped: droppedOf(raw, kept) },
      answer: {
        text: res?.text ?? "",
        cited: citedTitles(cited ?? res?.cited, kept),
        shown: shownTitles(events),
        declined: events.some((e) => e.type === "warning" && !!e.declined),
        weakSources: events.some((e) => e.type === "warning" && e.code === "weak_sources"),
        warnings,
      },
      timing: (PARALLEL ? invalidateTiming : (x: any) => x)({
        ttftMs: res?.receipt?.ttftMs ?? null,
        totalMs: round1(total),
        retrievalMs: res?.receipt?.retrievalMs ?? null,
        prefillMs: gen ? round1(gen.promptMs) : null,
        decodeTokPerSec: gen && gen.predictedMs > 0 ? +((gen.predictedTokens - 1) / (gen.predictedMs / 1000)).toFixed(2) : null,
        promptTokens: gen?.promptTokens ?? null,
        outputTokens: gens.reduce((s, g) => s + g.predictedTokens, 0),
        // Retrieval outside the receipt's retrievalMs (the engine's first search): DEEPITER follow-ups, multi-pass sub-questions.
        ...(extraRetrieveMs.length ? { retrievalMs2: round1(extraRetrieveMs.reduce((s, x) => s + x, 0)) } : {}),
        ...(server || gens.some((g) => g.hidden) ? hiddenTiming(gens, started) : {}),
      }, events),
      resources: server ? { peakRssMb: peakMb(gens), thermal: null, sustainedRatio: null } : null,
      events: capTokenEvents(events, cli.tokenEventsMax),
      error: err,
      createdAt: new Date().toISOString(),
    };
    const parsed = EvalTrace.safeParse(trace);
    if (!parsed.success) fail(`${q.id}: trace does not parse: ${parsed.error.issues.map((x) => `${x.path.join(".")}: ${x.message}`).join("; ")}`);
    appendFileSync(cli.out!, JSON.stringify(parsed.data) + "\n");
    if (err) errors++;
    const t = parsed.data;
    console.log(`${q.id} ${t.route.tier} ${t.route.outcome} ttft=${t.timing.ttftMs === null ? "-" : Math.round(t.timing.ttftMs)} raw=${t.retrieval.raw.length} kept=${t.retrieval.kept.length} dropped=${t.retrieval.dropped.length}${t.answer.declined ? " DECLINED" : ""}${err ? ` ERROR ${err.code}` : ""}`);
  }
  console.log(JSON.stringify({ done: requests.length, errors, setupMs: Math.round(setupMs), modelLoadMs: Math.round(engine.loadMs), runMs: Math.round(performance.now() - runStart), out: cli.out,
                               ...(server ? { backend: "llama-server", llamaServer: engine.version, idleRssMb: mb(engine.idleRssBytes ?? null), peakRssMb: mb(engine.peakRssBytes ?? null) } : {}) }));
  await engine.close?.();
}

const mb = (b: number | null) => (b === null ? null : round1(b / 1024 ** 2));
const peakMb = (gens: Generation[]) => mb(gens.reduce<number | null>((m, g) => (g.hidden?.peakRssBytes == null ? m : Math.max(m ?? 0, g.hidden.peakRssBytes)), null));

/**
 * Hidden-reasoning timing (protocol optional fields; server backend, or node with an active thought budget): firstVisibleMs = first non-blank visible text since answer() of the
 * generation that produced the answer text; reasoningMs = its hidden thinking before that text (firstTextMs -
 * firstReasoningMs, 0 without reasoning); reasoningTokens summed over generations.
 */
function hiddenTiming(gens: Generation[], answerStart: number) {
  const g = [...gens].reverse().find((x) => x.hidden?.visibleText) ?? null;
  return {
    firstVisibleMs: g ? round1(g.hidden!.startedAt - answerStart + g.firstTextMs) : null,
    reasoningMs: g ? round1(g.hidden!.firstReasoningMs === null ? 0 : g.firstTextMs - g.hidden!.firstReasoningMs) : null,
    reasoningTokens: gens.reduce((s, x) => s + (x.hidden?.reasoningTokens ?? 0), 0),
  };
}

main().catch((e) => fail(String(e?.stack ?? e)));
