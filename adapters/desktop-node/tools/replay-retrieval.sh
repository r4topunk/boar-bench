#!/usr/bin/env bash
# Retrieval-only replay of BOAR's real retrieve() (no LLM, no judge); usage at the top of replay-retrieval.ts.
H="$(cd "$(dirname "$0")" && pwd)"; exec "$H/../node_modules/.bin/tsx" "$H/replay-retrieval.ts" "$@"
