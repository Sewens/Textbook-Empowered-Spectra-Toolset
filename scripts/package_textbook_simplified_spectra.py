#!/usr/bin/env python3
"""Build textbook-only release with exactly meta.json and img/ at root."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument('--accepted',required=True,type=Path);ap.add_argument('--images-root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists(): raise SystemExit(f'refusing to overwrite existing output: {args.output}')
    source=json.loads((args.accepted/'_all_books_summary.json').read_text(encoding='utf-8'));args.output.mkdir(parents=True);img_root=args.output/'img';img_root.mkdir();records=[];missing=[];copied=0
    for book_meta in source['books']:
        book=book_meta['book']; payload=json.loads((args.accepted/book/'material_spectra.json').read_text(encoding='utf-8'))
        materials={x['material_candidate_id']:x for x in payload.get('material_candidates',[])};images={x['image_candidate_id']:x for x in payload.get('image_candidates',[])};features={x['feature_candidate_id']:x for x in payload.get('feature_candidates',[])};evidence={x['evidence_id']:x for x in payload.get('evidence_spans',[])}
        for spectrum in payload.get('spectrum_candidates',[]):
            ids=[x for x in spectrum.get('image_candidate_ids',[]) if x in images]
            if not ids: continue
            rid=f'{len(records)+1:06d}'; assets=[]
            for pos,iid in enumerate(ids,1):
                im=images[iid]; rel=im.get('source_image_path') or ''; src=args.images_root/book/'unzipped'/rel
                if src.is_file():
                    name=f'{rid}_{pos:02d}_{src.name}';dst=img_root/name;shutil.copy2(src,dst);assets.append({'image_candidate_id':iid,'path':f'img/{name}','sha256':sha256(dst),'size_bytes':dst.stat().st_size,'source_image_path':rel});copied+=1
                else: missing.append({'record_id':rid,'book':book,'spectrum_id':spectrum['spectrum_candidate_id'],'image_candidate_id':iid,'source_image_path':rel})
            records.append({'record_id':rid,'record_type':'textbook_spectrum','source_scope':'textbook','book':book,'source_id':(payload.get('source') or {}).get('source_id'),'spectrum_id':spectrum['spectrum_candidate_id'],'page':spectrum.get('source_page'),'content_list_index':spectrum.get('content_list_index'),'caption_or_context':spectrum.get('caption_or_context'),'materials':[{'material_id':mid,'name':materials[mid].get('canonical_name_candidate'),'source_forms':materials[mid].get('source_forms',[])} for mid in spectrum.get('material_candidate_ids',[]) if mid in materials],'feature_candidates':[features[x] for x in spectrum.get('feature_candidate_ids',[]) if x in features],'evidence_spans':[evidence[x] for x in spectrum.get('evidence_ids',[]) if x in evidence],'assets':assets,'packaging_qa':{'images_referenced':len(ids),'images_copied':len(assets),'missing_images':len(ids)-len(assets)}})
    meta={'schema_version':'textbook-simple-spectra-release-1.0.0','release_id':args.output.name,'created_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat(),'source_scope':'textbook_only','excluded_sources':['nist'],'layout':'all records are in this meta.json; every image uses a relative img/... path','source_release':str(args.accepted),'counts':{'records':len(records),'images':copied,'missing_images':len(missing),'books_with_records':len({r['book'] for r in records})},'records':records,'missing_images':missing}
    (args.output/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(meta['counts'],ensure_ascii=False))
if __name__=='__main__':main()
