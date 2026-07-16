#!/usr/bin/env python3
"""Re-extract valid textbook material/spectrum candidates from MinerU pages.

This pass intentionally prefers precision: a material must be a chemical name,
formula, or explicit sample identity in an IR-related context. Sentence
fragments and section/instrument labels remain in the old broad staging run.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUT = ROOT / '20260616 谱学教科书知识抽取加强版' / 'outputs'
OUTPUT = ROOT / '0714谱构效数据' / 'material_spectra_clean'
LEGACY_GROUPS = ROOT / 'Github' / 'Textbook-Empowered-Spectra-Toolset' / 'raw_data' / 'basic_groups_v07_20260619'
RUN_ID = 'RUN_valid-materials-20260716-all-books-v1'
IR_RE = re.compile(r'(红外|infrared|\bIR\b|ftir|光谱|spectrum|spectra|吸收峰|吸收带|波数|wavenumber|cm\s*[-−]?\s*1)', re.I)
SPECTRUM_RE = re.compile(r'(红外光谱|红外吸收光谱|infrared\s+(?:absorption\s+)?spectrum|IR\s+spectrum|spectrum\s+of|spectra\s+of|光谱图|谱图|吸收光谱)', re.I)
PEAK_RE = re.compile(r'(?<!\d)(\d{3,4}(?:\s*[-–—]\s*\d{3,4})?)(?:\s*(?:cm\s*[-−]?\s*1|cm\^\s*[-−]?\s*1|波数))', re.I)
CHINESE_NAME_RE = re.compile(r'[\u4e00-\u9fff]{1,18}(?:酸|醇|酚|醛|酮|胺|酰胺|酯|醚|苯|烷|烯|炔|腈|硝基|聚合物|树脂|矿物|药物)')
FORMULA_RE = re.compile(r'\b(?:[A-Z][a-z]?\d*){2,}\b')
ENGLISH_SUFFIXES = ('benzene','toluene','xylene','phenol','alcohol','aldehyde','ketone','acid','ester','amine','amide','ether','nitrile','alkane','alkene','alkyne','acetate','chloride','bromide','fluoride','oxide','sulfate','sulfonate','phosphate','siloxane','glucose','fructose','sucrose','cellulose','polyethylene','polystyrene','polyamide','protein')
BAD_FORMULA = {'ch3','ch2','pb99','i5s583'}
BAD_EXACT = {x.casefold() for x in {'together','whether','dioxide','monoxide','acid','oxide','sulfate','sulfonate','phosphate','chloride','bromide','fluoride','nitrile','acetate','tetrachloride','FTIRs','CCDs','ADCs','DACs','DSPs','PCs','CPUs','GHz','MHz','THz','VOCs','ANNs','NEPs','FWHHs','AOTFs','FPAs','PMTs','LIAs','IREs','PZTs','PEMs','amide','amine','alcohol','aldehyde','ketone','ester','ether','alkane','alkene','alkyne','siloxane','hydroxide','protein','hydrochloride','peroxide','orthophosphate','sulfur oxide','sulfoxide','polyether','n-alkane','fluorochloride','oxyfluoride','uorochloride'}}

KNOWN = {'water','benzene','toluene','acetone','methanol','ethanol','chloroform','carbon tetrachloride','carbon monoxide','carbon dioxide','hydrochloric acid','ammonia','hcl','co2','co','h2o','甲醇','乙醇','水','苯','甲苯','丙酮','氯仿','四氯化碳','氨','盐酸'}
BAD_WORDS = {'spectrum','spectra','infrared','sample','samples','compound','compounds','molecule','molecules','materials','material','equation','text','figure','table','gases','liquids','solids','diameter','modulation','measurements','the','this','that','which','these','many','most','unknown','is','are','and','with','from','for','about','such','equation'}

ELEMENTS = set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og'.split())

GROUP_WORDS = ['羰基','羧基','羟基','氨基','亚氨基','酰胺','酯基','醚键','醛基','酮基','硝基','腈基','卤素','芳环','苯环','烯烃','炔烃','甲基','亚甲基','次甲基','磷酸','硫酸','硅氧烷','官能团','carbonyl','carboxyl','hydroxyl','amine','amide','ester','ether','aldehyde','ketone','nitro','nitrile','halide','aromatic','alkene','alkyne','methyl','methylene','phosphate','sulfate','siloxane','functional group']

def sid(prefix, text):
    x = re.sub(r'[^A-Za-z0-9]+', '_', text).strip('_').lower() or hashlib.sha1(text.encode()).hexdigest()[:16]
    return f'{prefix}_{x[:70]}'

def flat(value):
    if isinstance(value, str): return [value]
    if isinstance(value, list):
        out=[]
        for x in value: out.extend(flat(x))
        return out
    if isinstance(value, dict):
        out=[]
        for k,v in value.items():
            if k not in {'path','bbox','image_source'}: out.extend(flat(v))
        return out
    return []

def item_text(item): return '\n'.join(x.strip() for x in flat(item.get('content',{})) if x.strip())

def load_items(path):
    pages=json.loads(path.read_text(encoding='utf-8-sig'))
    items=[]; idx=0
    for page_no,page in enumerate(pages,1):
        seq=page if isinstance(page,list) else [page]
        for ordinal,item in enumerate(seq):
            if not isinstance(item,dict): continue
            content=item.get('content',{})
            image_path=(content.get('image_source') or {}).get('path') if isinstance(content,dict) else None
            items.append({'global_index':idx,'page':page_no,'ordinal':ordinal,'type':item.get('type',''),'text':item_text(item),'bbox':item.get('bbox'),'image_path':image_path,'content':content})
            idx+=1
    return items

def valid_name(raw):
    name=re.sub(r'\s+',' ',raw).strip(' -—()（）[]')
    name=re.sub(r'^(?:a|an|the|pure|common|very common|low-density|high-density|must be)\s+', '', name, flags=re.I)
    if not (2 <= len(name) <= 50): return None
    low=name.casefold()
    if low in BAD_WORDS or low in {x.casefold() for x in BAD_EXACT} or low in BAD_FORMULA: return None
    if re.match(r'^(?:as|contains|must|very|common|primary|secondary|tertiary|saturated|aromatic|alkyl|a|an|the)\b', low): return None
    if '(' in name or ')' in name: return None
    if low in KNOWN: return name
    if any(w in low for w in ['spectrum','spectra','infrared spectroscopy','vibrational','resolution','wavenumber','equation','techniques','measurements','samples','molecules with','is now','cannot be','usually','consists of','according to','such as']): return None
    if re.search(r'[。；！？,:：]|\b(?:is|are|and|with|from|that|which|these|those|for|about|by|to|of)\b', name, re.I): return None
    if re.fullmatch(r'[\u4e00-\u9fff]{2,18}', name):
        if any(mark in name for mark in ('的','和','与','在','为','是','中','研究','分析','方法','光谱','化合物')): return None
        return name if CHINESE_NAME_RE.search(name) or name in KNOWN else None
    if FORMULA_RE.fullmatch(name) and len(name) <= 15 and (any(ch.isdigit() for ch in name) or name in KNOWN):
        letters = re.sub(r"\d+", "", name)
        symbols = re.findall(r"[A-Z][a-z]?", letters)
        if "".join(symbols) == letters and all(symbol in ELEMENTS for symbol in symbols) and max([int(x) for x in re.findall(r'\d+', name)] or [0]) <= 20 and (any(ch.islower() for ch in name) or low in {"co","co2","no","no2","n2","o2","h2o","nh3","so2","so3"}): return name
    words=name.split()
    if len(words)>4 or not re.search(r'[A-Za-z]',name): return None
    if any(w.casefold() in BAD_WORDS for w in words): return None
    if low in KNOWN: return name
    if low.endswith('amine') and not any(root in low for root in ('methyl','ethyl','propyl','butyl','benz','cyclo','dimethyl','amino')): return None
    if low.endswith('ester') and not any(root in low for root in ('acet','benzo','poly','methyl','ethyl','propyl','butyl','carbox','amino')): return None
    if low.endswith('acid') and len(low) <= 7: return None
    if any(low.endswith(suffix) for suffix in ENGLISH_SUFFIXES): return name
    return None

def extract_names(text):
    found=set()
    patterns=[
      r'(?i)\b(?:spectrum|spectra|infrared\s+(?:absorption\s+)?spectrum|IR\s+spectrum)\s+of\s+([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){0,4})',
      r'(?:红外光谱|红外吸收光谱|光谱图|谱图)\s*(?:的|：|:)\s*([\u4e00-\u9fffA-Za-z0-9()（）\-—/· ]{2,35})',
      r'(?:化合物|样品|物质|compound|sample|molecule)\s*(?:为|是|的|：|:)?\s*([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9()（）\-—/· ]{1,35})',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern,text):
            raw=re.split(r'[\n，。；,:：]|\s+(?:at|in|with|shows|has|and|is|are|was|were)\s+',match.group(1),maxsplit=1,flags=re.I)[0]
            name=valid_name(raw)
            if name: found.add(name)
    for match in CHINESE_NAME_RE.finditer(text):
        name=valid_name(match.group(0))
        if name: found.add(name)
    for match in FORMULA_RE.finditer(text):
        name=valid_name(match.group(0))
        if name: found.add(name)
    # Only retain standalone English chemical-looking names, not arbitrary prose.
    for token in re.findall(r'\b[A-Za-z][A-Za-z0-9-]{2,30}\b',text):
        name=valid_name(token)
        if name: found.add(name)
    return sorted(found)

def group_vocab():
    vocab={}
    for p in sorted(LEGACY_GROUPS.glob('FG_*.json')) if LEGACY_GROUPS.exists() else []:
        try: d=json.loads(p.read_text(encoding='utf-8'))
        except Exception: continue
        gid=d.get('group_id') or p.stem; vocab[gid]=[d.get('name_zh',''),d.get('name_en','')]
    return vocab

def evidence(book_slug,item):
    text=item['text'][:5000]
    return {'evidence_id':sid('EV',f'{book_slug}_{item["global_index"]}'),'evidence_type':item['type'] or 'text','locator':{'pdf_page':item['page'],'content_list_index':item['global_index'],'bbox':item.get('bbox')},'text_original':text,'content_hash':hashlib.sha256(text.encode()).hexdigest(),'review_status':'needs_review'}

def main():
    OUTPUT.mkdir(parents=True,exist_ok=True); vocab=group_vocab(); books_summary=[]; material_catalog={}; group_catalog={}; spectrum_catalog={}
    for book in sorted(p for p in INPUT.iterdir() if p.is_dir()):
        files=sorted((book/'unzipped').glob('*content_list_v2.json'))
        if not files: continue
        items=load_items(files[0]); by_page={}
        for item in items: by_page.setdefault(item['page'],[]).append(item)
        mats={}; groups={}; spectra={}; features={}; images={}; evs={}
        for page, page_items in by_page.items():
            for pos,item in enumerate(page_items):
                nearby=' '.join(x['text'] for x in page_items[max(0,pos-2):min(len(page_items),pos+3)] if x['text'])
                context=(item['text']+' '+nearby).strip(); names=extract_names(context) if IR_RE.search(context) else []
                if not names: continue
                ev=evidence(sid('BOOK',book.name),item); evs[ev['evidence_id']]=ev
                matched_groups=[]
                low=context.casefold()
                for gid,forms in vocab.items():
                    if any(f and f.casefold() in low for f in forms): matched_groups.append(gid)
                for word in GROUP_WORDS:
                    if word.casefold() in low: matched_groups.append(sid('GROUP_CAND',word))
                matched_groups=sorted(set(matched_groups))
                for name in names:
                    mid=sid('MAT',name); rec=mats.setdefault(mid,{'material_candidate_id':mid,'canonical_name_candidate':name,'source_forms':[name],'material_type':'valid_material_candidate','group_candidate_ids':[],'spectrum_ids':[],'feature_ids':[],'evidence_ids':[],'mention_count':0,'promotion_status':'candidate_needs_review'})
                    rec['mention_count']+=1; rec['evidence_ids'].append(ev['evidence_id']); rec['group_candidate_ids'].extend(matched_groups)
                is_spectrum=bool(SPECTRUM_RE.search(context)) or item['type'] in {'image','chart','table','figure'}
                if is_spectrum:
                    specid=sid('SPEC',f'{book.name}_{item["global_index"]}')
                    spec=spectra.setdefault(specid,{'spectrum_candidate_id':specid,'material_candidate_ids':[],'group_candidate_ids':matched_groups,'feature_candidate_ids':[],'image_candidate_ids':[],'evidence_ids':[ev['evidence_id']],'caption_or_context':context[:3000],'source_page':page,'content_list_index':item['global_index'],'promotion_status':'candidate_needs_review'})
                    for name in names:
                        mid=sid('MAT',name); spec['material_candidate_ids'].append(mid); mats[mid]['spectrum_ids'].append(specid)
                    for raw_value in PEAK_RE.findall(context):
                        fid=sid('FEAT',f'{book.name}_{item["global_index"]}_{raw_value}'); features[fid]={'feature_candidate_id':fid,'raw_position_text':raw_value,'unit':'cm-1','value_origin':'reported_or_ocr_candidate','evidence_ids':[ev['evidence_id']],'promotion_status':'candidate_needs_review'}; spec['feature_candidate_ids'].append(fid)
                        for name in names: mats[sid('MAT',name)]['feature_ids'].append(fid)
                    if item['type'] in {'image','chart','table','figure'} and item.get('image_path'):
                        iid=sid('IMG',f'{book.name}_{item["global_index"]}'); images[iid]={'image_candidate_id':iid,'source_page':page,'content_list_index':item['global_index'],'item_type':item['type'],'source_image_path':item['image_path'],'promotion_status':'candidate_needs_review'}; spec['image_candidate_ids'].append(iid)
        for rec in list(mats.values()):
            for k in ['group_candidate_ids','spectrum_ids','feature_ids','evidence_ids']: rec[k]=sorted(set(rec[k]))
        for rec in list(spectra.values()):
            for k in ['material_candidate_ids','group_candidate_ids','feature_candidate_ids','image_candidate_ids','evidence_ids']: rec[k]=sorted(set(rec[k]))
            for gid in rec['group_candidate_ids']: groups.setdefault(gid,{'group_candidate_id':gid,'preferred_name':{'source':gid},'source_forms':[],'spectrum_ids':[],'evidence_ids':[],'promotion_status':'candidate_needs_review'}); groups[gid]['spectrum_ids'].append(rec['spectrum_candidate_id']); groups[gid]['evidence_ids'].extend(rec['evidence_ids'])
        for gid,rec in groups.items(): rec['spectrum_ids']=sorted(set(rec['spectrum_ids'])); rec['evidence_ids']=sorted(set(rec['evidence_ids']))
        payload={'run_id':RUN_ID,'source':{'source_id':sid('SRC',book.name),'title':book.name,'source_type':'textbook','source_file':str(files[0].relative_to(ROOT))},'scope':{'unit_type':'whole_book_valid_material_pass','mineru_items':len(items)},'group_candidates':list(groups.values()),'material_candidates':list(mats.values()),'spectrum_candidates':list(spectra.values()),'feature_candidates':list(features.values()),'evidence_spans':list(evs.values()),'image_candidates':list(images.values()),'quality':{'status':'candidate_needs_review','strict_name_filter':True,'material_count':len(mats),'spectrum_count':len(spectra),'feature_count':len(features),'image_count':len(images),'evidence_count':len(evs)}}
        outdir=OUTPUT/book.name; outdir.mkdir(parents=True,exist_ok=True); (outdir/'material_spectra.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
        books_summary.append({'book':book.name,'mineru_items':len(items),'materials':len(mats),'groups':len(groups),'spectra':len(spectra),'features':len(features),'images':len(images),'evidence':len(evs)})
        for key,rec in groups.items(): group_catalog.setdefault(key,{'group_candidate_id':key,'source_records':[]})['source_records'].append({'book':book.name,'source_id':payload['source']['source_id'],'record':rec})
        for key,rec in mats.items(): material_catalog.setdefault(key,{'material_candidate_id':key,'source_records':[]})['source_records'].append({'book':book.name,'source_id':payload['source']['source_id'],'record':rec})
        for key,rec in spectra.items(): spectrum_catalog.setdefault(key,{'spectrum_candidate_id':key,'source_records':[]})['source_records'].append({'book':book.name,'source_id':payload['source']['source_id'],'record':rec})
    totals={k:sum(x[k] for x in books_summary) for k in ['mineru_items','materials','groups','spectra','features','images','evidence']}; unique={'materials':len(material_catalog),'groups':len(group_catalog),'spectra':len(spectrum_catalog)}
    (OUTPUT/'_compound_catalog.json').write_text(json.dumps({'run_id':RUN_ID,'unique_candidates':len(material_catalog),'materials':list(material_catalog.values())},ensure_ascii=False),encoding='utf-8')
    (OUTPUT/'_group_catalog.json').write_text(json.dumps({'run_id':RUN_ID,'unique_candidates':len(group_catalog),'groups':list(group_catalog.values())},ensure_ascii=False),encoding='utf-8')
    (OUTPUT/'_spectrum_catalog.json').write_text(json.dumps({'run_id':RUN_ID,'unique_candidates':len(spectrum_catalog),'spectra':list(spectrum_catalog.values())},ensure_ascii=False),encoding='utf-8')
    report={'run_id':RUN_ID,'book_count':len(books_summary),'books':books_summary,'totals':totals,'unique_catalogs':unique,'policy':{'mode':'precision_filtered_textbook_inventory','retain_all_book_sources':True,'only_valid_material_name_contexts':True,'formal_status':'staging_needs_review'}}
    (OUTPUT/'_all_books_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUTPUT/'_all_books_report.md').write_text('# 31本教材有效物质—特性—红外谱图抽取报告\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__': main()
