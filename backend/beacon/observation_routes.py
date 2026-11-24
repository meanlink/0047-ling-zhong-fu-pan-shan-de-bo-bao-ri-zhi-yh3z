from fastapi import APIRouter,Depends
from core import db,require
from beacon.observations import notes,register
from beacon.payloads import Note,Pair
from beacon.store import by_tour

router=APIRouter(prefix="/api/beacon")

@router.get("/tours/{tour}/pairs")
def list_pairs(tour:str,_=Depends(require())):
    with db() as cx:return by_tour(cx,tour)

@router.post("/tours/{tour}/pairs",status_code=201)
def pair(tour:str,body:Pair,_=Depends(require("operator"))):
    with db() as cx:return register(cx,tour,body)

@router.put("/pairs/{pair}/note")
def mark(pair:str,body:Note,user=Depends(require("reviewer"))):
    with db() as cx:return notes(cx,pair,body,user["email"])
