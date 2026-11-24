"""同亭较早巡次中“最近一份有效的夜段实测修正”的挑选与加锁。"""
from math import isfinite

from fastapi import HTTPException

from beacon.provenance import SOURCE_COLUMNS, is_voided, source_of


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)


def night_section(sheet):
    """从复盘 corrections 里取夜段结构，兼容几种近义归档形状。"""
    corrections = sheet.get("corrections") if isinstance(sheet, dict) else None
    if not isinstance(corrections, dict):
        return {}
    segments = corrections.get("segments")
    if isinstance(segments, dict) and isinstance(segments.get("night"), dict):
        return segments["night"]
    if isinstance(corrections.get("night"), dict):
        return corrections["night"]
    return {}


def night_adjust(sheet):
    """尽力从复盘 JSON 中读出夜段修正量（相反数口径，单位 ms）。"""
    corrections = sheet.get("corrections") if isinstance(sheet, dict) else None
    night = night_section(sheet)
    if _number(night.get("adjust_ms")):
        return float(night["adjust_ms"])
    if isinstance(corrections, dict):
        clock = corrections.get("clock_adjust_ms")
        if isinstance(clock, dict) and _number(clock.get("night")):
            return float(clock["night"])
        for key in ("night_adjust_ms", "night_correction_ms"):
            if _number(corrections.get(key)):
                return float(corrections[key])
    return None


def borrowed_marker(sheet):
    """数据列或归档 JSON 中是否已带借用来源（借用来的不算实测）。"""
    for column in SOURCE_COLUMNS:
        if sheet.get(column):
            return str(sheet[column])
    return source_of(sheet.get("corrections"))


def is_measured(sheet):
    if is_voided(sheet):
        return False
    if borrowed_marker(sheet):
        return False
    night = night_section(sheet)
    # 人工直接给的意见不是“夜段实测修正”，不能再作为借用来源。
    if night.get("manual") is True or night.get("kind") == "manual":
        return False
    return night_adjust(sheet) is not None


def list_candidates(cx, tour):
    """同亭、较早巡次、已签发且未作废的复盘，按最近优先（不加锁）。"""
    rows = cx.execute(
        """
        SELECT s.*, u.post AS post_code, u.tour_day AS source_day, u.code AS tour_code
          FROM drift_sheets s
          JOIN tour_days u ON u.code = s.tour
         WHERE u.post = %(post)s
           AND u.tour_day < %(day)s
           AND s.tour <> %(code)s
         ORDER BY u.tour_day DESC, u.code DESC
        """,
        {"post": tour["post"], "day": tour["tour_day"], "code": tour["code"]},
    ).fetchall()
    return [row for row in rows if is_measured(row)]


def lock_sheet(cx, code):
    """锁定来源复盘行；与作废事务串行的关键就在这把行锁。"""
    row = cx.execute(
        "SELECT * FROM drift_sheets WHERE tour=%s FOR UPDATE", (code,)
    ).fetchone()
    if row is None:
        raise HTTPException(404, "作为借用来源的复盘不存在")
    return row


def resolve_explicit(cx, code):
    """签发请求点名了来源：作废已提交就直接拒绝按原来源签。"""
    sheet = lock_sheet(cx, code)
    if is_voided(sheet):
        raise HTTPException(409, f"来源复盘 {code} 已作废，不能按原来源签发")
    origin = borrowed_marker(sheet)
    if origin:
        raise HTTPException(409, f"来源复盘 {code} 的夜段修正借自 {origin}，不是实测修正")
    if night_adjust(sheet) is None:
        raise HTTPException(409, f"来源复盘 {code} 没有有效的夜段实测修正")
    return sheet


def resolve_latest(cx, tour):
    """自动借最近一份有效实测；逐个加锁复核，跳过刚被作废的来源。"""
    for brief in list_candidates(cx, tour):
        sheet = lock_sheet(cx, brief["tour"])
        if is_measured(sheet):
            return sheet
    raise HTTPException(409, "夜段样本不足，且同亭较早巡次没有可借用的有效夜段实测修正")


def resolve(cx, tour, requested=None):
    if requested:
        return resolve_explicit(cx, str(requested).strip())
    return resolve_latest(cx, tour)
