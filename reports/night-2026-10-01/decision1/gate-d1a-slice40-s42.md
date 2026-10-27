# Gate: **PASS**

- base: `runs/night-2026-10-01/d1/ios-main-slice40-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm main · n=40
- candidate: `runs/night-2026-10-01/d1/ios-d1a-slice40-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm d1a-unconfirmed · n=40
- bench: `bench-d1` (80 public + 12 safety-track items) · safety rules v0.3 · checked: 0 health/danger items, 0 items with safety rules, 0 frozen-label items

| Rule | Failing items |
|---|---|
| lost-shown-sources | 0 |
| health-memory | 0 |
| new-safety-hit | 0 |
| frozen-route | 0 |
| error | 0 |

No frozen-label items in this bench: the frozen-route rule checked nothing (mark items `frozen_label: true` or add frozen-labels.json).
