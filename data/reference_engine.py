"""Reference eligibility engine (tri-state logic). Used to validate the spec's expected outputs."""
import json, itertools

T,F,U="TRUE","FALSE","UNKNOWN"
CURRENT_YEAR=2026

def derive(p):
    d=dict(p)
    inv=p.get("investment_plant_machinery_inr"); to=p.get("annual_turnover_inr")
    if inv is None or to is None: d["enterprise_size"]=None
    elif inv<=2.5e7 and to<=1e8: d["enterprise_size"]="micro"
    elif inv<=2.5e8 and to<=1e9: d["enterprise_size"]="small"
    elif inv<=1.25e9 and to<=5e9: d["enterprise_size"]="medium"
    else: d["enterprise_size"]="large"
    g=p.get("owner_gender"); sc=p.get("social_category")
    if g=="female" or sc in ("sc","st"): d["female_or_scst"]=True
    elif g in (None,"prefer_not") or sc in (None,"prefer_not"): d["female_or_scst"]=None
    else: d["female_or_scst"]=False
    # PMEGP special category
    if g=="female" or sc in ("sc","st","obc","minority") or p.get("is_ex_serviceman") or p.get("is_differently_abled") or g=="transgender":
        d["pmegp_special"]=True
    elif sc in (None,"prefer_not") or g in (None,"prefer_not"): d["pmegp_special"]=None
    else: d["pmegp_special"]=False
    # similar loans (Vishwakarma)
    loans=[l for l in p.get("existing_govt_loans",[]) if l.get("scheme") in ("pmegp","mudra","pm_svanidhi") and l.get("year",0)>=CURRENT_YEAR-5]
    if not loans: d["similar_loan_last_5y"]=False
    elif all(l.get("repaid") for l in loans): d["similar_loan_last_5y"]=None   # exception may apply -> unknown
    else: d["similar_loan_last_5y"]=True
    # Udyogini income
    inc=p.get("family_annual_income_inr")
    if p.get("is_widow") or p.get("is_differently_abled"): d["udyogini_income_ok"]=True
    elif inc is None: d["udyogini_income_ok"]=None
    elif sc in ("sc","st"): d["udyogini_income_ok"]=inc<200000
    elif sc in ("general","obc","minority"): d["udyogini_income_ok"]=inc<150000
    else: d["udyogini_income_ok"]= True if inc<150000 else (False if inc>=200000 else None)
    return d

def ev_cond(c,d):
    if "all" in c:
        rs=[ev_cond(x,d) for x in c["all"]]
        return F if F in rs else (U if U in rs else T)
    return ev_op(d.get(c["field"]),c["op"],c.get("value"))

def ev_op(v,op,val):
    if v is None: return U
    if op=="is_true": return T if v is True else F
    if op=="is_false": return T if v is False else F
    if op=="eq": return T if v==val else F
    if op=="neq": return T if v!=val else F
    if op=="in": return T if v in val else F
    if op=="not_in": return T if v not in val else F
    if op=="gte": return T if v>=val else F
    if op=="lte": return T if v<=val else F
    if op=="gt": return T if v>val else F
    if op=="lt": return T if v<val else F
    if op=="between": return T if val[0]<=v<=val[1] else F
    raise ValueError(op)

def evaluate_scheme(s,d):
    results=[]
    for c in s["criteria"]:
        if "when" in c:
            w=ev_cond(c["when"],d)
            if w==F: results.append((c,"N/A")); continue
            if w==U: results.append((c,U)); continue
        v=d.get(c["field"])
        if v is not None and c.get("unknown_values") and v in c["unknown_values"]: r=U
        else: r=ev_op(v,c["op"],c.get("value"))
        results.append((c,r))
    hard=[(c,r) for c,r in results if c["hard"] and r!="N/A"]
    fails=[c for c,r in hard if r==F]; unk=[c for c,r in hard if r==U]
    if s["status"]=="announced": status="WATCHLIST"
    elif s["kind"]=="registration" and any(c["field"]=="udyam_registered" and r==F for c,r in results): status="NOT_APPLICABLE"
    elif fails and all(c.get("fix") for c in fails) and len(fails)<=2: status="NEAR_MISS"
    elif fails: status="NOT_ELIGIBLE"
    elif unk: status="LIKELY"
    else: status="ELIGIBLE"
    met=sum(1 for c,r in hard if r==T)
    return {"status":status,"met":met,"total":len(hard),"unknown":len(unk),"fails":[c["id"] for c in fails],"results":[(c["id"],r) for c,r in results]}

def mudra_tier(a):
    if a<=50000: return "Shishu"
    if a<=500000: return "Kishore"
    if a<=1000000: return "Tarun"
    return "Tarun Plus"

