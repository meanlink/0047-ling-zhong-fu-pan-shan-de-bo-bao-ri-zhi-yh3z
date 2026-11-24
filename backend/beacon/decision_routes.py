from typing import Optional

from fastapi import APIRouter, Body, Depends, Request
from core import db, require
from beacon.decisions import issue, preview
from beacon.payloads import Decision

router = APIRouter(prefix="/api/beacon/tours")


def merge_payload(request: Request, body: Optional[Decision]):
    payload = dict(request.query_params)
    if body is not None:
        for key, value in body.model_dump().items():
            if value is not None:
                payload[key] = value
    return payload


@router.get("/{code}/drift")
def report(code: str, _=Depends(require())):
    with db() as cx:
        return preview(cx, code)


@router.post("/{code}/issue", status_code=201)
def close(code: str, request: Request,
          body: Optional[Decision] = Body(default=None),
          user=Depends(require("reviewer"))):
    payload = merge_payload(request, body)
    with db() as cx:
        return issue(cx, code, user["email"], payload)
