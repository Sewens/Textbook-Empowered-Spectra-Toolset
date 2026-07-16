#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'backend'))
from app.services.material_spectrum_claims_service import MaterialSpectrumClaimsService
EVIDENCE=REPO/'data/releases/material-spectrum-evidence-v1.0.0'
OUT=REPO/'data/releases/material-spectrum-claims-v1.0.0'
def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def digest(path):
 h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()
def main():
 items=MaterialSpectrumClaimsService.build_claims(EVIDENCE)
 pred={}
 for item in items: pred[item['predicate']]=pred.get(item['predicate'],0)+1
 OUT.mkdir(parents=True,exist_ok=True)
 dump(OUT/'claims.json',{'release_version':'v1.0.0','run_id':'RUN_material-spectrum-claims-20260716-v1','generated_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat(),'total':len(items),'items':items})
 dump(OUT/'manifest.json',{'release_version':'v1.0.0','schema_version':'strict_material_spectrum_claims_v1','counts':{'claims':len(items),'books':len({x['book'] for x in items}),'materials':len({x['material_id'] for x in items}),'spectra':len({x['spectrum_id'] for x in items}),'by_predicate':pred},'policy':{'required_fields':['material_id','spectrum_id','evidence_id','book','page'],'frequency_rule':'material and cm-1 must occur in the same explicit material-spectrum statement','effect_rule':'explicit causal condition plus direction only','excluded':['formula token partial matches','context-only material references','generic group ranges without material-spectrum statement']}})
 (OUT/'README.md').write_text('# Strict Material-Spectrum Claims v1.0.0\n\nEvery claim has a material, spectrum, evidence span, textbook and page.\n',encoding='utf-8')
 files=sorted(x for x in OUT.iterdir() if x.is_file() and x.name!='SHA256SUMS.txt')
 (OUT/'SHA256SUMS.txt').write_text('\n'.join(digest(x)+'  '+x.name for x in files)+'\n',encoding='utf-8')
 print(json.dumps({'total':len(items),'by_predicate':pred},ensure_ascii=False))
if __name__=='__main__': main()
