#!/usr/bin/env python3
"""coverage_classes.py: knowledge-coverage class per bench item, for bench v0.2's claim report (a research agent S1, F3).

Blind-safe by design. The coordinator or the writer agent runs it on the frozen v0.2 items; a research agent never opens them. The tool writes
per-item classes ONLY to --out (a path the runner controls) and prints aggregate counts only.

Class per item (needs the item's answer key: precheck must_any/must_k, and its reference_sources):
  in-kit-key      the answer key appears in the installed kit's text of a referenced article (any pack)
  in-kit-no-key   a referenced article is installed, but the key is not in its installed text (e.g. intro-only)
  not-in-kit      no referenced article is installed
  unkeyed         no must_any/must_k (venue, first-aid, judge-only items): not classified

Installed text per title is resolved like key_in_context.py's article mode: format-2 packs (articles + zstd blocks),
the bundled corpus (corpus.json at a given engine commit), wiki-vital5 chunks (only with --vital5). Titles come from the
item's en.wikipedia.org / en.wikivoyage.org reference URLs; Wikivoyage titles are tried in the Wikivoyage pack.

Usage (runner):  coverage_classes.py ITEMS.jsonl --out classes.json [--vital5] [--pack PATH ...]
Report the judged ratio per class next to the overall ratio. That is what "the knowledge BOAR ships" can explain.
"""
import argparse, collections, json, sys, urllib.parse

sys.argv_backup = sys.argv
sys.argv = ["x"]
exec(open(__file__.replace("coverage_classes.py", "key_in_context.py")).read().split('if __name__ == "__main__":')[0])
sys.argv = sys.argv_backup

def titles_of(item):
    out = []
    for u in item.get("reference_sources", []):
        for host in ("en.wikipedia.org/wiki/", "en.wikivoyage.org/wiki/"):
            if host in u:
                out.append((urllib.parse.unquote(u.split(host, 1)[1]).split("#")[0].replace("_", " "), "wikivoyage" in host))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items"); ap.add_argument("--out", required=True); ap.add_argument("--vital5", action="store_true")
    a = ap.parse_args()
    res = Resolver(a.vital5)
    classes = {}
    for line in open(a.items):
        if not line.strip(): continue
        q = json.loads(line); g = q.get("grading", {})
        if not (g.get("must_any") or g.get("must_k")): classes[q["id"]] = "unkeyed"; continue
        texts = []
        for title, voyage in titles_of(q):
            ref = {"title": f"Wikivoyage: {title}" if voyage else title, "source": "https://en.wikivoyage.org/" if voyage else None}
            tx = res.text(ref)
            if tx is not None: texts.append(tx)
        classes[q["id"]] = "not-in-kit" if not texts else ("in-kit-key" if key_hit("\n".join(texts), g) else "in-kit-no-key")
    json.dump(classes, open(a.out, "w"), indent=1)
    c = collections.Counter(classes.values())
    print(f"items {len(classes)}: " + ", ".join(f"{k} {c[k]}" for k in ("in-kit-key", "in-kit-no-key", "not-in-kit", "unkeyed")))

if __name__ == "__main__":
    main()
