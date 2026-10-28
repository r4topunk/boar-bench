# health-fresh2 blind eval set

- Date: 2026-10-03
- Writer: fresh sonnet subagent with no team-file access (blind; research team has not seen the items)
- File: items.jsonl, 150 items, schema {id, lang, kind, turns[{role,text}], expected}
- Multi-turn items end on a short user turn; the critical detail is in an earlier user turn.

| lang | danger | hard_negative | total | multi-turn |
|------|--------|---------------|-------|-----------|
| en   | 30 | 20 | 50  | 14 |
| pt   | 33 | 22 | 55  | 13 |
| es   | 27 | 18 | 45  | 12 |
| all  | 90 | 60 | 150 | 39 |

Multi-turn: 27 danger, 12 hard_negative (26%).
