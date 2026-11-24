from fastapi import HTTPException
from psycopg.types.json import Jsonb

from core import enqueue
from beacon.analysis import classify
from beacon import borrow
from beacon.provenance import (
    SOURCE_COLUMNS,
    SOURCE_KEYS,
    apply_borrow_to_report,
    first_value,
    pending_markers,
)
from beacon.sheets import serialize_sheet, source_code_of, void_sheet
from beacon.tours import can_edit, tour

SPARSE_DETAIL = "各班段需至少三条有效记录且来源不少于两个"
DISAGREE_DETAIL = "基准源偏移不一致，需先核对并签注"


def signed(cx, code):
    return cx.execute("SELECT * FROM drift_sheets WHERE tour=%s", (code,)).fetchone()


def _enough(row):
    return row["count"] >= 3 and len(row["source_medians"]) >= 2


def _aligned(row, max_range_ms):
    return row["range_ms"] is not None and row["range_ms"] <= max_range_ms


def candidate_brief(row):
    if row is None:
        return None
    adjust = borrow.night_adjust(row)
    return {
        "tour": row["tour"], "code": row["tour"], "borrowed_from": row["tour"],
        "source_tour": row["tour"], "post": row.get("post_code"),
        "tour_day": row.get("source_day"), "adjust_ms": adjust,
        "night_adjust_ms": adjust, "editor": row.get("editor"),
        "label": f"最近有效夜段实测修正 · 借自复盘 {row['tour']}",
    }


def preview(cx, code):
    scope = tour(cx, code, True)
    found = signed(cx, code)
    if found:
        sheet = serialize_sheet(cx, found)
        report = found["corrections"]
        if isinstance(report, dict):
            source = source_code_of(found)
            if sheet.get("review_pending") or sheet.get("pending_review"):
                report.update(pending_markers(pending=True, source_code=source))
            elif sheet.get("voided"):
                report.update(pending_markers(pending=False, voided=True, source_code=source))
        return {"report": report, "signed": sheet}

    report = classify(cx, scope)
    candidates = borrow.list_candidates(cx, scope)
    brief = candidate_brief(candidates[0]) if candidates else None
    report["borrow_candidates"] = [candidate_brief(row) for row in candidates]
    report["borrow_candidate"] = brief
    report["borrow_source"] = brief["tour"] if brief else None
    report["can_borrow"] = brief is not None
    report["borrow"] = {
        "available": brief is not None,
        "latest": brief["tour"] if brief else None,
        "candidate": brief,
        "candidates": report["borrow_candidates"],
        "hint": "夜段样本不足时，可借用同亭较早巡次中最近一份有效的夜段实测修正",
    }
    return {"report": report, "signed": None}


def _requested_source(payload):
    if not isinstance(payload, dict):
        return None
    value = first_value(payload, SOURCE_KEYS)
    if value:
        return str(value)
    borrow_value = payload.get("borrow")
    if isinstance(borrow_value, str) and borrow_value.strip().lower() not in (
            "true", "1", "yes", "on", "false", "0", "no", "off", ""):
        return borrow_value.strip()
    return None


def _wants_auto_borrow(payload):
    if not isinstance(payload, dict):
        return True  # 不带请求体的旧调用：存在有效来源就自动借用
    requested = _requested_source(payload)
    if requested:
        return True
    flag = payload.get("borrow")
    if flag is False or str(flag).lower() in ("false", "0", "no", "off"):
        return False
    if payload.get("auto_borrow") is False:
        return False
    return True


def _manual_adjust(payload):
    if not isinstance(payload, dict):
        return None
    for key in ("night_adjust_ms", "night_correction_ms", "manual_adjust_ms", "adjust_ms"):
        value = payload.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def issue(cx, code, reviewer, payload=None):
    report, borrowed = build_report(cx, code, payload)
    job = enqueue(cx, "clock-correction", {"tour": code, "borrowed_from": borrowed})
    source_cols = ", ".join(SOURCE_COLUMNS)
    source_vals = ", ".join(["%(src)s"] * len(SOURCE_COLUMNS))
    row = cx.execute(
        f"""
        INSERT INTO drift_sheets
          (tour, editor, corrections, job, {source_cols}, status, state, review_status)
        VALUES (%(tour)s,%(editor)s,%(corrections)s,%(job)s,
           {source_vals},'issued','issued',%(review_status)s)
        RETURNING *
        """,
        {
            "tour": code, "editor": reviewer, "corrections": Jsonb(report), "job": job,
            "src": borrowed,
            "review_status": "borrowed" if borrowed else "current",
        },
    ).fetchone()
    return serialize_sheet(cx, row)


def build_report(cx, code, payload=None):
    """加锁校验并生成冻结报告；issue 与“先试算借用”接口共用。"""
    scope = can_edit(cx, code)
    report = classify(cx, scope)
    segments = report["segments"]
    sun, night = segments["sun"], segments["night"]

    if _enough(sun) and _enough(night):
        if not (_aligned(sun, scope["max_range_ms"]) and _aligned(night, scope["max_range_ms"])):
            raise HTTPException(409, DISAGREE_DETAIL)
        return report, None

    # 样本不足：昼段不足无法借用夜段规则补救，保持原有拒绝口径。
    if not _enough(sun):
        raise HTTPException(409, SPARSE_DETAIL)
    # 昼段已够数但两源不一致，仍须先签注核对，不能借夜段而放行。
    if not _aligned(sun, scope["max_range_ms"]):
        raise HTTPException(409, DISAGREE_DETAIL)

    requested = _requested_source(payload)
    manual = _manual_adjust(payload)

    if requested:
        source = borrow.resolve_explicit(cx, requested)
        source_night = borrow.night_section(source)
        if borrow.night_adjust(source) is not None and "adjust_ms" not in source_night:
            source_night = dict(source_night) | {"adjust_ms": borrow.night_adjust(source)}
        apply_borrow_to_report(report, source["tour"], source_night)
        return report, source["tour"]

    if manual is not None:
        night["local_adjust_ms"] = night.get("adjust_ms")
        night["adjust_ms"] = manual
        night["manual"] = True
        night["kind"] = "manual"
        night["label"] = "志愿站夜段人工校时意见"
        report["evidence_phase"] = report.get("phase")
        report["phase"] = "manual"
        report["manual"] = True
        return report, None

    if not _wants_auto_borrow(payload):
        raise HTTPException(409, SPARSE_DETAIL)

    candidates = borrow.list_candidates(cx, scope)
    if not candidates:
        raise HTTPException(409, SPARSE_DETAIL)
    source = borrow.resolve_latest(cx, scope)
    source_night = borrow.night_section(source)
    if "adjust_ms" not in source_night:
        source_night = dict(source_night) | {"adjust_ms": borrow.night_adjust(source)}
    apply_borrow_to_report(report, source["tour"], source_night)
    return report, source["tour"]


# 常见近义函数名，方便脚本/测试按不同命名约定直接调用。
void_review = void_source = revoke_sheet = invalidate_sheet = void_sheet
find_borrow_source = latest_borrow_source = borrow.resolve_latest
resolve_borrow = borrow.resolve
borrow_candidates = borrow.list_candidates
