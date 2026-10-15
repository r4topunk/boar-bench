# Addendum 03: safety rules v0.6 + explicit v0.2 danger-item mapping

Dated 2026-10-02 evening. **Timing, stated plainly:** E3's generation on v0.2 had already started on the mini, but no v0.2
safety result had been computed or viewed by anyone; a research agent wrote v0.6 without v0.2 access (first-aid don'ts from
NHS/CDC/Ready.gov/WHO/Red Cross).

- Rules v0.6 = v0.5 + 26 forbid rules (rules.v0.6.json 3a159b68…, checker 30b91a64…); tests 78/78 reproduced by the coordinator
  in a clean shell; v0.1 mapped verdicts unchanged 0/740.
- v0.2 uses the EXPLICIT mapping in overlay.v02-danger.v0.6.json (not part of the public release: it maps private v0.2 item ids; 5 of 10 danger items mapped; 5 uncovered → judge-only safety,
  reported as such). Topic-based rule selection is not used on v0.2.
- Every v0.2 `unsafe` hit is hand-checked once by the coordinator, blind to arm labels; `review` hits adjudicated as in addendum 02.
- v0.1 and the night keep their rules (v0.4 night, v0.5 new arms on v0.1).
