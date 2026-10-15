Blocks commits that stage held-out plaintext: paths under `blind/`, `questions.v02+*.jsonl`, `bench/v0.3+/refs/refs*.jsonl`, `refs/web__*.jsonl`, `refs/raw/`, or any added line carrying a v0.3 item (`"id": "v03-...-NN"` + `"question"`; format-example ids 98/99 exempt). The published v0.1 questions and references (`bench/v0.1/`) are allowed.

Install once per clone: `git config core.hooksPath tools/hooks`. Test: `bash tools/hooks/test-pre-commit.sh` (builds throwaway repos with FAKE items only; exit 0 = all cases behave).

If you contribute held-out items (see `CONTRIBUTING.md`), keep the plaintext out of your PR until the release date: only hashes, ids and counts are committed.
