// ram-monitor on Node for the boar-eval desktop-node adapter: the device's RAM is SIMULATED (BOAR_EVAL_RAM_BYTES), so the app's
// own code (defaultContextSize, model picking, low-RAM rules) decides as it would on that phone. Memory info is the
// Node process's (it is not the phone's footprint).
const total = () => Number(process.env.BOAR_EVAL_RAM_BYTES || 8 * 1024 ** 3);
export function getDeviceTotalRamBytes() { return total(); }
export function getAvailableRamBytes() { return Math.round(total() * Number(process.env.BOAR_EVAL_RAM_AVAILABLE_FRACTION || 0.5)); }
export function getMemoryInfo() { const m = process.memoryUsage(); return { rssBytes: m.rss, totalPssBytes: m.rss }; }
export default { getDeviceTotalRamBytes, getAvailableRamBytes, getMemoryInfo };
