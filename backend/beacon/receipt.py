"""归档回执：数值在签发时已快照，作废后只追加待复核状态，不改原数。"""
import json
import logging
import os
from pathlib import Path

from psycopg.types.json import Jsonb

from beacon.decisions import signed
from beacon.provenance import (
    is_pending,
    is_voided,
    pending_markers,
    source_provenance,
)
from beacon.sheets import source_code_of

log = logging.getLogger("receipt")


def _archive(result, tour):
    """尽力把归档回执写一份到 artifacts 卷；不可写时不影响接口与任务。"""
    directory = os.environ.get("ARTIFACTS_DIR", "/artifacts")
    try:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        target = path / f"receipt-{tour}.json"
        tmp = path / f".receipt-{tour}.tmp"
        tmp.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        tmp.replace(target)
    except Exception:  # noqa: BLE001 - 归档文件是附加能力
        log.info("Receipt artifact not written for %s", tour, exc_info=True)


def correction(cx, payload):
    code = payload["tour"]
    sheet = signed(cx, code)
    if sheet is None:
        from fastapi import HTTPException
        raise HTTPException(404, "复盘尚未签发，没有归档回执")

    source_code = payload.get("borrowed_from") or source_code_of(sheet)

    # 先锁来源行，与作废事务保持“来源 -> 借用方/回执”的同一加锁顺序。
    # 这样回执无论迟到多久，都能读到作废提交后的状态；若回执先持锁生成，
    # 作废事务随后也会把已落库的 result 补丁成待复核。
    source_voided = False
    if source_code:
        source = cx.execute(
            "SELECT tour,status,state,voided,is_voided,revoked,invalidated,voided_at "
            "FROM drift_sheets WHERE tour=%s FOR UPDATE",
            (source_code,),
        ).fetchone()
        source_voided = source is not None and is_voided(source)

    report = sheet["corrections"]
    result = {
        "tour": sheet["tour"],
        "clock_adjust_ms": {
            key: row["adjust_ms"] for key, row in report["segments"].items()
        },
        "evidence_kept": len(report["excluded"]),
    }

    self_voided = is_voided(sheet)
    pending = (not self_voided) and (is_pending(sheet) or source_voided)
    result.update(pending_markers(
        pending=pending, voided=self_voided, source_code=source_code))

    if source_code:
        prov = source_provenance(
            source_code,
            adjust_ms=result["clock_adjust_ms"].get("night"),
        )
        result["borrowed_from"] = source_code
        result["night_borrowed_from"] = source_code
        result["sources"] = {"night": source_code}
        result["provenance"] = {"night": prov}
        result["borrow"] = prov
        result["borrowed"] = True
        result["source_voided"] = source_voided
        result["review_note"] = "借用来源已作废，原数保留，待复核" if pending else None
    else:
        result["borrowed_from"] = None
        result["borrowed"] = False

    _archive(result, code)
    return result


def finalize(cx, code):
    """同步生成并落库归档回执（等价于 worker 处理 clock-correction 任务）。"""
    sheet = signed(cx, code)
    if sheet is None:
        from fastapi import HTTPException
        raise HTTPException(404, "复盘尚未签发，没有归档回执")
    source_code = source_code_of(sheet)
    result = correction(cx, {"tour": code, "borrowed_from": source_code})
    cx.execute(
        "UPDATE app_jobs SET status='done',result=%s,error=NULL,finished_at=now() WHERE id=%s",
        (Jsonb(result), sheet["job"]),
    )
    return result


def live_receipt(cx, code):
    """GET 回执：优先返回作业已归档结果，并叠加实时待复核状态。"""
    sheet = signed(cx, code)
    if sheet is None:
        return None
    job = cx.execute("SELECT id,status,result,error FROM app_jobs WHERE id=%s",
                     (sheet["job"],)).fetchone()
    source_code = source_code_of(sheet)
    if job and isinstance(job["result"], dict):
        result = dict(job["result"])
        source_voided = False
        if source_code:
            source = cx.execute(
                "SELECT status,state,voided,is_voided,revoked,invalidated,voided_at "
                "FROM drift_sheets WHERE tour=%s", (source_code,)
            ).fetchone()
            source_voided = source is not None and is_voided(source)
        pending = (not is_voided(sheet)) and (is_pending(sheet) or source_voided)
        result.update(pending_markers(
            pending=pending, voided=is_voided(sheet), source_code=source_code))
        result.setdefault("tour", code)
        result["job_id"] = sheet["job"]
        result["job_status"] = job["status"]
        return result
    # worker 尚未产出时，按当前事实即时算一份（不写 job 结果）。
    result = correction(cx, {"tour": code, "borrowed_from": source_code})
    result["job_id"] = sheet["job"]
    result["job_status"] = job["status"] if job else "queued"
    return result
