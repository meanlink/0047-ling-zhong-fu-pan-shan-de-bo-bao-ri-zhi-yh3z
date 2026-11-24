# 岭钟复盘 · 山地播报日志

千径自然步道志愿站由 8 名志愿者巡看四季开放的步道，维护沿路整点播报亭的离线纸带。以前把各巡检记录仪和站亭原声时间抄进值守表，午夜记录常归错巡次，同一来源较密的记录压过另一来源，手动剔除误标时找不到解释。系统按巡次复核日志，给养护负责人保留时间对齐凭据。业务范围为离线记录分析及复盘签注。

| 角色 | 动作 |
|---|---|
| operator | 对照基准和实录的时间，补记原始文件 |
| reviewer | 标注异常记录和证据，签发校时意见 |
| viewer | 查看巡测时线、配对台账、分段偏移和回执 |

1. 11 月 18 日 06:00 本地开始 DAY-18 松径岭巡次。
2. 06:35 与 07:15 由 REF-A 得到 120、140 ms 偏移。
3. 16:40 由 REF-B 得到 150 ms 偏移，日段推荐修正 −140 ms。
4. 18:00 班段切换；次日 01:20 的 800 ms 和 05:50 的 350 ms 仍归 DAY-18。
5. 11 月 19 日 06:00 结束 DAY-18，边界后的实录不能补进上一巡次。
6. 08:00 两个基准在夜段的中位数极差超出 120 ms，拒绝签发。
7. 09:00 调阅《松径岭_夜班铃点.log》，把错取人工铃点签注排除，夜段修正为 −335 ms，签发复盘凭据。

巡次按当地 UTC+08:00 的 06:00 日切，再按巡次登记的昼夜分割时间作两段统计。每段先取各基准源的中位数，再取这些中位数的中位数，让各来源各占一票。至少两源三条记录且基准源中位数极差不超站亭上限；偏移相反数为日志建议修正量。源内诊断先将时间、偏移分别减去同一来源的均值，再计算斜率和 Pearson 相关系数，用来辨别持续漂移与来源之间的固定时差。有效的源内自由度少于 2 时保留空值。异常签注排除而保留原始记录。

```sh
cp -n .env.example .env
docker compose up -d --build --wait
docker compose exec backend python -m scripts.seed_demo
docker compose down -v --remove-orphans
```

演示账号 operator@demo.local、reviewer@demo.local、viewer@demo.local，默认密码 Demo2026!。FRONTEND_PORT、BACKEND_PORT、DB_PORT 决定宿主端口，SEED_DEMO 控制填充，DEMO_PASSWORD、JWT_SECRET、POSTGRES_PASSWORD 是本地配置。Nginx 原生 ES modules、FastAPI/Python、worker、PostgreSQL、Redis。后端本地安装 backend/requirements.txt，配置 DATABASE_URL、REDIS_URL、JWT_SECRET 后运行 `uvicorn app:app --reload` 和 `python worker.py`。backend/beacon 实现巡次、证据和修正，frontend/clockroom 为对应页面。角色/任务枚举在 backend/core.py、frontend/base.js；异常类型与分段枚举在 backend/schema.sql、backend/beacon/payloads.py、cutover.py、analysis.py 与 frontend/clockroom/phrases.js。MIT 许可证。

前端地址为 http://127.0.0.1:18441，API 为 http://127.0.0.1:19441，数据库本机映射端口为 17941。
