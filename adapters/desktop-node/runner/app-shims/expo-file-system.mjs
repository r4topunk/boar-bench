// expo-file-system (legacy API) on the real file system under the directory named by the BOAR_APP_DIR env var, which plays documentDirectory.
import { copyFile, mkdir, readFile, readdir, rename, rm, stat, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = process.env.BOAR_APP_DIR;
if (!ROOT) throw new Error("expo-file-system shim: set BOAR_APP_DIR");
export const documentDirectory = pathToFileURL(ROOT.endsWith("/") ? ROOT : ROOT + "/").href;
export const cacheDirectory = documentDirectory + "cache/";
const p = (uri) => (uri.startsWith("file://") ? fileURLToPath(uri) : uri);
export const EncodingType = { UTF8: "utf8", Base64: "base64" };

export async function getInfoAsync(uri) {
  try {
    const s = await stat(p(uri));
    return { exists: true, isDirectory: s.isDirectory(), size: s.size, modificationTime: s.mtimeMs / 1000, uri };
  } catch {
    return { exists: false, isDirectory: false, uri };
  }
}
export const readAsStringAsync = (uri, o) => readFile(p(uri), o?.encoding === "base64" ? "base64" : "utf8");
export const writeAsStringAsync = (uri, s, o) => writeFile(p(uri), s, o?.encoding === "base64" ? "base64" : "utf8");
export const makeDirectoryAsync = (uri) => mkdir(p(uri), { recursive: true }).then(() => {});
export const deleteAsync = (uri) => rm(p(uri), { recursive: true, force: true });
export const readDirectoryAsync = (uri) => readdir(p(uri));
export const copyAsync = ({ from, to }) => copyFile(p(from), p(to));
export const moveAsync = ({ from, to }) => rename(p(from), p(to));
export async function getFreeDiskStorageAsync() { return 50e9; }
export async function downloadAsync() { throw new Error("expo-file-system shim: no downloads in the eval"); }
export function createDownloadResumable() { throw new Error("expo-file-system shim: no downloads in the eval"); }
export default { documentDirectory, cacheDirectory, EncodingType, getInfoAsync, readAsStringAsync, writeAsStringAsync, makeDirectoryAsync, deleteAsync, readDirectoryAsync, copyAsync, moveAsync, getFreeDiskStorageAsync, downloadAsync, createDownloadResumable };
