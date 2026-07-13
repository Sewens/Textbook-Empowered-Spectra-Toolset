#!/usr/bin/env python3
import argparse, html, json, mimetypes, os, re, sqlite3, sys, time
from pathlib import Path
from collections import defaultdict
DDL = """
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT);
CREATE TABLE IF NOT EXISTS state(root TEXT,top TEXT,status TEXT,files INTEGER,updated TEXT,error TEXT,PRIMARY KEY(root,top));
CREATE TABLE IF NOT EXISTS compounds(k TEXT PRIMARY KEY,accession TEXT,source_dir TEXT,name TEXT,formula TEXT,smiles TEXT,inchi TEXT,inchikey TEXT,cas TEXT,meta TEXT);
CREATE TABLE IF NOT EXISTS files(id INTEGER PRIMARY KEY,k TEXT,path TEXT UNIQUE,modality TEXT,kind TEXT,mime TEXT,size INTEGER,meta TEXT);
CREATE TABLE IF NOT EXISTS spectra(id INTEGER PRIMARY KEY,k TEXT,file_id INTEGER UNIQUE,modality TEXT,technique TEXT,path TEXT,xunits TEXT,yunits TEXT,xmin REAL,xmax REAL,npoints INTEGER,meta TEXT);
CREATE TABLE IF NOT EXISTS tb_groups(id TEXT PRIMARY KEY,name_zh TEXT,name_en TEXT,formula TEXT,smarts TEXT,path TEXT);
CREATE TABLE IF NOT EXISTS tb_compounds(id TEXT PRIMARY KEY,name_zh TEXT,name_en TEXT,formula TEXT,smiles TEXT,inchikey TEXT,cas TEXT,groups TEXT,examples TEXT,evidence TEXT,paths TEXT);
CREATE TABLE IF NOT EXISTS tb_spectra(id TEXT PRIMARY KEY,compound_id TEXT,example_id TEXT,modality TEXT,image TEXT,peaks TEXT,evidence TEXT,path TEXT);
CREATE TABLE IF NOT EXISTS align(id INTEGER PRIMARY KEY,k TEXT,tb_id TEXT,method TEXT,score REAL,status TEXT,evidence TEXT,details TEXT,UNIQUE(k,tb_id,method));
CREATE TABLE IF NOT EXISTS spectrum_align(id INTEGER PRIMARY KEY,nist_id INTEGER,tb_id TEXT,modality TEXT,peak_matches INTEGER,tb_peaks INTEGER,nmin REAL,nmax REAL,tolerance REAL,evidence TEXT,details TEXT,UNIQUE(nist_id,tb_id));
"""
META = re.compile(r'<meta[^>]+(?:name|property|itemprop)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']', re.I)
CAS = re.compile(r'\b\d{2,7}-\d{2}-\d\b')
def clean(x):
    if x is None: return None
    x = html.unescape(str(x)).strip()
    return x or None
def formula(x): return re.sub(r'\s+', '', str(x)).upper() if x else None
def ident(x):
    x = clean(x)
    return x.upper() if x and '-' in x and len(x) >= 14 else x
def html_meta(p):
    try: s = p.read_text('utf8', errors='replace')[:300000]
    except OSError: return {}
    d = {a.lower(): clean(b) for a,b in META.findall(s)}
    t = re.search(r'<title[^>]*>(.*?)</title>', s, re.I|re.S)
    if t: d.setdefault('title', clean(re.sub(r'\s+', ' ', t.group(1))))
    c = CAS.search(s)
    if c: d.setdefault('cas', c.group(0))
    for k,v in re.findall(r'"(molecularFormula|inChIKey|inChI|smiles|name)"\s*:\s*"([^"]+)"', s[:300000], re.I): d.setdefault(k.lower(), v)
    return d
