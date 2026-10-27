# bench v0.2/v0.3 pre-registered plan (public re-issue)

Frozen 2026-10-02 by the BOAR R&D coordinator, before any v0.2 item existed in the repository. The plan fixes the analysis, the item spec, the metric scripts and the judge prompt first, so none of them can be tuned to items or results. Items and references were added at a later freeze and are not part of this repository.

Public re-issue note: this is a cleaned copy of the private plan folder. The text was edited only to remove local filesystem paths, personal names and internal agent names; the analysis content is unchanged. Because the text changed, the hashes changed: `SHA256SUMS` here is freshly generated over every file in this folder, `COMBINED.sha256` is the sha256 of that `SHA256SUMS` file, and the addendum sums were regenerated over the (also cleaned) addendum files and the shipped safety rule files. The private (pre-edit) combined hash was `fe100e91c4d6e51bb0c18001ce5e341e3e290d05e251cd997a0c50faa252855e`; no shipped item depends on the old hashes.

The two v0.2 safety overlay files (`overlay.v02-danger.v0.6/0.7.json`) and the undecided `pack-matched.md` draft are not part of the public release. Safety rule files in `scorers/vendor/safety/` ship without the quoted NHS wording (rule ids, patterns and URLs are kept), which is why their hashes differ from the private ones.

Second re-issue (v1.0 open record, 2026-10-26): `item-spec.draft.md` (a competitor repository's name replaced by a role) and this README changed, so `SHA256SUMS` and `COMBINED.sha256` were regenerated again. The first public release (2026-10-15) had combined hash `134382692d74...`; the hash map below lists the public hashes valid for this repository. The analysis content of the plan is unchanged.

A change to any file here after release = a new dated addendum with its own sums.

## Hash map for hashes quoted in the addendum prose

The addendum texts quote the private hashes of some files (8-hex prefixes). Their public equivalents:

| file | private sha256 | public sha256 |
|---|---|---|
| `coverage_classes.py` | `fe7ba6a16896fd11c8eff10f597806f2a339f087cb22a286dd7928733a2eacd0` | `7e3ba80e80d42cb77e1dc3af6178b873833bd034b6003c084e52de30d07a0cf1` |
| `key_in_context.py` | `c9124e43f1696a7a5e82684f1a7d1bae4744ce04357d287995cf2344eb4db329` | `565ddff9a68798321c2e6e096e8748fb307e0dc81a404f2efd633aaf194626e4` |
| `rules.v0.5.json` | `385bb31e2ceedb6384f91772078609987652553f2231ea5035e48a64b6bb0337` | `964f936f90083873a377733b8930b27d609a92668555d6e562d826cb924cc0ec` |
| `rules.v0.6.json` | `3a159b6833985e5dac173278d87934688c52728c0a660873d0d9301ba9914da3` | `4df8856ee9efcadc01fb1b8679913f4cdc75aa2978e7e16f432ce5b39495c515` |
| `rules.v0.7.json` | `18c1fe24e7454d7e11a0645251d092e10cec9a00f922f2b0fc06123496931e69` | `30fcb4427aea756094d1a530084abb535aa7678b5ee591a650840ff3bf2a6bf4` |

Only the public hashes are valid for the files in this repository.
