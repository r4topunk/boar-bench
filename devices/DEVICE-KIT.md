# Device test kit: the 72-item eval on r4to's iPhone 13 and the app maintainer's Android (2026-10-02)

## TL;DR

- **What:** the same 72 questions that ran on desktop tonight (bench v0.1 public 60 + safety track 12), run inside the real app on two phones. Both phones use the in-app answer pipeline: a request file goes into the app, `answerEval` writes one row per question, and the rows come back.
- **Engine:** shared main `0cfd4a77`.
  - iPhone: build `d8e83200` (= main + PR #62 `src/ui-ios`) plus the bench commit, rebased locally to `00747371`.
  - Android: main `0cfd4a77` dev client.
  - Outside the UI folders, the engine is byte-identical to `0cfd4a77`, so every trace uses `--commit 0cfd4a77`.
- **Priority:** P1 baseline (2 reps per config), then P2 (the desktop-winning arms, one build each), then P3 (speed/thermal).
- **Results come back as `rows.jsonl`.**
  - r4to: they land straight in `boar-eval/runs/devices/2026-10-02/ios/`.
  - the app maintainer: zip `eval-results/boar-eval/` and send it.
- **Scoring:** `scorers/convert_device.py`, then `harness/judge.mjs`, `report.py`, `diff.py` and `devices/agreement.py` against the desktop trace of the same config (§5).
- **Time:**
  - iPhone: P1 ≈ 1 h including the build; P3 adds 1–1.5 h.
  - Android: P1 ≈ 3–3.5 h for both models × 2 reps; Qwen alone ≈ 1.2 h.

```
questions72.jsonl ──make_requests.py──► devices/requests/*.request.json | questions72.device.jsonl
        │                                        │
desktop-node (night runs)                 phone app (answerEval, pipeline "answer")
        │                                        │ rows.jsonl
        ▼                                        ▼
  EvalTrace ◄──────── agreement.py / diff.py ──── convert_device.py → EvalTrace → judge → report
```

## 1. What to run, in priority order

| P | Config | iPhone 13 (r4to) | Android (the app maintainer) | Reps | Desktop counterpart (night 2026-10-01) |
|---|---|---|---|---|---|
| **P1** | baseline, shared main, quick mode (`quickFirst` on, `alwaysComplete` off), kit crypto + Wikivoyage | Qwen2.5-1.5B (`ios-q15-quick`) | Qwen3-4B-2507 (`and-qwen3-4b-quick`), then Gemma 4 E4B (`and-gemma4-e4b-quick`) | 2 | `ios-main-s42/s43`, `and-qwen-s42/s43`, `and-gemma-s42` |
| **P2** | arms that win on desktop tonight: one build each (table below) | same 72, `--request-id be-ios-q15-quick-<arm>-rN` | same 72, `--tag <arm>` | 2 | the arm's desktop traces |
| **P3** | speed/thermal: is the first answer slow after setup or install? Does `n_threads`/batch matter? | P3a `p3-speed9x3` unplugged + P3b `bench-iphone.mjs` grid | P3a `*-p3speed` only (no llama.rn bench on Android) | 1 | none (device-only axis) |

Android order, so that a short day still covers both models: **qwen r1 → gemma r1 → qwen r2 → gemma r2**. Skip Gemma if the phone has under 8 GB RAM: the file is 5.2 GB.

### P2 arms (coordinator fills this in the morning from `rnd/research/QUEUE.md`)

Every patch in `adapters/desktop-node/arms/` is JS-only and applies cleanly on the device tree `00747371` (`git apply --check`, 2026-10-01 23:00):
- `a1-danger-v1`
- `cmpsplit`, `cmpsplit-v2`
- `d1a-unconfirmed`, `d1c-pt-keywords`
- `leadgate`
- `main+46`

| Arm (tag: lowercase, digits, dashes) | Patch | sha256 | Desktop result (Δ, inside/outside MDE) | iPhone build | Android |
|---|---|---|---|---|---|
| _e.g. `cmpsplit`_ | `arms/cmpsplit.patch` | `arms/cmpsplit.patch.sha256` | _fill_ | _fill_ | _fill_ |
| | | | | | |

Rule: only arms that won on desktop **outside the MDE** go to the phones, and every arm runs ≥ 2 reps. An arm is a different requestId (§2.4, §3.3). With the baseline's id, the app would *resume* and reuse the baseline's answers.

## 2. iPhone 13 (r4to)

Phone rules:
- Install with `devicectl install` (it keeps the container). Never uninstall, never delete models.
- `GGML_METAL_DEVICES=0`; `eval-iphone.mjs` sets it on launch.
- No WebDriverAgent while it generates.
- Airplane mode for every measured run.
- **After any install, r4to opens the app once from the icon, with mobile data on.**

Device: UDID `<DEVICE_UDID>`, bundle **`<APP_BUNDLE_ID>`**. Note that `eval-iphone.mjs` defaults to `<DEFAULT_BUNDLE_ID>`, so always pass `--bundle`. Host string for traces: `iPhone14,5 iOS 26.6.2`.

Commands below are fish-safe. The scripts run from the worktree `<workspace>/wt/plumb-bench-uiios`, which holds `00747371` with `scripts/eval-iphone.mjs` and `scripts/bench-iphone.mjs`.

### 2.1 Build (the mini, before r4to is needed)

One build serves P1 and P3: `00747371` = `d8e83200` + the bench commit (§6), built with **`EXPO_PUBLIC_DEVICE_EVAL=1`**. Without that flag, a release build ignores requests (`src/eval/deviceEvalGate.ts`).

Use the usual device-build route from `handoff/Harbor.md` (Mini tooling):
- **Tree:** `git archive` + `rsync --delete` into `<runner>-ios-build`, excluding `node_modules`, `/ios`, `.expo` and `build.log`.
- **Build:** `<runner>/ios-gui/device-cpu.command` from the GUI session.
- **Prebuild:** a full one. `modules/ram-monitor` (Swift) changed, so `SKIP=1` is not allowed.

```fish
git -C <workspace>/boar-app archive -o /tmp/evalbench-0074737.tar 00747371   # commit is local (detached), not pushed
# → mini: unpack into <runner>-ios-build, EXPO_PUBLIC_DEVICE_EVAL=1 in the build env, run device-cpu.command (GUI session)
# → back on the MacBook:
codesign --verify --deep --strict <workspace>/builds/ios/device/evalbench-0074737/std/BOAR.app
```

Fallback if the bench commit misbehaves: build `d8e83200` itself with the flag. P1 works the same; only P3b is lost.

### 2.2 Install, the one icon launch, prep (network ON, r4to present)

```fish
xcrun devicectl device install app --device <DEVICE_UDID> <workspace>/builds/ios/device/evalbench-0074737/std/BOAR.app
# r4to: open BOAR once FROM THE ICON with mobile data on; wait for the chat
cd <workspace>/wt/plumb-bench-uiios
node scripts/eval-iphone.mjs --bundle <APP_BUNDLE_ID> --questions <workspace>/boar-eval/devices/requests/questions72.device.jsonl --only vit-hum-001 --models qwen2.5-1.5b-instruct-q4km --install-assets qwen2.5-1.5b-instruct-q4km,boar-crypto,boar-wikivoyage-en --quick-first on --always-complete off --dataset prep --request-id be-ios-prep --out <workspace>/boar-eval/runs/devices/2026-10-02/ios/be-ios-prep
```

The prep run does three things:
- proves that this build picks up requests (it fails within 5 min with a clear message if not);
- downloads crypto (0.04 GB) and Wikivoyage (0.35 GB) if they are missing;
- leaves the phone ready.

Kit evidence: retrieval only matches desktop when the kits match (§5.3).

```fish
xcrun devicectl device info files --device <DEVICE_UDID> --domain-type appDataContainer --domain-identifier <APP_BUNDLE_ID> --json-output <workspace>/boar-eval/runs/devices/2026-10-02/ios/kit.json
python3 -c 'import json;fs={f["name"]:f["metadata"]["size"] for f in json.load(open("<workspace>/boar-eval/runs/devices/2026-10-02/ios/kit.json"))["result"]["files"]};[print(n,fs[n]) for n in sorted(fs) if n.endswith((".sqlite",".gguf"))]'
```

### 2.3 P1: two reps (airplane mode ON, Wi-Fi off, USB plugged)

```fish
cd <workspace>/wt/plumb-bench-uiios
node scripts/eval-iphone.mjs --bundle <APP_BUNDLE_ID> --questions <workspace>/boar-eval/devices/requests/questions72.device.jsonl --models qwen2.5-1.5b-instruct-q4km --install-assets qwen2.5-1.5b-instruct-q4km,boar-crypto,boar-wikivoyage-en --quick-first on --always-complete off --dataset bench-v0.1-72 --timeout-min 90 --request-id be-ios-q15-quick-r1 --out <workspace>/boar-eval/runs/devices/2026-10-02/ios/be-ios-q15-quick-r1
# ~10 min cool-down (screen off), then the same command with -r2 in --request-id and --out
```

How the run behaves:
- `--install-assets` is a no-op when the files are present, so nothing goes to the network.
- The script relaunches the app (`--terminate-existing`), so the first question pays the model load. It is recorded in the receipt.
- Keep BOAR in the foreground with the phone unlocked.
- If iOS kills the app, re-run the **same** command: the same requestId resumes from the last answered question.

P1 runs **plugged** (the transport is USB devicectl). Its latency numbers are therefore "charging" numbers. Clean speed numbers come from P3.

### 2.4 P2 arms

For each arm in the §1 table, the iPhone needs its own build. That means one install and **one icon launch by r4to** each time.

```fish
git -C <workspace>/boar-app worktree add --detach <workspace>/wt/dev-arm-ARM 00747371
cd <workspace>/wt/dev-arm-ARM
shasum -a 256 <workspace>/boar-eval/adapters/desktop-node/arms/ARM.patch   # must equal arms/ARM.patch.sha256
git apply <workspace>/boar-eval/adapters/desktop-node/arms/ARM.patch; and git add -A; and git -c user.name=Plumb -c user.email=plumb@local commit -qm "device arm ARM (local only)"
# mini build as §2.1 with this sha (JS-only change: SKIP=1 prebuild reuse is fine), install, icon launch, airplane mode, then §2.3 with:
#   --request-id be-ios-q15-quick-ARM-r1 --out …/ios/be-ios-q15-quick-ARM-r1
```

### 2.5 P3: speed and thermal (UNPLUGGED, airplane mode)

**P3a: is the first answer slow after an install or a heavy load?**
- **Questions:** 9 items that generate ≥ 60 tokens on desktop, asked 3 times (`p3-speed9x3.device.jsonl`, ids `<id>__k1..k3`).
- **What it measures:** the per-row receipt gives model load, TTFT, prefill and tok/s in order, so it shows "slow first answer" (k1 vs k2/k3, `loadMs`) and drift over ~10 min of load.
- **Variant A, right after P1 r2 (hot):** send it plugged, then **unplug as soon as it prints `running`**. The CLI gives up about 5 min after the cable goes, but the app keeps going. Plug back in when it's done and pull:

```fish
node scripts/eval-iphone.mjs --bundle <APP_BUNDLE_ID> --questions <workspace>/boar-eval/devices/requests/p3-speed9x3.device.jsonl --models qwen2.5-1.5b-instruct-q4km --quick-first on --always-complete off --dataset p3speed --request-id be-ios-q15-p3speed-hot-r1 --out <workspace>/boar-eval/runs/devices/2026-10-02/ios/be-ios-q15-p3speed-hot-r1
xcrun devicectl device copy from --device <DEVICE_UDID> --domain-type appDataContainer --domain-identifier <APP_BUNDLE_ID> --source Documents/eval/be-ios-q15-p3speed-hot-r1.answer.jsonl --destination <workspace>/boar-eval/runs/devices/2026-10-02/ios/be-ios-q15-p3speed-hot-r1/rows.jsonl
```

- **Variant B, after ≥ 15 min idle, unplugged, screen off (cool):** same commands with `-cool-r1`.
- **Clean-install case:** "first answer after a *clean setup*" (25 s at 0.5 tok/s, review/IPHONE-uiios-0e68e26.md) can't be reproduced without an uninstall, which the rules forbid. What this kit measures is "after install + cold launch" and "hot vs cool".

**P3b: llama.rn settings grid** (`n_threads` 2–6, `n_ubatch`/`n_batch`, flash attention, q8 KV), about 40–90 min.

```fish
node scripts/bench-iphone.mjs --model qwen2.5-1.5b-instruct-q4km --reps 3 --cool nominal --out <workspace>/boar-eval/runs/devices/2026-10-02/ios/bench-grid
# send plugged, unplug after "request sent"; if the CLI gives up, plug back in at the end and pull:
xcrun devicectl device copy from --device <DEVICE_UDID> --domain-type appDataContainer --domain-identifier <APP_BUNDLE_ID> --source Documents/bench/REQUEST_ID.jsonl --destination <workspace>/boar-eval/runs/devices/2026-10-02/ios/bench-grid/rows.jsonl
```

`REQUEST_ID` is printed by the script and is also in `…/bench-grid/request.json`. The rows carry thermal state before and after each run, the battery and the charging flag.

## 3. Android (the app maintainer)

Why not `npm run eval:device`: on main it only sends the legacy request (`models/adaptive/queries`) and can't send our 72 questions through `pipeline: "answer"`. `devices/android-run.sh` does the same adb transport (run-as, base64), polls the same status file and pulls the rows. It was tested on the MacBook against a fake adb; it has **not** run on a real phone yet.

### 3.1 Once

1. Phone: USB debugging on, `adb devices` shows `device`, screen timeout long (or "stay awake while charging").
2. Computer: the app repository at `0cfd4a77` (public fork: https://github.com/r4topunk/boar-app), `npm ci`, and a **debug dev client** (`npx expo run:android`) if yours predates main's native deps.
3. Metro in **dev mode**: `npx expo start --localhost`, plus `adb reverse tcp:8081 tcp:8081`.
   - **Not `--no-dev`.** On main, `src/ui-android/ChatScreen.tsx` only polls for requests when `__DEV__` is true (`ui-ios` uses `DEVICE_EVAL_ON`). Production-mode JS would never pick the request up.
   - Consequence: JS-side stages (retrieval, ranking) run as dev-mode JS, so their timings are pessimistic. Model speed is native and unaffected.
4. Get from r4to:
   - `boar-eval/devices/android-run.sh`;
   - `devices/requests/and-*.request.json`;
   - for P2, the arm `.patch` files with their `.sha256`.
5. Free space: Qwen3-4B 2.5 GB + Gemma 4 E4B 5.2 GB + packs 0.4 GB. The first request downloads what's missing, so use Wi-Fi.

### 3.2 P1

BOAR is open on the chat with its models loaded. Between requests, close the Evaluation screen (✕) so the chat polls again.

```bash
bash android-run.sh and-qwen3-4b-quick.request.json 1      # → eval-results/boar-eval/be-and-qwen3-4b-quick-r1/
bash android-run.sh and-gemma4-e4b-quick.request.json 1
bash android-run.sh and-qwen3-4b-quick.request.json 2      # after ~10 min cool-down
bash android-run.sh and-gemma4-e4b-quick.request.json 2
```

How a run behaves:
- **What gets saved:** progress prints every 15 s. Each run folder holds:
  - `rows.jsonl` (the result);
  - `status.json`;
  - `device.txt` (model, SoC, Android version, RAM);
  - `kit.txt` (models and packs on the phone);
  - `battery-before.txt` and `battery-after.txt` (temperature);
  - `request.json`.
- **If Android kills BOAR:** reopen it and re-run the same line. It resumes.
- **If the script times out but the phone finishes:** run `bash android-run.sh <file> <rep> --pull-only`.
- **First use:** `--dry-run` prints every adb command and touches nothing.

### 3.3 P2 arms (no rebuild: JS-only patches, Metro serves them)

```bash
git apply ARM.patch          # in the boar-app checkout at 0cfd4a77; check sha256 first
# restart Metro (dev mode), reload the app, then:
bash android-run.sh and-qwen3-4b-quick.request.json 1 --tag ARM
git apply -R ARM.patch       # back to main before the next arm
```

### 3.4 P3a

Unplug once the script prints `running`. It will give up while unplugged; plug back in at the end and run `--pull-only`.

```bash
bash android-run.sh and-qwen3-4b-quick-p3speed.request.json 1
```

There is no llama.rn settings bench on Android (P3b is iOS-only, `src/bench` is r4to's).

### 3.5 What to send back

Zip `eval-results/boar-eval/` (one folder per requestId) and send it to r4to. **`rows.jsonl` is the result**; the other files are context.

## 4. Durations (estimates; device numbers are the unknown being measured)

| Step | iPhone 13 | Android (Qwen3-4B / Gemma 4 E4B) | Basis |
|---|---|---|---|
| Build | 15–30 min on the mini (full native prebuild) | 0 if the dev client is current, else 10–20 min | Harbor builds; ram-monitor Swift changed |
| Install + icon launch | 2 min, **r4to present** | n/a | memory: an icon launch with mobile data after every install |
| Prep or downloads | 2 min (≈ 10 if packs missing) | 10–30 min the first time (up to 8.1 GB) | catalog sizes |
| **P1, one rep of 72** | **≈ 14 min** | **≈ 30 min / ≈ 45–60 min** | iPhone: 52 items ≈ 10 min (rnd/plumb/run-commands.md). Android: 59/72 items generate on desktop, ~65 output + ~450 prompt tokens each, ~25 s per answer assumed |
| P1 total (2 reps + 10 min cool-down) | ≈ 40 min | ≈ 3–3.5 h for both models | |
| P3a (27 answers) | ≈ 10 min per variant, + 15 min idle for "cool" | ≈ 15–20 min | |
| P3b grid | 40–90 min (11 configs × 3 reps, cool to nominal ≤ 180 s each) | n/a | bench-iphone defaults |

The app's own timeout per question is 240 s, after which the row is `outcome: failure` and convert_device marks it `error: timeout`.

## 5. Scoring (boar-eval, MacBook)

Put the rows under `runs/devices/2026-10-02/{ios,android}/<requestId>/rows.jsonl` (gitignored). Take `ram-gb` and the Android host from `device.txt`.

### 5.1 Commands (one config, rep 1; repeat for r2 and for each config)

```bash
# bash (from fish: run `bash` first)
cd <workspace>/boar-eval; D=runs/devices/2026-10-02; N=runs/night-2026-10-01; mkdir -p reports/devices-2026-10-02
# rows -> EvalTrace (engine commit = 0cfd4a77 for every device build here; the app build goes in --build)
python3 scorers/convert_device.py $D/ios/be-ios-q15-quick-r1/rows.jsonl --out $D/ios-q15-r1.traces.jsonl \
  --commit 0cfd4a77 --arm main --platform ios --host "iPhone14,5 iOS 26.6.2" --ram-gb 4 --build evalbench-00747371 --run-id dev1002-ios-q15-r1
python3 scorers/convert_device.py $D/android/be-and-qwen3-4b-quick-r1/rows.jsonl --out $D/and-qwen-r1.traces.jsonl \
  --commit 0cfd4a77 --arm main --platform android --host "<model> Android <ver>" --ram-gb <GB> --build main-0cfd4a77-devclient --run-id dev1002-and-qwen-r1
node harness/validate.mjs $D/*.traces.jsonl
# judge (Opus, resumable; venue items are scored by OSM, not judged)
node harness/judge.mjs --traces $D/ios-q15-r1.traces.jsonl --out $D/ios-q15-r1.judgments.jsonl --bench bench/v0.1 --system dev1002-ios-q15-r1
# 7-axis report for the config, 2 reps
python3 harness/report.py $D/ios-q15-r1.traces.jsonl --judgments $D/ios-q15-r1.judgments.jsonl \
  --repeat $D/ios-q15-r2.traces.jsonl --repeat-judgments $D/ios-q15-r2.judgments.jsonl --bench bench/v0.1 --out reports/devices-2026-10-02/ios-q15.md
# paired diff vs the desktop trace of the same config (route, sources, declines, judge Δ with MDE)
python3 harness/diff.py $N/ios-main-v5-s42.traces.jsonl $D/ios-q15-r1.traces.jsonl --labels desktop-v5-s42 iphone-r1 \
  --judgments-a $N/ios-main-v5-s42.judgments.jsonl --judgments-b $D/ios-q15-r1.judgments.jsonl --bench bench/v0.1 \
  --out reports/devices-2026-10-02/diff-desktop-iphone-q15-r1.md
# desktop <-> device agreement per key (the expected level is in §5.2)
python3 devices/agreement.py $N/ios-main-v5-s42.traces.jsonl $D/ios-q15-r1.traces.jsonl --labels desktop iphone
python3 harness/stability.py $D/ios-q15-r1.traces.jsonl $D/ios-q15-r2.traces.jsonl --judgments $D/ios-q15-r1.judgments.jsonl $D/ios-q15-r2.judgments.jsonl --out reports/devices-2026-10-02/ios-q15.stability.md
```

| Device config | Desktop traces to diff against |
|---|---|
| `ios-q15-quick` | **`ios-main-v5-s42`, `ios-main-v5-s43`** (kit + `wiki-vital5`, judged; r4to's phone has vital5, confirmed 2026-10-02 prep). `ios-main-s42/s43` only for a phone without vital5 |
| `and-qwen3-4b-quick` | `and-qwen-s42`, `and-qwen-s43` |
| `and-gemma4-e4b-quick` | `and-gemma-s42` (s43 not run yet) |
| arm `X` | the desktop traces of arm X on the same profile |

### 5.2 What "desktop ↔ device agreement" should look like (measured, not hoped)

Two references:
- **Desktop seed-to-seed:** `ios-main-s42` vs `s43` (72 items) and `and-qwen-s42` vs `s43`.
- **Historic desktop vs iPhone at the same commit:** exp-06 vs the iPhone 14de107 device run (52 items).

| Key (`devices/agreement.py`) | Desktop s42↔s43, 1.5B | Desktop s42↔s43, Qwen3-4B | Desktop↔iPhone, 14de107 | Expect tomorrow |
|---|---|---|---|---|
| task, tier, `retrieve:*`, `instant:*`, route codes (minus `context:`/`citations:`/`grounding:`) | 72/72 | 72/72 | **52/52** | all. Any miss is a bug or a kit/RAM mismatch (§5.3) |
| shown sources (title set) | 72/72 | 72/72 | **52/52** | all, if the kits match |
| declined | 59/72 | 72/72 | 44/52 | ~80–85% on the 1.5B: the decline follows the generated text (citation check) |
| identical answer text | 34/72 | 17/72 | 28/52 | about half on the 1.5B, about a quarter on the 4B. Generations differ (temperature 0.7, llama.rn vs node-llama-cpp sampler) |
| kept | n/a | n/a | n/a | **not comparable**: device rows carry only the final list, so a device trace has kept = shown |
| timing, resources | n/a | n/a | n/a | never compared desktop vs device; device numbers only |

Read it like this:
- Route and sources should match. Generations won't.
- A device run is consistent when its decline and text agreement with desktop is about the same as desktop's own seed-to-seed agreement.
- Quality deltas count only outside the MDE that `diff.py` prints (coordinator rule, QUEUE.md).

### 5.3 Known reasons route or sources can differ legitimately

- **Kit.** Desktop has the bundled essential corpus (`corpus-standard` + `corpus-full`), `boar-crypto` and `boar-wikivoyage-en`.
  - **iPhone:** r4to's phone was set up with the "Encyclopedia" package, which adds **`wiki-vital5`**, plus any places tiles. Check `kit.json`.
  - If vital5 is there, the fix is a desktop rerun with vital5 in the kit (Kiln, about 3 min per run). The alternative is to neutralize the pack on the phone, which needs r4to's OK.
  - **Android:** same check against `kit.txt`.
- **Places.** Desktop runs without places. The 4 venue items (`local-food` ×3, `travel-local` ×1) can show places on a phone that has city tiles.
- **RAM profile.** Desktop `and-*` simulated a 12 GB phone, and the engine's RAM-dependent choices (context size, low-RAM model rules) follow the real RAM. If the app maintainer's phone isn't 12 GB, rerun desktop with his RAM (`device.ramGb` in the config).
- **Android JS dev mode:** affects timing only.

## 6. iPhone bench branch readiness (`origin/feat/iphone-bench` f5fbd5c1 → `r4to:feat/ui-ios` d8e83200)

**Verdict: ready as one cherry-pick. Not ready as a full-branch rebase. Nothing pushed, no branch created.**

| Check | Result |
|---|---|
| Full rebase (`git rebase d8e83200` from f5fbd5c1) | Replays **7** commits, 6 of them old `ios/main` engine commits: `231d1dcc`, `a0b25465`, `dc3866f5`, `0ccc4911`, `577912b6`, `01daf792`. It stops at the first one: **CONFLICT `src/routing/answer.ts`** (231d1dcc). Not attempted further: those commits are fork-only engine arms (ADR-001) and must not ride along with tooling. Aborted |
| **Bench commit alone** (`git rebase --onto d8e83200 01daf792 origin/feat/iphone-bench`, done as a cherry-pick) | **1 trivial conflict**: `src/ui/BenchScreen.tsx` (a new file) is a *location* conflict. Git's directory-rename detection placed it at `src/ui-ios/BenchScreen.tsx`. Accepted as is; no content markers |
| What moved where | `src/ui/BenchScreen.tsx` → `src/ui-ios/BenchScreen.tsx`. The `src/ui/ChatScreen.tsx` hunk (bench request poll + render, same `DEVICE_EVAL_ON` gate) auto-applied to `src/ui-ios/ChatScreen.tsx`. Clean and unchanged: `modules/ram-monitor/{index.ts, ios/RamMonitorModule.swift}`, `src/bench/{modelBench.pure.ts, modelBench.ts, modelBench.test.ts}`, `scripts/bench-iphone.mjs` |
| Result | Local commit **`00747371`**, detached HEAD in worktree `<workspace>/wt/plumb-bench-uiios` |
| `tsc --noEmit` | **0 errors** (7 s) |
| `vitest run` | **186 files / 2560 tests pass**, including `src/bench` (6) and `engineBoundary` |
| `node scripts/bench-iphone.mjs --help` | loads on Node 25.9 (it needs ≥ 23.6). One harmless warning: module type not specified |
| Build impact | Native rebuild needed (ram-monitor Swift: `getThermalState`/`getPowerInfo`). Bench default bundle `<APP_BUNDLE_ID>` matches ui-ios |

Typecheck setup: the worktree's `node_modules` is a shadow folder of links to `wt/eval-inapp-build/node_modules`. Its versions match `d8e83200`'s lock for every checked dependency (navigation, reanimated, keyboard-controller, expo-network, typescript 6.0.3, vitest 5.0.1). The local `file:` modules (ram-monitor, …) are relinked to this tree, so the new Swift/TS API is the one type-checked.

To publish it later (r4to's call; nothing pushed): `git branch feat/iphone-bench-uiios 00747371`, then push to the fork. PR #62 must merge first, or the PR targets `feat/ui-ios`.

## 7. Files in this kit

| Path | What |
|---|---|
| `devices/requests/questions72.device.jsonl` | 72 × `{id, query, category}`: input of `eval-iphone.mjs --questions` |
| `devices/requests/{ios-q15-quick,and-qwen3-4b-quick,and-gemma4-e4b-quick}.request.json` | in-app request per config (validated with the app's own `parseEvalRequest` + `resolveAnswerRequest` at d8e83200; no unknown fields) |
| `devices/requests/p3-speed9x3.device.jsonl`, `and-*-p3speed.request.json` | P3a probe |
| `devices/requests/MANIFEST.json` | sha256 of every request file and of the source questions file |
| `devices/make_requests.py` | regenerates all of the above (deterministic) |
| `devices/android-run.sh` | Android sender/poller/puller (`--tag`, `--pull-only`, `--dry-run`) |
| `devices/agreement.py` | desktop ↔ device agreement per key |
| `scorers/convert_device.py` + `scorers/tests/test_convert_device.py` | answer-pipeline rows → EvalTrace (10 tests) |

## Decisions / Options / Tasks

**Decisions (made here, reversible):**
- answerAnyway is off in every request, so a device run is asked exactly like desktop.
- One iPhone build serves P1 and P3.
- Every trace says engine `0cfd4a77`; the app build is recorded in `runtime.versions.appBuild`.

**Options (for the coordinator or r4to):**
- iPhone kit parity: (a) a desktop rerun with `wiki-vital5` (recommended, non-destructive), or (b) neutralize vital5 on the phone.
- Android production-mode JS: a one-line change in the app maintainer's `ui-android` (`!__DEV__` → `!DEVICE_EVAL_ON`). His repo, his call; r4to's hands-off rule runs until Monday.

**Tasks:**
- [ ] Coordinator: fill the P2 table.
- [ ] Build `evalbench-0074737` on the mini with `EXPO_PUBLIC_DEVICE_EVAL=1`.
- [ ] r4to: install + icon launch → prep → P1 r1/r2 → P3.
- [ ] the app maintainer: P1 (4 runs) → P3a → send the zip.
- [ ] Plumb: convert, judge, report, diff, agreement; desktop rerun requests to Kiln if the kits differ.

## UNKNOWN

- How `EXPO_PUBLIC_DEVICE_EVAL=1` reaches the mini's `device-cpu.command` (env file or shell). The rc6eval, o2eval and ios-bench builds had it; no local note says where. The prep run is the check.
- Whether `uiios-d8e8320/std` (the current build on the phone) was built with the flag. Assumed not ("release build" in the review).
- the app maintainer's phone model and RAM. "F3" (Poco F3?) is named in the v1.1.0 plan only. If it has ≤ 6 GB, skip Gemma.
- Android durations: Qwen3-4B and Gemma 4 E4B have never been timed on his phone, and these are the first numbers.
- Whether devicectl reaches the iPhone wirelessly while it is unplugged. The kit assumes it doesn't and uses plug → send → unplug → replug → pull.
- Whether r4to's Wi-Fi allows the HF pack downloads in prep (it blocks Apple's verification). Use mobile data if it doesn't.
