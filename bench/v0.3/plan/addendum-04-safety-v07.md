# Addendum 04: safety rules v0.7 — all 10 v0.2 danger items mapped

Dated 2026-10-02 evening. Rules v0.7 = v0.6 + 5 forbid rules (rip current, generator indoors, floodwater, lightning exposed,
tornado in a mobile home) from NOAA/NHC, CDC, NWS, SPC, written by a research agent without v0.2 access. Tests 96/96 reproduced
clean; v0.1 verdicts unchanged 0/740. Explicit mapping: overlay.v02-danger.v0.7.json (10/10 mapped; not part of the public release: it maps private v0.2 item ids).

**Precedence rule (stated before knowing which case applies):** if NO v0.2 safety result had been computed when this addendum
was committed, v0.7 is the v0.2 safety scorer for E3 and everything after. If any v0.2 safety result already existed, E3 stays
scored under v0.6 (addendum 03) and v0.7 applies only to runs after E3; E3 is then reported under both, v0.6 primary.
a research agent reports which case applies, with timestamps.
