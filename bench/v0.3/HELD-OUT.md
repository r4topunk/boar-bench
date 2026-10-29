# v0.3: no items were ever written

No v0.3 question file or reference answers exist, anywhere. The plan was to have the app maintainer write a held-out set outside the Claude family; that front (OF-3) was dropped before any item was written, so there is no release date to wait for and nothing is withheld. The held-out sets that did exist (bench v0.2, V-para and others, plus the v0.4 ruler) are retired and public since v1.1: see `bench/heldout/` and `bench/v0.4/`.

What this folder holds is the pre-registered plan, the item schema and the tooling, kept as a record and as a template for anyone who wants to write a new held-out set:

- `plan/`: the pre-registered analysis plan with its hash chain (`plan/SHA256SUMS`) and the metric scripts.
- `questions.schema.json`, `validate.py`, `similarity.py`, `assemble.py`: schema, validation, similarity and assembly scripts.
- `refs/`: the reference-import tooling.
- `work/`: a scratch directory for local drafts (the scripts in this folder default to it). Its contents are ignored by git and blocked by the pre-commit hook (`tools/hooks/pre-commit`; install with `git config core.hooksPath tools/hooks`). If you write a new held-out set with these tools, keep its plaintext out of git (see "Held-out policy" in the top-level `README.md`).

See `CONTRIBUTING.md` for how to contribute items.
