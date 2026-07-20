#!/usr/bin/env python3
"""Build a textbook-only simple spectra release: NNNNNN/{meta.json,img/}."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def digest(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def copy_asset(src: Path,dst: Path) -> str:
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(src,dst)
    return digest(dst)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--accepted',required=True,type=Path);ap.add_argument('--images-root',required=True,type=Path);ap.add_argument('--output',required=True,type=Path);args=ap.parse_args()
    if args.output.exists(): raise SystemExit(f'refusing to overwrite existing output: {args.output}')
    summary=json.loads((args.accepted/'_all_books_summary.json').read_text(encoding='utf-8'))
    args.output.mkdir(parents=True); counts=Counter(); index=[]; missing=[]; number=0
    for book_meta in summary['books']:
        book=book_meta['book']; payload=json.loads((args.accepted/book/'material_spectra.json').read_text(encoding='utf-8'))
        materials={x['material_candidate_id']:x for x in payload.get('material_candidates',[])}; images={x['image_candidate_id']:x for x in payload.get('image_candidates',[])}; features={x['feature_candidate_id']:x for x in payload.get('feature_candidates',[])}; evid={x['evidence_id']:x for x in payload.get('evidence_spans',[])}
        for spectrum in payload.get('spectrum_candidates',[]):
            image_ids=[x for x in spectrum.get('image_candidate_ids',[]) if x in images]
            if not image_ids: continue
            number+=1; rid=f'{number:06d}'; record=args.output/rid; imgdir=record/'img'; imgdir.mkdir(parents=True); assets=[]
            for pos,image_id in enumerate(image_ids,1):
                image=images[image_id]; rel=image.get('source_image_path') or ''; src=args.images_root/book/'unzipped'/rel
                if src.is_file():
                    name=f'{pos:02d}_{src.name}'; dst=imgdir/name; sha=copy_asset(src,dst); assets.append({'image_candidate_id':image_id,'path':f'img/{name}','sha256':sha,'size_bytes':dst.stat().st_size,'source_image_path':rel})
                else: missing.append({'record_id':rid,'book':book,'spectrum_id':spectrum['spectrum_candidate_id'],'image_candidate_id':image_id,'source_image_path':rel})
            material_refs=[]
            for mid in spectrum.get('material_candidate_ids',[]):
                x=materials.get(mid)
                if x: material_refs.append({'material_id':mid,'name':x.get('canonical_name_candidate'),'source_forms':x.get('source_forms',[])})
            peaks=[features[x] for x in spectrum.get('feature_candidate_ids',[]) if x in features]
            evidence=[evid[x] for x in spectrum.get('evidence_ids',[]) if x in evid]
            meta={'schema_version':'textbook-simple-spectrum-1.0.0','package_record_id':rid,'record_type':'textbook_spectrum','source_scope':'textbook','book':book,'source_id':(payload.get('source') or {}).get('source_id'),'spectrum_id':spectrum['spectrum_candidate_id'],'page':spectrum.get('source_page'),'content_list_index':spectrum.get('content_list_index'),'caption_or_context':spectrum.get('caption_or_context'),'materials':material_refs,'feature_candidates':peaks,'evidence_spans':evidence,'assets':assets,'packaging_qa':{'image_candidates':len(image_ids),'images_copied':len(assets),'missing_image_candidates':len(image_ids)-len(assets),'layout':'record contains only meta.json and img/'}}
            (record/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); index.append({'record_id':rid,'book':book,'spectrum_id':meta['spectrum_id'],'materials':[x['material_id'] for x in material_refs],'page':meta['page'],'img_count':len(assets)});counts['records']+=1;counts['images']+=len(assets);counts['missing_images']+=len(image_ids)-len(assets)
    counts['books_with_records']=len({x['book'] for x in index}); created=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    (args.output/'release_meta.json').write_text(json.dumps({'release_id':args.output.name,'created_at':created,'source_scope':'textbook_only','excluded_sources':['nist'],'layout':'each numeric record directory contains only meta.json and img/','counts':dict(counts),'source':str(args.accepted),'missing_image_count':len(missing)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.output/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(args.output/'missing_images.json').write_text(json.dumps(missing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    files=sorted(x for x in args.output.rglob('*') if x.is_file());(args.output/'SHA256SUMS.txt').write_text(''.join(f'{digest(x)}  {x.relative_to(args.output).as_posix()}\n' for x in files),encoding='utf-8');print(json.dumps({'output':str(args.output),'counts':dict(counts),'missing':len(missing)},ensure_ascii=False))
if __name__=='__main__':main()
