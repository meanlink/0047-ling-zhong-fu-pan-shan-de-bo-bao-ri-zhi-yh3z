from fastapi import APIRouter,Depends
from core import db,require
from beacon.tours import list_tours,sources
from beacon.cutover import bounds

router=APIRouter(prefix="/api/beacon")

@router.get("/tours")
def roster(_=Depends(require())):
    with db() as cx:
        return [row | dict(zip(("start","cut","end"),bounds(row),strict=True)) for row in list_tours(cx)]

@router.get("/sources")
def standards(_=Depends(require())):
    with db() as cx:return sources(cx)
