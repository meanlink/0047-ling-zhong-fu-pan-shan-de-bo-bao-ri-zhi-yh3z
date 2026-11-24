from beacon.decisions import signed

def correction(cx,payload):
    sheet=signed(cx,payload["tour"])
    report=sheet["corrections"]
    return {"tour":sheet["tour"],"clock_adjust_ms":{key:row["adjust_ms"] for key,row in report["segments"].items()},
            "evidence_kept":len(report["excluded"])}
