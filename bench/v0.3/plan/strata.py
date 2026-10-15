# Per-category ratio on v0.1 (Android 4B) and stratified vs plain two-level bootstrap: does a declared category mix narrow the CI?
import json, collections, numpy as np
B="runs/night-2026-10-01/"
Q={json.loads(l)["id"]:json.loads(l) for l in open("bench/v0.1/questions.public.jsonl")}
K=("correctness","completeness","usefulness"); mr=lambda s: sum(s[k] for k in K)/3
def load(run):
    J=collections.defaultdict(list)
    for l in open(B+run+".judgments.jsonl"):
        r=json.loads(l)
        if r.get("ok"): J[r["queryId"]].append(r["mapped"])
    return {q:((mr(v[0]["boar"])+mr(v[1]["boar"]))/2,(mr(v[0]["ref"])+mr(v[1]["ref"]))/2) for q,v in J.items() if len(v)==2}
runs=[load("and-qwen-s42"),load("and-qwen-s43")]
items=sorted(set(runs[0])&set(runs[1]))
cat=lambda q:{"danger-situation":"danger","travel-local":"travel","travel-practical":"travel"}.get(Q[q]["category"],Q[q]["category"])
S=np.array([[r[q][0] for q in items] for r in runs]); R=np.array([[r[q][1] for q in items] for r in runs])
print("per-category ratio (2 runs):")
C=collections.defaultdict(list)
for i,q in enumerate(items): C[cat(q)].append(i)
for c,ix in sorted(C.items(),key=lambda x:-len(x[1])): print(f"  {c:16} n={len(ix):2} ratio {S[:,ix].sum()/R[:,ix].sum():.3f}")
rng=np.random.default_rng(11)
def boot(strat,Bn=4000):
    out=[]; n=len(items)
    for _ in range(Bn):
        if strat: ii=np.concatenate([rng.choice(ix,len(ix)) for ix in C.values()])
        else: ii=rng.integers(0,n,n)
        rr=rng.integers(0,2,(len(ii),2))
        out.append(S[rr,ii[:,None]].mean(1).sum()/R[rr,ii[:,None]].mean(1).sum())
    lo,hi=np.percentile(out,[2.5,97.5]); return (hi-lo)/2
print(f"half-width plain {boot(False):.4f}  stratified by category {boot(True):.4f}")
