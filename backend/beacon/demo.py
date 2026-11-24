from datetime import datetime,timedelta

def seed(cx):
    cx.execute("""
      INSERT INTO relay_posts VALUES ('RIDGE','松径岭播报亭',120),('GLEN','折石谷播报亭',100) ON CONFLICT DO NOTHING;
      INSERT INTO clock_refs VALUES ('REF-B','巡检记录仪乙',true,25),('REF-A','巡检记录仪甲',true,20),
        ('REF-D','停用备机',false,50) ON CONFLICT DO NOTHING;
      INSERT INTO tour_days VALUES ('DAY-18','RIDGE','2026-11-18',1080),
        ('DAY-17','GLEN','2026-11-17',1080) ON CONFLICT DO NOTHING;
    """)
    observations=[
        ("B-01","REF-A","2026-11-18T06:35:00+08:00",120),
        ("B-02","REF-A","2026-11-18T07:15:00+08:00",140),
        ("B-03","REF-B","2026-11-18T16:40:00+08:00",150),
        ("B-04","REF-A","2026-11-18T20:00:00+08:00",300),
        ("B-05","REF-A","2026-11-18T23:40:00+08:00",340),
        ("B-06","REF-B","2026-11-19T01:20:00+08:00",800),
        ("B-07","REF-B","2026-11-19T05:50:00+08:00",350),
    ]
    for code,clock,stamp,shift in observations:
        original=datetime.fromisoformat(stamp)
        cx.execute("""
          INSERT INTO log_pairs VALUES (%s,'DAY-18',%s,%s,%s,'松径岭_夜班铃点.log')
          ON CONFLICT DO NOTHING
        """,(code,clock,original,original+timedelta(milliseconds=shift)))
