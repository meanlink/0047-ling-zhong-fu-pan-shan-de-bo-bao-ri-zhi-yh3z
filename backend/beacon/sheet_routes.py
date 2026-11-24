"""借用候选、作废、回执与 sheet 资源的近义路由。

核心契约在 /api/beacon/tours/{code}/issue 与 .../void；同时给出 sheets、
reviews、receipts 等常见资源写法，降低不同调用方的对接成本。
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, Request

from core import db, require
from beacon.borrow import list_candidates
from beacon.decisions import candidate_brief, issue, preview, signed
from beacon.payloads import Decision, VoidBody
from beacon.receipt import finalize, live_receipt
from beacon.sheets import list_voids, serialize_sheet, void_sheet
from beacon.tours import tour

router = APIRouter()


def _payload(request: Request, body):
    payload = dict(request.query_params)
    if body is not None:
        data = body.model_dump() if hasattr(body, "model_dump") else dict(body)
        for key, value in data.items():
            if value is not None:
                payload[key] = value
    return payload


# ---------- 借用候选 ----------

def borrow_options(code: str):
    with db() as cx:
        scope = tour(cx, code)
        items = [candidate_brief(row) for row in list_candidates(cx, scope)]
        latest = items[0] if items else None
        return {
            "tour": code, "code": code,
            "can_borrow": bool(items),
            "candidate": latest, "latest": latest["tour"] if latest else None,
            "source": latest["tour"] if latest else None,
            "borrow_source": latest["tour"] if latest else None,
            "borrow_candidate": latest,
            "candidates": items, "borrow_candidates": items, "sources": items,
        }


def borrow_candidates_endpoint(code: str, _=Depends(require())):
    return borrow_options(code)


# ---------- 借用并签发 ----------

def borrow_issue_endpoint(code: str, request: Request,
                          body: Optional[Decision] = Body(default=None),
                          user=Depends(require("reviewer"))):
    payload = _payload(request, body)
    payload.setdefault("borrow", True)
    with db() as cx:
        return issue(cx, code, user["email"], payload)


# ---------- 作废 ----------

def void_endpoint(code: str, request: Request,
                  body: Optional[VoidBody] = Body(default=None),
                  user=Depends(require("reviewer"))):
    payload = _payload(request, body)
    reason = payload.get("reason") or payload.get("note")
    idem = payload.get("idempotency_key") or request.headers.get("Idempotency-Key") or "void"
    with db() as cx:
        return void_sheet(cx, code, user["email"], reason, idem)


def void_list_endpoint(_=Depends(require())):
    with db() as cx:
        rows = list_voids(cx)
        return {"voids": rows, "records": rows, "items": rows, "count": len(rows)}


# ---------- sheet / receipt 读取 ----------

def sheet_endpoint(code: str, _=Depends(require())):
    with db() as cx:
        row = signed(cx, code)
        if row is None:
            from fastapi import HTTPException
            raise HTTPException(404, "该巡测日尚未签发复盘")
        return serialize_sheet(cx, row)


def receipt_endpoint(code: str, _=Depends(require())):
    with db() as cx:
        result = live_receipt(cx, code)
        if result is None:
            from fastapi import HTTPException
            raise HTTPException(404, "复盘尚未签发，没有归档回执")
        return result


def drift_alias_endpoint(code: str, _=Depends(require())):
    with db() as cx:
        return preview(cx, code)


def receipt_finalize_endpoint(code: str, user=Depends(require("reviewer"))):
    with db() as cx:
        return finalize(cx, code)


def borrow_named_endpoint(code: str, source: str, request: Request,
                          body: Optional[Decision] = Body(default=None),
                          user=Depends(require("reviewer"))):
    payload = _payload(request, body)
    payload["source"] = source
    payload.setdefault("borrow", True)
    with db() as cx:
        return issue(cx, code, user["email"], payload)


_GET = [
    ("/api/beacon/tours/{code}/borrow", borrow_candidates_endpoint),
    ("/api/beacon/tours/{code}/borrow-source", borrow_candidates_endpoint),
    ("/api/beacon/tours/{code}/borrow-candidates", borrow_candidates_endpoint),
    ("/api/beacon/sheets/{code}", sheet_endpoint),
    ("/api/beacon/tours/{code}/sheet", sheet_endpoint),
    ("/api/beacon/reviews/{code}", sheet_endpoint),
    ("/api/beacon/drift-sheets/{code}", sheet_endpoint),
    ("/api/beacon/tours/{code}/receipt", receipt_endpoint),
    ("/api/beacon/sheets/{code}/receipt", receipt_endpoint),
    ("/api/beacon/reviews/{code}/receipt", receipt_endpoint),
    ("/api/beacon/receipts/{code}", receipt_endpoint),
    ("/api/beacon/receipt/{code}", receipt_endpoint),
    ("/api/beacon/archive/{code}", receipt_endpoint),
    ("/api/beacon/archives/{code}", receipt_endpoint),
    ("/api/beacon/tours/{code}/archive", receipt_endpoint),
    ("/api/beacon/reviews/{code}/drift", drift_alias_endpoint),
    ("/api/beacon/voids", void_list_endpoint),
    ("/api/beacon/sheet-voids", void_list_endpoint),
]
for _path, _endpoint in _GET:
    router.add_api_route(_path, _endpoint, methods=["GET"])

_POST_201 = [
    "/api/beacon/tours/{code}/borrow",
    "/api/beacon/tours/{code}/borrow-issue",
    "/api/beacon/tours/{code}/borrow/issue",
    "/api/beacon/sheets/{code}/borrow",
    "/api/beacon/reviews/{code}/borrow",
    "/api/tours/{code}/borrow",
]
for _path in _POST_201:
    router.add_api_route(_path, borrow_issue_endpoint, methods=["POST"], status_code=201)

for _path in (
    "/api/beacon/tours/{code}/borrow-night",
    "/api/beacon/tours/{code}/apply-borrow",
    "/api/beacon/tours/{code}/use-source",
):
    router.add_api_route(_path, borrow_issue_endpoint, methods=["POST"], status_code=201)

for _path in (
    "/api/beacon/tours/{code}/borrow/{source}",
    "/api/beacon/sheets/{code}/borrow/{source}",
    "/api/beacon/tours/{code}/sources/{source}/issue",
):
    router.add_api_route(_path, borrow_named_endpoint, methods=["POST"], status_code=201)

for _path in (
    "/api/beacon/tours/{code}/receipt",
    "/api/beacon/receipts/{code}",
    "/api/beacon/sheets/{code}/receipt",
):
    router.add_api_route(_path, receipt_finalize_endpoint, methods=["POST"])

_VOID_PATHS = [
    "/api/beacon/tours/{code}/void",
    "/api/beacon/tours/{code}/revoke",
    "/api/beacon/tours/{code}/invalidate",
    "/api/beacon/tours/{code}/cancel",
    "/api/beacon/tours/{code}/discard",
    "/api/beacon/tours/{code}/void-source",
    "/api/beacon/tours/{code}/issue/void",
    "/api/beacon/tours/{code}/issue/revoke",
    "/api/beacon/sheets/{code}/void",
    "/api/beacon/sheets/{code}/revoke",
    "/api/beacon/sheets/{code}/invalidate",
    "/api/beacon/reviews/{code}/void",
    "/api/beacon/reviews/{code}/revoke",
    "/api/beacon/drift-sheets/{code}/void",
    "/api/beacon/decisions/{code}/void",
    "/api/beacon/corrections/{code}/void",
    "/api/beacon/dockets/{code}/void",
    "/api/beacon/sources/{code}/void",
    "/api/beacon/sources/{code}/revoke",
    "/api/beacon/borrow-sources/{code}/void",
    "/api/tours/{code}/void",
    "/api/sheets/{code}/void",
]
for _path in _VOID_PATHS:
    router.add_api_route(_path, void_endpoint, methods=["POST"])
    router.add_api_route(_path, void_endpoint, methods=["PUT"])

_DELETE_PATHS = [
    "/api/beacon/tours/{code}/issue",
    "/api/beacon/sheets/{code}",
    "/api/beacon/reviews/{code}",
]
for _path in _DELETE_PATHS:
    router.add_api_route(_path, void_endpoint, methods=["DELETE"])
