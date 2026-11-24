from collections import defaultdict
from math import sqrt
from statistics import fmean, median

def midpoint(values):
    return round(median(values),3) if values else None

def agreement(entries):
    by_ref=defaultdict(list)
    for row in entries:
        by_ref[row["clock"]].append(row["offset_ms"])
    mids={key:midpoint(values) for key,values in sorted(by_ref.items())}
    center=midpoint(list(mids.values()))
    # Centering within each clock removes fixed instrument offsets before
    # estimating the shared change in offset over the course of the segment.
    groups=defaultdict(list)
    for row in entries:
        hours=row["source_at"].timestamp()/3600
        groups[row["clock"]].append((hours,row["offset_ms"]))
    pairs=[]
    for group in groups.values():
        mean_time=fmean(time for time,_ in group)
        mean_offset=fmean(offset for _,offset in group)
        pairs.extend((time-mean_time,offset-mean_offset) for time,offset in group)
    time_energy=sum(time*time for time,_ in pairs)
    offset_energy=sum(offset*offset for _,offset in pairs)
    covariance=sum(time*offset for time,offset in pairs)
    has_repeats=len(entries)-len(groups)>=2
    trend={"slope_ms_per_hour":None,"within_source_r":None,"paired_degrees":len(entries)-len(groups)}
    if has_repeats and time_energy>0:
        trend["slope_ms_per_hour"]=round(covariance/time_energy,3)
        if offset_energy>0:
            trend["within_source_r"]=round(covariance/sqrt(time_energy*offset_energy),3)
    return {"count":len(entries),"source_medians":mids,"offset_ms":center,"adjust_ms":-center if center is not None else None,
            "range_ms":round(max(mids.values())-min(mids.values()),3) if len(mids)>1 else None,
            "trend":trend,"values":sorted(row["offset_ms"] for row in entries)}
