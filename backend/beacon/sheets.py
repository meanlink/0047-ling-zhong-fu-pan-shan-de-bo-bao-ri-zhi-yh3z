""" drift_sheets 的对外形态、来源作废与待复核联动。"""
from fastapi import HTTPException
from psycopg.types.json import Jsonb

from beacon.provenance import (
    ISSUED_STATUS,
    PENDING_STATUS,
    SOURCE_COLUMNS,
    SOURCE_KEYS,
    STATUS_LABELS_ZH,
    VOID_STATUS,
    is_pending,
    is_voided,
    pending_markers,
    source_of,
)


def source_code_of(row):
    if not isinstance(row, dict):
        return None
    for column in SOURCE_COLUMNS:
        if row.get(column):
            return str(row[column])
    return source_of(row.get("corrections"))


def serialize_sheet(cx, row, *, check_source=True):
    """统一 sheet 的 JSON 形态：来源别名、实时作废/待复核状态、中文状态词。"""
    if row is None:
        return None
    data = dict(row)
    src = source_code_of(data)
    corrections = data.get("corrections")
    if src is None and isinstance(corrections, dict):
        src = source_of(corrections)

    source_voided = False
    source_missing = False
    if src and check_source:
        source = cx.execute(
            "SELECT tour,status,state,voided,is_voided,revoked,invalidated,voided_at "
            "FROM drift_sheets WHERE tour=%s",
            (src,),
        ).fetchone()
        if source is None:
            source_missing = True
        else:
            source_voided = is_voided(source)

    self_voided = is_voided(data)
    pending = (not self_voided) and (is_pending(data) or source_voided)

    # 所有来源近义键都给同一个值（含真实列与额外 JSON 键）。
    if src:
        for column in SOURCE_COLUMNS:
            data[column] = src
        for key in SOURCE_KEYS:
            data[key] = src

    if self_voided:
        markers = pending_markers(pending=False, voided=True, source_code=src)
        data.update(markers)
    elif pending:
        markers = pending_markers(pending=True, voided=False, source_code=src)
        data.update(markers)
    else:
        data.setdefault("status", ISSUED_STATUS)
        data.setdefault("state", ISSUED_STATUS)
        data["status_label"] = STATUS_LABELS_ZH.get(str(data.get("status")), "已签发")
        for key in ("review_pending", "pending_review", "needs_review"):
            data.setdefault(key, False)
        for key in ("voided", "is_voided", "revoked", "invalidated"):
            data.setdefault(key, False)

    data["source_voided"] = source_voided
    data["source_missing"] = source_missing
    data["borrowed"] = bool(src)
    if src:
        data["borrow_label"] = f"夜段实测修正借自复盘 {src}"
    return data


def _patch_archived_result(cx, job_id, source_code):
    """作废时同步给已生成的归档回执结果打上待复核标记，原数不动。"""
    if not job_id:
        return
    job = cx.execute("SELECT id,result FROM app_jobs WHERE id=%s", (job_id,)).fetchone()
    if not job or not isinstance(job["result"], dict):
        return
    result = dict(job["result"])
    result.update(pending_markers(pending=True, source_code=source_code))
    if source_code:
        result.setdefault("borrowed_from", source_code)
        result["night_borrowed_from"] = source_code
        borrow = result.get("borrow")
        if not isinstance(borrow, dict):
            borrow = {}
        borrow.update({"segment": "night", "from": source_code, "borrowed_from": source_code,
                       "label": f"夜段实测修正借自复盘 {source_code}"})
        result["borrow"] = borrow
    cx.execute("UPDATE app_jobs SET result=%s WHERE id=%s", (Jsonb(result), job_id))


def _dependent_rows(cx, code):
    # 任一来历列指向该来源都算借用方；列名来自代码内常量，不接受外部拼接。
    predicate = " OR ".join(f"{column}=%s" for column in SOURCE_COLUMNS)
    params = [code] * len(SOURCE_COLUMNS)
    return cx.execute(
        f"SELECT * FROM drift_sheets WHERE {predicate} FOR UPDATE",
        params,
    ).fetchall()


def void_sheet(cx, code, actor=None, reason=None, idempotency_key="void"):
    """作废一份复盘来源。

    - 来源行 FOR UPDATE，与借用签发的来源行锁互斥；
    - 作废登记（sheet_voids / review_events）靠主键与唯一约束保证重试不重复；
    - 已借用的复盘保留 corrections 原数，只改状态为待复核，并补丁归档回执。
    """
    row = cx.execute(
        "SELECT * FROM drift_sheets WHERE tour=%s FOR UPDATE", (code,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "要作废的复盘不存在")

    already = is_voided(row)
    if not already:
        cx.execute(
            """
            UPDATE drift_sheets SET
              status=%(void)s, state=%(void)s,
              voided=true, is_voided=true, revoked=true, invalidated=true,
              voided_at=now(), status_changed_at=now(),
              voided_by=%(actor)s, void_reason=%(reason)s,
              review_pending=false, pending_review=false, needs_review=false
            WHERE tour=%(code)s
            """,
            {"void": VOID_STATUS, "actor": actor, "reason": reason, "code": code},
        )
        cx.execute(
            "INSERT INTO sheet_voids(tour,voided_by,reason) VALUES(%s,%s,%s) "
            "ON CONFLICT (tour) DO NOTHING",
            (code, actor, reason),
        )
        cx.execute(
            """
            INSERT INTO review_events(tour,kind,actor,detail,idempotency_key)
            VALUES (%s,'void',%s,%s,%s)
            ON CONFLICT (tour,kind,idempotency_key) DO NOTHING
            """,
            (code, actor, Jsonb({"reason": reason}), idempotency_key or "void"),
        )

    # 联动所有借用方。即使是作废重试也做一次幂等核对，拦住晚到的借用（正常路径
    # 会在签发时直接拒绝已作废来源，这里是第二道保险）。
    for dep in _dependent_rows(cx, code):
        if dep["tour"] == code or is_voided(dep):
            continue
        cx.execute(
            """
            UPDATE drift_sheets SET
              status=%(pending)s, state=%(pending)s, review_status='pending',
              review_pending=true, pending_review=true, needs_review=true,
              status_changed_at=now()
            WHERE tour=%(tour)s
            """,
            {"pending": PENDING_STATUS, "tour": dep["tour"]},
        )
        cx.execute(
            """
            INSERT INTO review_events(tour,kind,actor,detail,idempotency_key)
            VALUES (%s,'source_voided',%s,%s,%s)
            ON CONFLICT (tour,kind,idempotency_key) DO NOTHING
            """,
            (dep["tour"], actor, Jsonb({"source": code, "reason": reason}), f"source-void:{code}"),
        )
        _patch_archived_result(cx, dep["job"], code)

    fresh = cx.execute("SELECT * FROM drift_sheets WHERE tour=%s", (code,)).fetchone()
    return serialize_sheet(cx, fresh, check_source=False)


def list_voids(cx):
    return cx.execute(
        "SELECT * FROM sheet_voids ORDER BY created_at, tour"
    ).fetchall()
