# Bill of materials: models, packs and large files (never copied here)

TL;DR: the benchmark, harness and data in this repository run without any of these files. Regenerating our traces (README, step 2) needs the engine at a pinned commit, the three models and the knowledge packs below. Everything is pinned by sha256 so you can check what you downloaded. Pins come from `bench/v0.1/corpus-manifest.json`. public; reachable through the author's fork https://github.com/r4topunk/boar-app is the app maintainer's public repository (the handle is withheld by policy; ask the author for the URL).

## Engine under test

| What | Pin |
|---|---|
| App engine ("shared engine") | commit `0cfd4a77` of the app maintainer's open-source app (public; reachable through the author's fork https://github.com/r4topunk/boar-app), used by the P2 run profiles; arm patches in `adapters/desktop-node/arms/` apply on top of it |
| Run profiles | `adapters/desktop-node/configs/*.json` (P2 = iPhone-13 class, temperature 0 and 0.7 variants) |
| Desktop adapter runtime | Node 24 (`node:sqlite`), `node-llama-cpp` 3.21.1 in the runner tree, optional `llama-server` build b11010 (llama.cpp) for `--backend server` |

## Models (GGUF, Q4_K_M unless noted)

| id | sha256 | licence | source |
|---|---|---|---|
| `qwen2.5-1.5b-instruct-q4km` | `1adf0b11065d8ad2e8123ea110d1ec956dab4ab038eab665614adba04b6c3370` | per the upstream model card (Qwen) | https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/9eadc66189c7641e1ddd226b8267a9119b2ce2d4/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf |
| `qwen3-4b-instruct-2507-q4km` | `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` | per the upstream model card (Qwen) | https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/a06e946bb6b655725eafa393f4a9745d460374c9/Qwen3-4B-Instruct-2507-Q4_K_M.gguf |
| `bge-small-en-v1.5-q8` (embeddings, Q8_0) | `ec38e8da142596baa913124ae50550de284b6916bf59577ef2f0cb9660c2f514` | per the upstream model card (BAAI bge) | https://huggingface.co/CompendiumLabs/bge-small-en-v1.5-gguf/resolve/d32f8c040ea3b516330eeb75b72bcc2d3a780ab7/bge-small-en-v1.5-q8_0.gguf |

Other models appear in arm READMEs and reports (for example a 35B mixture-of-experts deep tier, 1.7B and Gemma-class models). They are not pinned in this repository: their pins are in the arm criteria and in the `boar-research` repository. The emergency-detector model used in some profiles is not released (its base-model licence is unknown). Sizes of the three GGUF files above: not recorded here (UNKNOWN; read them from the source pages).

## Knowledge packs

| id | bytes | sha256 | licence | source |
|---|---:|---|---|---|
| `corpus-standard` (Wikipedia essentials, JSON) | n/a | `2aeff76db48098851e1304fb37dc8013d9facf9214395897e7e05f276f85d2ff` | CC BY-SA 4.0 (Wikipedia) | `https://raw.githubusercontent.com/r4topunk/boar-app/9e46dc4d8f9a95bc7716194b94117f769504c0e0/assets/corpus/corpus-standard.json` |
| `corpus-full` (JSON) | n/a | `6d602003bb9da59200e3e55b75b9e15bb073a4b9b1357da2c2d47b2803c570be` | CC BY-SA 4.0 (Wikipedia) | `https://raw.githubusercontent.com/r4topunk/boar-app/9e46dc4d8f9a95bc7716194b94117f769504c0e0/assets/corpus/corpus-full.json` |
| `wiki-vital5` (Wikipedia Vital Articles level 5 introductions, SQLite) | 163,647,488 | `d3b87d562baba3489f6878bf99783f50d504db94c347029771e53f6d1aecc666` | CC BY-SA 4.0 | `https://github.com/UPSTREAM_REPO/boar-app/releases/download/knowledge-pack-v1/wiki-vital5.sqlite` |
| `boar-crypto` (SQLite) | 36,093,952 | `ae9fbd2c7a46a46a815d46d0283e7b192adb4c342b38a2adc4881e8f9d8831fb` | mixed: CC0 (EIPs, ERCs, specs), MIT (ethereum.org), CC BY-SA 4.0 (Wikipedia, Yellow Paper), per-BIP permissive | https://huggingface.co/datasets/r4topunk/boar-packs/resolve/a55c1ec8a5fe8bbda99c4197c33474637bef1958/topics/boar-crypto.sqlite |
| `boar-wikivoyage-en` (SQLite) | 351,092,736 | `ff8595e32f56b8b84e20464afd8bf88532d47d2d82d799e3df8489440004b66e` | CC BY-SA 4.0 (Wikivoyage) | https://huggingface.co/datasets/r4topunk/boar-packs/resolve/9557c7b2a50a1c37fdf36d41db4cd0fdc8c33c0b/wiki/en/boar-wikivoyage-en.sqlite |

The self-test sets in `bench/selftest/` were written against the packs of the dataset https://huggingface.co/datasets/r4topunk/boar-packs (Stack Exchange QA packs, MedlinePlus, first aid, CIA World Factbook, Simple English Wikipedia, NIST, visa requirements, preparedness). Per-pack cards and licences are in the `boar-research` repository (`packs/`).

OSM venue tiles used by device runs: pin UNKNOWN (downloaded per city at run time, see `places` in `bench/v0.1/corpus-manifest.json`).

## Large files not copied

| What | Size | Why not here | How to get it |
|---|---:|---|---|
| Retrieval replay caches (`runs/replay-cache`, `-rb1`, `-v7`, `-v7st`, `-x2b`, SQLite) | 1.11 GB, 104 MB, 232 MB, 26 MB, 101 MB | derived from the packs above, not content | `adapters/desktop-node/tools/replay-retrieval.sh` regenerates them from the packs (about 8 s per replay, no model) |
| Run traces and judgments (`runs/`) | about 1.8 GB | embed answers, retrieved third-party text and (for some directories) held-out items | not released; a filtered `traces-v0.1` release is an option |
| Judge-labeller response cache, judge usage ledger | n/a | no value / not method | not released |

No file in this repository is larger than 1 MB; the 20 MB rule of the release was never reached.
