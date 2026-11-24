from fastapi import HTTPException
from psycopg.types.json import Jsonb
from core import enqueue
from beacon.analysis import classify
from beacon.tours import can_edit,tour

def signed(cx,code):
    return cx.execute("SELECT * FROM drift_sheets WHERE tour=%s",(code,)).fetchone()

def preview(cx,code):
    scope=tour(cx,code,True)
    found=signed(cx,code)
    return {"report":found["corrections"] if found else classify(cx,scope),"signed":found}

def issue(cx,code,reviewer):
    report=classify(cx,can_edit(cx,code))
    phase=report["phase"]
    if phase=="sparse":
        raise HTTPException(409,"各班段需至少三条有效记录且来源不少于两个")
    if phase=="disagree":
        raise HTTPException(409,"基准源偏移不一致，需先核对并签注")
    job=enqueue(cx,"clock-correction",{"tour":code})
    return cx.execute("INSERT INTO drift_sheets VALUES (%s,%s,%s,%s) RETURNING *",
                      (code,reviewer,Jsonb(report),job)).fetchone()