def estimate(s,d):
    """returns dict(grant_min, grant_max, credit_max)"""
    g0=g1=0; cr=0
    if s["id"]=="pmegp" and d.get("project_cost_inr"):
        cap=5000000 if d["business_activity"]=="manufacturing" else 2000000
        base=min(d["project_cost_inr"],cap); area=d.get("area_type","urban")
        r=s["rates"]; sp=d.get("pmegp_special")
        lo=r["general"][area] if sp is not True else r["special"][area]
        hi=r["special"][area] if sp is not False else r["general"][area]
        g0,g1=round(base*lo),round(base*hi)
        own=r['own_contribution']['special' if sp is True else 'general']; cr=round(base*(1-own))
    elif s["id"]=="ka_udyogini":
        loan=min(d.get("loan_amount_needed_inr") or 300000,300000)
        sc=d.get("social_category")
        gen=min(round(loan*0.30),90000); scst=min(round(loan*0.50),150000)
        if sc in ("sc","st"): g0=g1=scst
        elif sc in ("general","obc","minority"): g0=g1=gen
        else: g0,g1=gen,scst
        cr=loan
    elif s["id"]=="pm_vishwakarma": g0=g1=15000; cr=300000
    elif s["id"]=="mudra": cr=min(d.get("loan_amount_needed_inr") or 0,2000000)
    elif s["id"]=="pm_svanidhi": cr=15000
    elif s["id"]=="me_card": cr=500000
    elif s["id"]=="cgtmse": cr=d.get("loan_amount_needed_inr") or 0
    return {"grant_min":g0,"grant_max":g1,"credit":cr}

def best_paths(evals,schemes,conflicts):
    cand=[sid for sid,e in evals.items() if e["status"] in ("ELIGIBLE","LIKELY","NEAR_MISS") and schemes[sid]["kind"]!="registration" and e["est"]["grant_max"]>0]
    excl=set()
    for c in conflicts:
        if c["type"]=="mutually_exclusive": excl|={tuple(sorted(x)) for x in itertools.combinations(c["schemes"],2)}
        if c["type"]=="anchor_excludes":
            for o in c["schemes"]:
                if o!=c["anchor"]: excl.add(tuple(sorted((c["anchor"],o))))
    best=[]
    for n in range(len(cand),0,-1):
        for combo in itertools.combinations(cand,n):
            if any(tuple(sorted(pr)) in excl for pr in itertools.combinations(combo,2)): continue
            gmax=sum(evals[s]["est"]["grant_max"] for s in combo)
            gmin=sum(evals[s]["est"]["grant_min"] for s in combo)
            best.append((gmax,gmin,combo))
    best.sort(key=lambda x:(-x[0],-len(x[2])))
    # keep maximal distinct paths
    out=[]
    for g in best:
        if not any(set(g[2])<=set(o[2]) for o in out): out.append(g)
    return out[:3]

def run_all(base_dir):
    import os
    data=json.load(open(os.path.join(base_dir,"schemes.seed.json"),encoding="utf-8"))
    P=json.load(open(os.path.join(base_dir,"personas.json"),encoding="utf-8"))
    S={s["id"]:s for s in data["schemes"]}
    out={}
    for pid,p in P.items():
        d=derive(p); evals={}
        for s in data["schemes"]:
            e=evaluate_scheme(s,d); e["est"]=estimate(s,d); evals[s["id"]]=e
        paths=best_paths(evals,S,data["conflicts"])
        out[pid]={"schemes":{sid:{"status":e["status"],"met":e["met"],"total":e["total"],"unknown":e["unknown"],
                                  "fails":e["fails"],"grant_min":e["est"]["grant_min"],"grant_max":e["est"]["grant_max"],
                                  "credit":e["est"]["credit"]} for sid,e in evals.items()},
                  "best_paths":[{"schemes":list(g[2]),"grant_min":g[1],"grant_max":g[0]} for g in paths]}
    return out

if __name__=="__main__":
    import os, sys
    base=os.path.dirname(os.path.abspath(__file__))
    out=run_all(base)
    for pid,r in out.items():
        print("==",pid)
        for sid,v in r["schemes"].items(): print(f"  {sid:22s} {v['status']:14s} met {v['met']}/{v['total']} unk {v['unknown']} fails {v['fails']} grant {v['grant_min']}-{v['grant_max']} credit {v['credit']}")
        for pth in r["best_paths"]: print("  PATH", pth["schemes"], "grant", pth["grant_min"], "-", pth["grant_max"])
    exp=os.path.join(base,"expected.json")
    if os.path.exists(exp) and "--write" not in sys.argv:
        ok = json.load(open(exp,encoding="utf-8")) == json.loads(json.dumps(out))
        print("\nMATCHES expected.json" if ok else "\nMISMATCH with expected.json")
    else:
        json.dump(out,open(exp,"w",encoding="utf-8"),indent=1,ensure_ascii=False); print("\nwrote expected.json")
