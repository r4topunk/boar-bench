# v0.3 is held out: plaintext is not here

The v0.3 question file and its reference answers are held offline by the bench maintainers until the published release date. They are not in this repository, and they must never be committed to any git repository: only hashes, ids, counts and numbers go in.

- `bench/v0.3/work/` is a scratch directory for contributors' local drafts (the scripts in this folder default to it). Its contents are ignored by git and blocked by the pre-commit hook (`tools/hooks/pre-commit`; install with `git config core.hooksPath tools/hooks`).
- This folder keeps the schema, the validation, similarity and assembly scripts, the pre-registered plan under `plan/` (with `SHA256SUMS`), and the reference-import tooling under `refs/`.
- Claim runs on v0.3 are started by the maintainers with `--bench <private dir>`; their outputs stay private.

See `CONTRIBUTING.md` for how to contribute held-out items.
