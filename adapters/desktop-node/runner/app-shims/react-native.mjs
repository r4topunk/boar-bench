// the simulated device's platform (BOAR_EVAL_PLATFORM=ios|android), so the app's platform branches run as on it.
const OS = process.env.BOAR_EVAL_PLATFORM || "node";
export const Platform = { OS, select: (o) => o[OS] ?? o.default ?? o.native ?? o.ios };
export default { Platform };