def jdx(p):
    m = {}; n = 0; data = False
    try: lines = p.read_text('utf8', errors='replace').splitlines()
    except OSError: return m,n
    for line in lines:
        if line.startswith('##XYDATA='): data=True; continue
        if not data and line.startswith('##') and '=' in line:
            k,v=line[2:].split('=',1); m[k.upper()]=v.strip()
        elif data and not line.startswith('##'):
            n += max(0, len(re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?', line))-1)
    return m,n
def modality(r):
    for x in ('IR Spectrum','Mass Spectrum','Raman Spectrum','UV/Vis Spectrum','Gas chromatography','Phase change data','Thermochemistry','ion energetics'):
        if x.lower() in r.lower(): return x.lower().replace(' ','_')
    return 'other'
def kind(p): return {'.jdx':'raw_sequence','.svg':'spectrum_image','.png':'image','.tif':'image','.html':'metadata_page','.mas':'raw_sequence','.msa':'raw_sequence','.raw':'raw_sequence'}.get(p.suffix.lower(),'other')
def load_textbook(root,c):
    cs=defaultdict(lambda:[None,None,None,None,None,set(),set(),set(),set()]); ng=ns=0
    for p in sorted(root.glob('FG_*.json')):
        try: d=json.loads(p.read_text('utf8'))
        except Exception: continue
        gid=d.get('group_id') or d.get('group',{}).get('group_id')
        if not gid: continue
        c.execute('INSERT OR REPLACE INTO tb_groups VALUES(?,?,?,?,?,?)',(gid,d.get('name_zh'),d.get('name_en'),d.get('chemical_formula'),d.get('smarts'),str(p))); ng+=1
        for e in d.get('compound_examples') or []:
            q=e.get('compound') or {}; cid=q.get('compound_id')
            if not cid: continue
            z=cs[cid]; names=q.get('names') or {}; z[:5]=[names.get('zh'),names.get('en'),q.get('molecular_formula'),q.get('smiles'),q.get('inchi_key')]; z[5].add(gid); z[6].add(e.get('example_id')); z[7].update(e.get('evidence_ids') or []); z[8].add(str(p))
            for sp in e.get('spectra') or []:
                peaks=[v.get('wavenumber_cm_1') for v in sp.get('peaks') or [] if isinstance(v.get('wavenumber_cm_1'),(int,float))]; ev=set(sp.get('evidence_ids') or [])
                for v in sp.get('peaks') or []: ev.update(v.get('evidence_ids') or [])
                c.execute('INSERT OR REPLACE INTO tb_spectra VALUES(?,?,?,?,?,?,?,?)',(sp.get('spectrum_id') or e.get('example_id'),cid,e.get('example_id'),sp.get('modality') or 'unknown',sp.get('image_path'),json.dumps(peaks),json.dumps(sorted(ev)),str(p))); ns+=1
    for cid,z in cs.items(): c.execute('INSERT OR REPLACE INTO tb_compounds VALUES(?,?,?,?,?,?,?,?,?,?,?)',(cid,z[0],z[1],z[2],z[3],z[4],None,json.dumps(sorted(z[5])),json.dumps(sorted(z[6])),json.dumps(sorted(z[7])),json.dumps(sorted(z[8]))))
    return ng,len(cs),ns
def scan(root,top):
    fs=[]; m={}
    for dp,_,names in os.walk(top):
        for name in names:
            p=Path(dp)/name; fs.append((p,str(p.relative_to(root))))
            if p.suffix.lower()=='.html': m.update(html_meta(p))
    for p,_ in fs:
        if p.suffix.lower()=='.jdx':
            q,_=jdx(p); [m.setdefault(k.lower(),v) for k,v in q.items()]; break
    a=top.name; ca=m.get('cas') or m.get('cas registry no'); fo=m.get('molecularformula') or m.get('molform') or m.get('formula'); ik=m.get('inchikey'); key='nist:'+str(ident(ik) or ca or a).replace('/','_')
    return fs,(key,a,str(top.relative_to(root)),m.get('name') or m.get('dcterms.title') or m.get('title') or a,fo,m.get('smiles'),m.get('inchi'),ik,ca,json.dumps(m,ensure_ascii=False))
def align(c):
    c.execute('DELETE FROM align'); idx=defaultdict(list)
    for r in c.execute('SELECT id,name_zh,name_en,formula,smiles,inchikey,cas,groups,evidence FROM tb_compounds'):
        for k,v in [('ik',r[5]),('cas',r[6]),('smiles',r[4]),('formula',formula(r[3]))]:
            if v: idx[(k,ident(v) if k in ('ik','cas') else (formula(v) if k=='formula' else v.lower()))].append(r)
    for ck,nm,fo,sm,ik,ca in c.execute('SELECT k,name,formula,smiles,inchikey,cas FROM compounds'):
        hits=[]
        for k,v,s in [('ik',ik,1.0),('cas',ca,.98),('smiles',sm,.95),('formula',fo,.4)]:
            if v: hits += [(r,s,k) for r in idx.get((k,ident(v) if k in ('ik','cas') else (formula(v) if k=='formula' else v.lower())),[])]
        best={}
        for r,s,k in hits: best.setdefault(r[0],[]).append((r,s,k))
        for tbid,vals in best.items():
            r,s,k=max(vals,key=lambda x:x[1]); c.execute('INSERT OR IGNORE INTO align(k,tb_id,method,score,status,evidence,details) VALUES(?,?,?,?,?,?,?)',(ck,tbid,k,s,'identity_exact' if s>=.95 else 'formula_candidate',r[8],json.dumps({'method':k,'groups':json.loads(r[7])},ensure_ascii=False)))
def main(a):
    nr=Path(a.nist).resolve(); tr=Path(a.raw).resolve(); db=Path(a.db).resolve(); db.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(db); c.executescript(DDL); c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=NORMAL'); print(json.dumps({'textbook':load_textbook(tr,c)},ensure_ascii=False),flush=True); c.commit()
    done={x[0] for x in c.execute("SELECT top FROM state WHERE root=? AND status='done'",(str(nr),))}; tops=sorted(x for x in nr.iterdir() if x.is_dir()); total=0; start=time.time()
    for i,top in enumerate(tops,1):
        if top.name in done: continue
        try:
            fs,m=scan(nr,top); c.execute('INSERT OR REPLACE INTO compounds VALUES(?,?,?,?,?,?,?,?,?,?)',m)
            for p,r in fs:
                try: size=p.stat().st_size
                except OSError: continue
                md={}; np=None
                if p.suffix.lower()=='.jdx': md,np=jdx(p)
                c.execute('INSERT OR IGNORE INTO files(k,path,modality,kind,mime,size,meta) VALUES(?,?,?,?,?,?,?)',(m[0],r,modality(r),kind(p),mimetypes.guess_type(p.name)[0],size,json.dumps(md,ensure_ascii=False)))
                if p.suffix.lower()=='.jdx':
                    fid=c.execute('SELECT id FROM files WHERE path=?',(r,)).fetchone()[0]; c.execute('INSERT OR IGNORE INTO spectra(k,file_id,modality,technique,path,xunits,yunits,xmin,xmax,npoints,meta) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(m[0],fid,modality(r),md.get('DATA TYPE'),r,md.get('XUNITS'),md.get('YUNITS'),float(md['MINX']) if md.get('MINX') else None,float(md['MAXX']) if md.get('MAXX') else None,np,json.dumps(md,ensure_ascii=False)))
            c.execute('INSERT OR REPLACE INTO state VALUES(?,?,?,?,?,NULL)',(str(nr),top.name,'done',len(fs),time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))); c.commit(); total+=len(fs)
            if i%a.progress_every==0: print(json.dumps({'top_done':i,'top_total':len(tops),'files':total,'elapsed_s':round(time.time()-start,1)}),flush=True)
        except Exception as e:
            c.rollback(); c.execute('INSERT OR REPLACE INTO state VALUES(?,?,?,?,?,?)',(str(nr),top.name,'error',0,time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),repr(e))); c.commit(); print('ERROR',top,repr(e),file=sys.stderr,flush=True)
    align(c); c.commit(); tables=['compounds','files','spectra','tb_groups','tb_compounds','tb_spectra','align']; print(json.dumps({'completed':True,'db':str(db),'stats':{t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}},ensure_ascii=False),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--nist',required=True); p.add_argument('--raw',required=True); p.add_argument('--db',required=True); p.add_argument('--progress-every',type=int,default=100); main(p.parse_args())
