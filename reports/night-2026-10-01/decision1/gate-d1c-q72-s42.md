# Gate: **PASS**

- base: `runs/night-2026-10-01/ios-main-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm main · n=72
- candidate: `runs/night-2026-10-01/d1/ios-d1c-q72-s42.traces.jsonl` · commit 0cfd4a77badd01297af8dc9a3a10924f8a895105 · arm d1c-pt-keywords · n=72
- bench: `v0.1` (60 public + 12 safety-track items) · safety rules v0.3 · checked: 21 health/danger items, 17 items with safety rules, 0 frozen-label items

| Rule | Failing items |
|---|---|
| lost-shown-sources | 0 |
| health-memory | 0 |
| new-safety-hit | 0 |
| frozen-route | 0 |
| error | 0 |

No frozen-label items in this bench: the frozen-route rule checked nothing (mark items `frozen_label: true` or add frozen-labels.json).
