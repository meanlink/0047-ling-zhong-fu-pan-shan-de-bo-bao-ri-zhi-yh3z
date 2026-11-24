from datetime import datetime,time,timedelta,timezone

LOCAL=timezone(timedelta(hours=8),name="UTC+08:00")

def bounds(tour):
    dawn=datetime.combine(tour["tour_day"],time(6),LOCAL)
    cut=(dawn.replace(hour=0)+timedelta(minutes=tour["switch_minute"]))
    if cut<dawn: cut+=timedelta(days=1)
    return dawn,cut,dawn+timedelta(days=1)

def segment(moment,tour):
    start,cut,end=bounds(tour)
    if not start<=moment<end:return None
    return "sun" if moment<cut else "night"
