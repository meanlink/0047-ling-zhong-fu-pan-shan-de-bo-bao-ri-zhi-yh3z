from beacon.cutover import segment
from beacon.robust import agreement
from beacon.store import by_tour

def classify(cx,tour):
    sections={"sun":[],"night":[]}
    excluded=[]
    for row in by_tour(cx,tour["code"]):
        if row["label"]:
            excluded.append(row["code"])
            continue
        key=segment(row["source_at"],tour)
        if key:
            delta=row["observed_at"]-row["source_at"]
            sections[key].append(row | {"offset_ms":round(delta.total_seconds()*1000,3)})
    report={name:agreement(rows) for name,rows in sections.items()}
    enough=all(row["count"]>=3 and len(row["source_medians"])>=2 for row in report.values())
    aligned=all(row["range_ms"] is not None and row["range_ms"]<=tour["max_range_ms"] for row in report.values())
    phase="ready" if enough and aligned else "disagree" if enough else "sparse"
    return {"segments":report,"phase":phase,"excluded":excluded,"max_range_ms":tour["max_range_ms"]}
