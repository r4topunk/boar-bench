// The protocol as the runner imports it. On the MacBook: the workspace package. On the mini setup.sh replaces this
// file with `export * from "./vendor/protocol"` (a copy of packages/protocol/src/index.ts + zod), since the mini's
// shared node_modules have no zod.
export * from "@boar-eval/protocol";
