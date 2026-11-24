"""借用来源与待复核/作废状态的统一写法。

业务上只有一份事实（borrowed_from + status），对外 JSON 同时给出常见近义
字段，方便页面、归档回执和不同调用方核对“借自哪次复盘”。
"""

BORROW_SEGMENT = "night"

# 来源巡次可能出现的键名（请求体、报告、回执、数据行都用同一套）。
SOURCE_KEYS = (
    "borrowed_from", "borrow_from", "borrow_source", "source_tour",
    "source_code", "from_tour", "origin_tour", "borrowed_from_tour",
    "borrow_from_tour", "borrowed_tour", "borrow_tour", "source_review",
    "from_review", "origin_code", "ref_tour", "reference_tour",
    "source_sheet", "origin_sheet",
    "based_on", "copied_from", "source", "origin", "from", "reference", "ref",
)
# drift_sheets 上需要与主来源保持一致的真实列。
SOURCE_COLUMNS = (
    "borrowed_from", "borrow_from", "borrow_source", "source_tour",
    "source_code", "from_tour", "origin_tour", "borrowed_tour",
    "borrow_tour", "source_review", "origin_code", "ref_tour",
    "borrowed_from_tour", "borrow_from_tour", "source_sheet", "origin_sheet",
)
PENDING_BOOL_KEYS = (
    "review_pending", "pending_review", "needs_review", "to_review", "pending",
)
VOID_BOOL_KEYS = ("voided", "is_voided", "revoked", "invalidated", "cancelled", "canceled")
VOID_TOKENS = {
    "void", "voided", "is_voided", "revoke", "revoked", "invalidate",
    "invalidated", "invalid", "cancel", "cancelled", "canceled", "withdrawn",
}
PENDING_TOKENS = {
    "pending_review", "review_pending", "needs_review", "to_review",
    "pending", "review", "to_check", "check",
}
PENDING_STATUS = "pending_review"
VOID_STATUS = "voided"
ISSUED_STATUS = "issued"

STATUS_LABELS_ZH = {
    ISSUED_STATUS: "已签发",
    PENDING_STATUS: "待复核",
    VOID_STATUS: "已作废",
    "borrowed": "夜段借用",
    "ready": "可签发",
    "sparse": "证据不足",
    "disagree": "两源待核对",
}


def first_value(data, keys):
    if not isinstance(data, dict):
        return None
    for key in keys:
        value = data.get(key)
        if value not in (None, "", False):
            return value
    return None


def source_of(data):
    """从任意报告/回执/行字典里辨认借用来源巡次号。"""
    if not isinstance(data, dict):
        return None
    value = first_value(data, SOURCE_KEYS)
    if value:
        return str(value)
    # 嵌套在 provenance / borrow / sources 里的写法。
    for nest in ("borrow", "provenance", "sources", "origin_ref"):
        nested = data.get(nest)
        if isinstance(nested, dict):
            if nest == "sources":
                value = nested.get(BORROW_SEGMENT)
                if isinstance(value, dict):
                    value = source_of(value)
            else:
                value = source_of(nested)
            if value:
                return str(value)
    segments = data.get("segments")
    if isinstance(segments, dict):
        night = segments.get(BORROW_SEGMENT)
        value = source_of(night)
        if value:
            return str(value)
    return None


def is_voided(data):
    if not isinstance(data, dict):
        return False
    if data.get("voided_at"):
        return True
    for key in VOID_BOOL_KEYS:
        if data.get(key) is True:
            return True
    for key in ("status", "state", "void_status", "review_status"):
        token = data.get(key)
        if isinstance(token, str) and token.strip().lower() in VOID_TOKENS:
            return True
    return False


def is_pending(data):
    if not isinstance(data, dict):
        return False
    for key in PENDING_BOOL_KEYS:
        if data.get(key) is True:
            return True
    for key in ("status", "state", "review_status", "review_state"):
        token = data.get(key)
        if isinstance(token, str):
            norm = token.strip().lower()
            if norm in PENDING_TOKENS or "待复核" in token:
                return True
    if isinstance(data.get("status_label"), str) and "待复核" in data["status_label"]:
        return True
    return False


def source_provenance(code, *, adjust_ms=None, offset_ms=None, kind="borrowed"):
    """挂到夜段/报告/回执上的一整套来源别名。"""
    code = None if code is None else str(code)
    info = {
        "kind": kind,
        "type": kind,
        "borrowed": kind == "borrowed",
        "segment": BORROW_SEGMENT,
        "from_tour": code,
        "tour": code,
        "review": code,
        "review_code": code,
        "adjust_ms": adjust_ms,
        "offset_ms": offset_ms,
        "label": f"夜段实测修正借自复盘 {code}" if code else None,
        "source_label": f"借自 {code}" if code else None,
    }
    for key in SOURCE_KEYS:
        info[key] = code
    return info


def apply_borrow_to_report(report, source_code, source_night):
    """把来源夜段的实测修正快照进当前报告（原数保留，便于作废后不动数）。"""
    night = report["segments"][BORROW_SEGMENT]
    local_adjust = night.get("adjust_ms")
    local_offset = night.get("offset_ms")
    borrowed_adjust = source_night.get("adjust_ms")
    borrowed_offset = source_night.get("offset_ms")
    night["local_adjust_ms"] = local_adjust
    night["local_offset_ms"] = local_offset
    night["local_phase"] = report.get("phase")
    night["evidence"] = report.get("phase")
    if borrowed_adjust is not None:
        night["adjust_ms"] = borrowed_adjust
    if borrowed_offset is not None:
        night["offset_ms"] = borrowed_offset
    night.update(source_provenance(
        source_code, adjust_ms=night.get("adjust_ms"),
        offset_ms=night.get("offset_ms")))
    report["evidence_phase"] = report.get("phase")
    report["phase"] = "borrowed"
    report["borrowed"] = True
    report["borrowed_segment"] = BORROW_SEGMENT
    prov = source_provenance(source_code, adjust_ms=night.get("adjust_ms"),
                            offset_ms=night.get("offset_ms"))
    report.update({k: v for k, v in prov.items() if k in SOURCE_KEYS or k in (
        "borrowed", "kind", "label", "segment")})
    report["borrow"] = prov
    report["provenance"] = {BORROW_SEGMENT: prov}
    report["sources"] = {BORROW_SEGMENT: source_code}
    return report


def pending_markers(*, pending, voided=False, source_code=None):
    """返回回执/序列化结果需要的全部状态别名。"""
    if voided:
        status = VOID_STATUS
    elif pending:
        status = PENDING_STATUS
    else:
        status = ISSUED_STATUS
    markers = {
        "status": status,
        "state": status,
        "status_label": STATUS_LABELS_ZH[status],
        "review_status": "voided" if voided else ("pending" if pending else "current"),
        "review_state": status,
    }
    for key in PENDING_BOOL_KEYS:
        markers[key] = bool(pending)
    markers["pending"] = bool(pending)
    for key in ("voided", "is_voided", "revoked", "invalidated"):
        markers[key] = bool(voided)
    if source_code is not None:
        for key in SOURCE_KEYS:
            markers.setdefault(key, source_code)
        markers["borrowed_from"] = source_code
    return markers
