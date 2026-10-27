# Vendored scorer code (SOURCE)

Copied unchanged on 2026-10-01 (jev/ on 2026-10-02) so `scorers/` does not read code from `rnd/` or `wt/` at run time. Do not edit these files: re-vendor and update the hashes. `scorers/tests/test_vendor.py` checks every hash below.

| Vendored file | Source | sha256 |
|---|---|---|
| `eval-lib/judge-core.mjs` | `wt/eval/eval/scripts/lib/judge-core.mjs` in the private workspace (wt/eval @ 0a024dba) | `521f7ad33a130e1a4b5906b9578fc78d84749fc1ad3d9e89c64600a83ac57080` |
| `eval-lib/venues.mjs` | same lib dir | `65dd53ac9d59666e8b52c00182465a2242905dba805b1a1b71363d6b734ed30e` |
| `eval-lib/firstaid-check.mjs` | same lib dir | `55092f37ca211fa768fd486f4c758f7b200aa6d8d01965340287b17d07688f4d` |
| `eval-lib/preface.mjs` | same lib dir | `9b3e4df4b476c3b539c8f4c8c6d8e2792ba9df4746d43b1ea817077ac8acb1c3` |
| `eval-lib/claude-cli.mjs` | same lib dir | `d2686d62af35c0fc0a74cd5e638876e1af4e1af6d2b4126af9b95b7b4a39cdfc` |
| `lantern/precheck.py` | `rnd/lantern/tools/precheck.py` (only `grade`, `refused`, `norm` are used) | `cb50966061f9ad9526bba2525295c340365bf8ff25cadeaab357c9c2e25e2948` |
| `safety/safety_check.py` | `rnd/bench/safety/safety_check.py` | `56f71d11c48a06559ab50f976cc4597afe07493661373f17544b58eb60bcd0bd` |
| `safety/rules.v0.3.json` | `rnd/bench/safety/rules.v0.3.json` | `544f31dc600d162b0e2945d7996ae12accf6c0c4229ab390e7b21d2e3da9f842` |
| `safety/overlay.v0.3.json` | `rnd/bench/safety/overlay.v0.3.json` | `6e2dba495af7f08f5544a282a62d106b72180022450261e9b610381f086374bd` |
| `safety/track.v0.3.jsonl` | `rnd/bench/safety/track.v0.3.jsonl` | `b7c87b1e5e2a7743cb8d5eaa3ad4b7c2ab5104ab45427f424ba7734fd3c3ec29` |

`eval-lib/claude-cli.mjs` carries one local edit (f16769e, 2026-10-05: `--effort` passthrough only); its pin was updated on 2026-10-13 (PIPELINE-AUDIT F9; previous pin c06c1e84…).

Ported (not copied byte for byte):

| boar-eval file | Source | Source sha256 | Change |
|---|---|---|---|
| `scorers/bridge.mjs` | `rnd/bench/score/bridge.mjs` | `716a655b9e03d425bfc25c482d536f72650610b86cf10a60dd6a9799e6c6b478` | eval lib path defaults to `scorers/vendor/eval-lib` |
| `scorers/score.py` | `rnd/bench/score/score.py` | `3cbf85bc67dc32cbba7b05d9ecea5895ee0e50406472deafe8777b1e4527f2f1` | answers from EvalTrace; bench from `--bench`; device block removed (latency/resources come from traces); truthfulness CI added |
| `harness/judge.mjs` | `rnd/bench/judge/judge_bench.mjs` | `7bc914135517432b75635488d668bdff6fc983612553bd375f6a4f89afcc0e24` | reads EvalTrace + bench refs; refs/questions sha checked against the refs MANIFEST instead of a hard-coded sha |

Licensing: the OSM gold files in `bench/v0.1/gold/` are © OpenStreetMap contributors, ODbL 1.0 (see their NOTICE.md).


Public re-issue: `safety/rules.v0.*.json` ship without the quoted NHS wording (rule ids, patterns, urls kept), so their hashes differ from the private files. Rows are origin paths in the private workspace, kept as provenance only; the files are vendored here. `safety/rules.v0.3.json` sha256 above is the public one.
