#!/usr/bin/env python3
"""Gratis PrijsProfeet-scan. Geen niet-gecontroleerde deals publiceren."""
import json, sys, urllib.request, urllib.parse, datetime, pathlib, hashlib
BASE="https://www.prijsprofeet.nl/api/v1/search"
TERMS=["kip","kwark","skyr","eieren","zalm","tonijn","spinazie","groente","banaan","noten","wraps","melk","olijfolie","wasmiddel","vaatwastabletten","rituals","janzen","earth 46","doucheschuim","deodorant","deo","shower foam","geurstokjes","handzeep","bodylotion","douchegel","huisparfum","luchtverfrisser","sandelhout","cederhout"]
RETAILERS={"albert_heijn":"Albert Heijn","jumbo":"Jumbo","lidl":"Lidl","aldi":"Aldi","dirk":"Dirk","plus":"PLUS","hoogvliet":"Hoogvliet","vomar":"Vomar"}
PREMIUM={"rituals","janzen","earth 46","doucheschuim","deodorant","deo","shower foam","geurstokjes","handzeep","bodylotion","douchegel","huisparfum","luchtverfrisser","sandelhout","cederhout"}
FOOD={"kip","kwark","skyr","eieren","zalm","tonijn","spinazie","groente","banaan","noten","wraps","melk","olijfolie"}
TODAY=datetime.datetime.now(datetime.timezone.utc).date()
def get(term):
    params=urllib.parse.urlencode({"q":term,"page_size":50})
    url=BASE+"?"+params
    request=urllib.request.Request(url,headers={"User-Agent":"KansenradarPersoonlijk/1.0 (+https://github.com/DASPHHS/Kansenradar)","Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=25) as f:
        return json.load(f)
def scan():
    warnings=[]; out={}; successful=0
    for term in TERMS:
        try:
            data=get(term)
            if not isinstance(data.get("results"),list): raise ValueError("Geen results-lijst")
            successful+=1
            for p in data["results"]:
                if p.get("promotion_status")!="active":continue
                retailer=str(p.get("retailer") or "").lower()
                if retailer not in RETAILERS:continue
                end=str(p.get("valid_until") or "")[:10]
                if not end:continue
                try:
                    if datetime.date.fromisoformat(end)<TODAY:continue
                except ValueError:continue
                name=str(p.get("name") or "").strip()
                price=p.get("price")
                if not name or not isinstance(price,(int,float)) or price<=0:continue
                code=str(p.get("id") or p.get("ean") or hashlib.sha256((name+retailer+end).encode()).hexdigest()[:16])
                key=retailer+":"+code
                old=p.get("original_price")
                saving=p.get("savings_percentage")
                if not isinstance(saving,(int,float)):saving=None
                source=p.get("url") or p.get("product_url")
                if not isinstance(source,str) or not source.startswith("https://"):
                    source="https://www.prijsprofeet.nl/api/v1/search?"+urllib.parse.urlencode({"q":name[:55]})
                out[key]={"id":key,"title":name,"store":RETAILERS[retailer],"category":"food" if term in FOOD else "premium" if term in PREMIUM else "home","price":round(price,2),"original_price":round(old,2) if isinstance(old,(int,float)) and old>price else None,"discount_percent":round(saving,1) if saving is not None else None,"valid_until":end,"url":source,"verified":True,"note":"Aanbieding uit PrijsProfeet, controleer beschikbaarheid en afrekenprijs bij de winkel.","source":"PrijsProfeet"}
        except Exception as exc: warnings.append(term+": "+str(exc)[:180])
    if not successful:
        raise RuntimeError("Geen enkele API-aanroep gelukt: bestaand deals.json blijft ongewijzigd. "+str(warnings[:3]))
    arr=sorted(out.values(),key=lambda p:(p["discount_percent"] or 0),reverse=True)
    result={"last_updated":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),"deals":arr[:350],"warnings":warnings+["Deze API dekt alleen aangesloten supermarktproducten. Rituals/Janzen buiten supermarkten, Action, Kruidvat en dupes zijn nog niet volledig aangesloten. Geen historische prijscontrole beschikbaar op gratis API."],"sources":{"PrijsProfeet":"OK","failed_queries":len(warnings)}}
    pathlib.Path("deals.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(arr)} actieve deals, {successful} API-queries geslaagd, {len(warnings)} waarschuwingen")
if __name__=="__main__":scan()
