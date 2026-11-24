from fastapi import HTTPException

def list_tours(cx):
    return cx.execute("""
      SELECT t.*,p.name,p.max_range_ms FROM tour_days t JOIN relay_posts p ON p.code=t.post
      ORDER BY tour_day DESC,code
    """).fetchall()

def sources(cx):
    return cx.execute("SELECT * FROM clock_refs ORDER BY code").fetchall()

def tour(cx,code,lock=False):
    row=cx.execute("""
      SELECT t.*,p.name,p.max_range_ms FROM tour_days t JOIN relay_posts p ON p.code=t.post
      WHERE t.code=%s
    """+(" FOR UPDATE OF t" if lock else ""),(code,)).fetchone()
    if not row: raise HTTPException(404,"巡测日未登记")
    return row

def can_edit(cx,code):
    row=tour(cx,code,True)
    if cx.execute("SELECT 1 FROM drift_sheets WHERE tour=%s",(code,)).fetchone():
        raise HTTPException(409,"该巡测日复盘已签发")
    return row
