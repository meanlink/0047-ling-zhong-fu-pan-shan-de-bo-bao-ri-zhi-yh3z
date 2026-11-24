from fastapi import HTTPException
from beacon.cutover import segment
from beacon.store import annotate,entry,put
from beacon.tours import can_edit,sources

def register(cx,tour,body):
    context=can_edit(cx,tour)
    if not any(row["code"]==body.clock and row["enabled"] for row in sources(cx)):
        raise HTTPException(409,"只能接收可用授时源作基准")
    if segment(body.source_at,context) is None:
        raise HTTPException(409,"基准时刻跨过巡测日切边界")
    if abs((body.observed_at-body.source_at).total_seconds()) > 15:
        raise HTTPException(409,"两日志相差超过 15 秒，需核对是否同一播报铃点")
    return put(cx,tour,body)

def notes(cx,pair,body,email):
    origin=entry(cx,pair)
    can_edit(cx,origin["tour"])
    return annotate(cx,pair,body,email)
