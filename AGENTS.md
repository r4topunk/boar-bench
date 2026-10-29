# AGENTS.md (boar-bench)

Notes for people and coding agents who work in this repository.

- Contract first: anything an adapter writes must parse with `packages/protocol` `EvalTrace`. Scorers read traces only.
- The engine under test is the app maintainer's open-source Android/iOS app (see `BOM.md`); this repository never edits it. Engine trees are built with `git archive <sha>` and run on a second machine ("the mini") by `adapters/desktop-node/setup.sh` and `run.sh`.
- Heavy jobs: run one CPU-heavy job at a time per machine and keep at least 15 GiB of free disk (`BOAR_EVAL_MIN_FREE_GIB`). An optional wrapper command (`BOAR_EVAL_WRAP`) can put a lock around a run. The remote shell may be fish, so wrap remote commands in `bash -lc '...'`.
- The retired held-out sets are committed on purpose since v1.1 (`bench/heldout/`, `bench/v0.4/`). For any new held-out set you write, never commit its reference answer text (`bench/**/refs/*.jsonl`) or item text before its release date. `tools/hooks/pre-commit` blocks the common leaks; install it with `git config core.hooksPath tools/hooks`.
- Language: code, docs and commits in English.
