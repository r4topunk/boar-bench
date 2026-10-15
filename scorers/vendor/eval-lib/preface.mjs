// The app tells the model to open a sourceless knowledge answer by saying it is not from an offline source
// (engine-routing bdcbf8b). That "not" must never excuse a claim that follows in the same sentence.
const PREFACE = /\b(this|the|my)?\s*(answer|information|response|reply)?\s*(is|isn't|is not|does not come|doesn't come|comes|was)?\s*(not\s+)?(from|based on|drawn from|in)\s+(an?|the|any|your)?\s*offline\s+(source|library|sources|collection|pack)s?\b[^,.:;!?—–-]*[,.:;!?—–-]?|\b(esta|essa|a)?\s*(resposta|informa[çc][ãa]o)?\s*(n[ãa]o\s+)?(vem|[ée]|foi tirada|se baseia)\s+(de|do|da|em)\s+(uma\s+|nenhuma\s+)?(fonte|acervo|biblioteca|pacote)s?\s+offline\b[^,.:;!?—–-]*[,.:;!?—–-]?|\bn[ãa]o (h[áa]|encontrei) fonte offline\b[^,.:;!?—–-]*[,.:;!?—–-]?/gi;

/** Removes the offline-source preface so checks see only the claims. */
export const stripOfflinePreface = (text) => (text ?? "").replace(PREFACE, " ");
