// expo-sqlite on node:sqlite: the methods the app's db.ts / packs.ts call. Databases opened by name live in
// <BOAR_APP_DIR>/SQLite/<name> (as on the phone); a path with a directory is opened as is (packs).
import { DatabaseSync } from "node:sqlite";
import { mkdirSync, rmSync } from "node:fs";
import { dirname, isAbsolute, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = process.env.BOAR_APP_DIR;
// BOAR_EVAL_SQL_COUNT=1: count every async call (on the phone, each one crosses the JS<->native bridge) per database file
// (globalThis.__boarSqlCalls, basename -> calls); the adapter reads and resets it per item. Off by default.
const COUNT = process.env.BOAR_EVAL_SQL_COUNT === "1";
const calls = (globalThis.__boarSqlCalls ??= new Map());
const tick = (key) => { if (COUNT) calls.set(key, (calls.get(key) ?? 0) + 1); };
function pathFor(name, directory) {
  const n = name.startsWith("file://") ? fileURLToPath(name) : name;
  if (isAbsolute(n)) return n;
  const dir = directory ? (directory.startsWith("file://") ? fileURLToPath(directory) : directory) : join(ROOT, "SQLite");
  return join(dir, n);
}
function wrap(db, key = "?") {
  const params = (p) => (p === undefined ? [] : Array.isArray(p) ? p : [p]);
  const api = {
    raw: db,
    async execAsync(sql) { tick(key); db.exec(sql); },
    async getAllAsync(sql, ...p) { tick(key); return db.prepare(sql).all(...params(p.length > 1 ? p : p[0])); },
    async getFirstAsync(sql, ...p) { tick(key); return db.prepare(sql).get(...params(p.length > 1 ? p : p[0])) ?? null; },
    async runAsync(sql, ...p) { tick(key); const r = db.prepare(sql).run(...params(p.length > 1 ? p : p[0])); return { changes: Number(r.changes), lastInsertRowId: Number(r.lastInsertRowid) }; },
    async withTransactionAsync(work) {
      db.exec("BEGIN");
      try { await work(); db.exec("COMMIT"); } catch (e) { db.exec("ROLLBACK"); throw e; }
    },
    async withExclusiveTransactionAsync(work) {
      db.exec("BEGIN EXCLUSIVE");
      try { await work(api); db.exec("COMMIT"); } catch (e) { db.exec("ROLLBACK"); throw e; }
    },
    async prepareAsync(sql) {
      const st = db.prepare(sql);
      return {
        async executeAsync(...p) { tick(key); const r = st.run(...params(p.length > 1 ? p : p[0])); return { changes: Number(r.changes), lastInsertRowId: Number(r.lastInsertRowid), async getAllAsync() { return []; } }; },
        async finalizeAsync() {},
      };
    },
    async closeAsync() { try { db.close(); } catch {} },
    closeSync() { try { db.close(); } catch {} },
  };
  return api;
}
export async function openDatabaseAsync(name, options, directory) {
  const path = pathFor(name, directory);
  mkdirSync(dirname(path), { recursive: true });
  return wrap(new DatabaseSync(path, options?.readOnly ? { readOnly: true } : {}), path.split("/").pop());
}
export function openDatabaseSync(name, options, directory) {
  const path = pathFor(name, directory);
  mkdirSync(dirname(path), { recursive: true });
  return wrap(new DatabaseSync(path), path.split("/").pop());
}
export async function deleteDatabaseAsync(name, directory) {
  const path = pathFor(name, directory);
  for (const f of [path, path + "-wal", path + "-shm", path + "-journal"]) rmSync(f, { force: true });
}
export default { openDatabaseAsync, openDatabaseSync, deleteDatabaseAsync };
