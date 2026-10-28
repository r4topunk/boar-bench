# Balance round r2 + freeze assembly (2026-10-20). Merges critique + both fact-checks; no item text invented here.
import json, sys, collections
V='<workspace>/boar-eval/bench/v0.4/'; R=V+'drafts/r2/'
L=lambda p:[json.loads(l) for l in open(p) if l.strip()]
cand=L(V+'items.candidate.jsonl')
fx={x['id']:x for x in L(R+'items-for-factcheck.jsonl')}
crit={c['id']:c for c in L(R+'critique-of-claude-by-codex.jsonl')+L(R+'critique-of-codex-by-claude.jsonl')}
fcC={x['id']:x for x in L(R+'factcheck-claude.jsonl')}; fcX={x['id']:x for x in L(R+'factcheck-codex.jsonl')}
def merge(a,b):
    s={a,b}
    if 'contradicted' in s: return 'disagreement'
    if 'supported' in s: return 'supported'
    return 'unverifiable'
def pts(i,only=None):
    cp={p['point']:p for p in fcC[i]['points']}; xp={p['point']:p for p in fcX[i]['points']}
    out=[]
    for k,t in enumerate(fx[i]['checklist'],1):
        if only and k not in only: continue
        c=cp[k]; x=xp[k]
        out.append({"point":k,"text":t,"claude":{"status":c['status'],"url":c['url']},"codex":{"status":x['status'],"url":x['url']},"merged":merge(c['status'],x['status'])})
    return out
problems=[]; final=[]; dropped=[]
EDIT={'cw-002':[4],'cw-032':[1,2,3],'cx-012':[1]}
ANCH={'cx-001':'Tell me about Japan','cx-007':'Which signature algorithms are quantum resistant?','cx-014':"Explain Mozi's views on universal love.",'cx-015':'Why does Gríma kill Saruman in The Lord of the Rings?'}
for it in cand:
    i=it['id']
    if i=='cw-034':
        new=dict(fx[i]); new['critique']={"by":"codex","verdict":crit[i]['verdict'],"reason":crit[i]['reason'],"round":"r2"}
        P=pts(i); st='checked' if all(p['merged']=='supported' for p in P) else 'pending'
        new['factcheck']={"points":P,"claude_note":fcC[i]['note'],"codex_note":fcX[i]['note'],"status":st,"round":"r2"}
        new['changelog']="2026-10-20 r2: replaced (was drill-down 'what were the main schools of thought in ancient china'; now context carry, Europe), r4to-approved balance round"
        it=new
    elif i in EDIT:
        it=json.loads(json.dumps(it)); it['checklist']=fx[i]['checklist']; it['tags']=fx[i]['tags']; it['reference_sources']=fx[i]['reference_sources']
        P=pts(i,EDIT[i]); byk={p['point']:p for p in P}
        np=[]
        for k,t in enumerate(it['checklist'],1):
            if k in byk: np.append(byk[k])
            else:
                old=it['factcheck']['points'][k-1]; assert old['merged']=='supported',(i,k); np.append(old)
        it['factcheck']['points']=np
        it['factcheck']['r2_note']={"claude":fcC[i]['note'],"codex":fcX[i]['note']}
        it['factcheck']['status']='checked' if all(p['merged']=='supported' for p in np) else 'pending'
        it['changelog']="2026-10-20 r2: point(s) %s reworded per DISAGREEMENTS.md suggested resolution (r4to-approved) and re-verified by both families"%EDIT[i]
    if i in ANCH:
        it=json.loads(json.dumps(it)); it['tags']['anchor_vexact']=True; it['tags']['anchor_vexact_question']=ANCH[i]
    if it['factcheck']['status']!='checked': problems.append(i)
    final.append(it)
for i in ['cw-037','cw-038','cw-039','cx-037','cx-038','cx-039']:
    it=dict(fx[i]); c=crit[i]
    it['critique']={"by":"codex" if i.startswith('cw') else "claude","verdict":c['verdict'],"reason":c['reason'],"round":"r2"}
    P=pts(i); st='checked' if all(p['merged']=='supported' for p in P) else 'pending'
    it['factcheck']={"points":P,"claude_note":fcC[i]['note'],"codex_note":fcX[i]['note'],"status":st,"round":"r2"}
    it['changelog']="2026-10-20 r2: new item (balance round, r4to-approved)"
    if st!='checked': problems.append(i)
    final.append(it)
for it in final: it['tags'].setdefault('anchor_vexact',False)
print('problems',problems)
for i in problems:
    it=[x for x in final if x['id']==i][0]
    print(i,[ (p['point'],p['claude']['status'],p['codex']['status']) for p in it['factcheck']['points'] if p['merged']!='supported'])
DROP={'cx-012':"Dropped at r2 re-verification (2026-10-20): the r4to-approved rewording of P1 was contradicted by Codex (live web) and, on review, by Claude: in a one-item second-price auction a seller's fixed shill bid raises the price but leaves truthful bidding weakly dominant, and fake bidder identities do not break it (false-name failures are a combinatorial/multi-unit VCG result). Rule: unresolved point -> drop the item rather than guess a third wording."}
rej=[]
for i,why in DROP.items():
    it=[x for x in final if x['id']==i][0]; final.remove(it)
    rej.append({"id":i,"writer":it['writer'],"rejected_by":"claude+codex","stage":"r2 fact-check (re-verification of edited point)","reason":why,"item":it})
print('dropped',list(DROP))
if '--write' in sys.argv:
    with open(V+'REJECTED.jsonl','a') as f:
        for r in rej: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    final.sort(key=lambda x:(x['id'][:2],int(x['id'][3:]))); open(V+'items.jsonl','w').write(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in final))
    print('wrote',len(final))
