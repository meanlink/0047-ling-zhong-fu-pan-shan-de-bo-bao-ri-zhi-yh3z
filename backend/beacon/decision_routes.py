from fastapi import APIRouter,Depends
from core import db,require
from beacon.decisions import issue,preview

router=APIRouter(prefix="/api/beacon/tours")

@router.get("/{code}/drift")
def report(code:str,_=Depends(require())):
    with db() as cx:return preview(cx,code)

@router.post("/{code}/issue",status_code=201)
def close(code:str,user=Depends(require("reviewer"))):
    with db() as cx:return issue(cx,code,user["email"])
