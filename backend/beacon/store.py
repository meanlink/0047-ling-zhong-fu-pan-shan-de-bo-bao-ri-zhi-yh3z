from fastapi import HTTPException

def by_tour(cx,code):
    return cx.execute("""
      SELECT p.*,r.label AS ref_label,r.uncertainty_ms,n.label,n.note FROM log_pairs p
      JOIN clock_refs r ON r.code=p.clock LEFT JOIN log_notes n ON n.pair=p.code
      WHERE p.tour=%s ORDER BY p.source_at,p.code
    """,(code,)).fetchall()

def entry(cx,code):
    row=cx.execute("SELECT * FROM log_pairs WHERE code=%s",(code,)).fetchone()
    if row is None: raise HTTPException(404,"配对日志不存在")
    return row

def put(cx,code,body):
    return cx.execute("""
      INSERT INTO log_pairs(code,tour,clock,source_at,observed_at,import_note)
      VALUES (%(code)s,%(tour)s,%(clock)s,%(source_at)s,%(observed_at)s,%(import_note)s)
      RETURNING *
    """,body.model_dump()|{"tour":code}).fetchone()

def annotate(cx,pair,body,email):
    row=cx.execute("""
      INSERT INTO log_notes VALUES (%s,%s,%s,%s)
      ON CONFLICT(pair) DO UPDATE SET note=EXCLUDED.note,label=EXCLUDED.label,signed_by=EXCLUDED.signed_by
      RETURNING *
    """,(pair,body.note,body.label,email)).fetchone()
    return row
