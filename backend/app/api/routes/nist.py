from pathlib import Path
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import get_settings
from app.core.security import CurrentUser, require_permission

router = APIRouter(prefix="/nist", tags=["nist"] )

def connect():
    path = get_settings().nist_index_path
    if not path.exists():
        raise HTTPException(status_code=503, detail="NIST index is not ready")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)

@router.get("/stats")
def stats(_user: CurrentUser = Depends(require_permission("project:read"))):
    con = connect()
    try:
        tables = ("compounds", "files", "spectra", "tb_groups", "tb_compounds", "tb_spectra", "align")
        return {"db": str(get_settings().nist_index_path), "counts": {t: con.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in tables}}
    finally: con.close()

@router.get("/compounds")
def compounds(q: str | None = Query(default=None), limit: int = Query(default=50, le=200), _user: CurrentUser = Depends(require_permission("compound:read"))):
    con = connect()
    try:
        if q:
            like = "%" + q + "%"
            rows = con.execute("SELECT k,accession,name,formula,smiles,inchikey,cas FROM compounds WHERE name LIKE ? OR formula LIKE ? OR cas LIKE ? OR inchikey LIKE ? LIMIT ?", (like, like, like, like, limit)).fetchall()
        else:
            rows = con.execute("SELECT k,accession,name,formula,smiles,inchikey,cas FROM compounds LIMIT ?", (limit,)).fetchall()
        return {"total": len(rows), "items": [dict(zip(("compound_key","accession","name","formula","smiles","inchikey","cas"), r)) for r in rows]}
    finally: con.close()

@router.get("/spectra")
def spectra(compound_key: str | None = None, modality: str | None = None, limit: int = Query(default=50, le=200), _user: CurrentUser = Depends(require_permission("spectrum:read"))):
    con = connect()
    try:
        sql = "SELECT id,k,modality,technique,path,xunits,yunits,xmin,xmax,npoints FROM spectra WHERE 1=1"; args=[]
        if compound_key: sql += " AND k = ?"; args.append(compound_key)
        if modality: sql += " AND modality = ?"; args.append(modality)
        sql += " LIMIT ?"; args.append(limit)
        rows=con.execute(sql,args).fetchall(); keys=("spectrum_id","compound_key","modality","technique","data_path","x_units","y_units","x_min","x_max","npoints")
        return {"total":len(rows),"items":[dict(zip(keys,r)) for r in rows]}
    finally: con.close()

@router.get("/alignment")
def alignment(compound_key: str | None = None, status: str = "identity_exact", limit: int = Query(default=100, le=500), _user: CurrentUser = Depends(require_permission("compound:read"))):
    con=connect()
    try:
        if compound_key:
            rows=con.execute("SELECT k,tb_id,method,score,status,evidence,details FROM align WHERE k=? AND status=? LIMIT ?",(compound_key,status,limit)).fetchall()
        else:
            rows=con.execute("SELECT k,tb_id,method,score,status,evidence,details FROM align WHERE status=? LIMIT ?",(status,limit)).fetchall()
        keys=("compound_key","textbook_compound_id","method","score","status","evidence_ids","details")
        return {"total":len(rows),"items":[dict(zip(keys,r)) for r in rows]}
    finally: con.close()
