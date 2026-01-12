import os
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .models import DocumentIn, DocumentStored
from .opensearch_client import (
    ensure_index, index_document, get_document, delete_document,
    search_documents, ping as os_ping
)
from .rate_limiter import check_rate_limit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("documentsearch")

app = FastAPI(title="DocumentSearch Prototype")

TENANT_HEADER = "X-Tenant-Id"

class ErrorResponse(BaseModel):
    detail: str

@app.on_event("startup")
def startup():
    try:
        ok = ensure_index()
        if not ok:
            logger.warning("Failed to ensure index on startup; continuing (will surface at runtime).")
    except Exception as ex:
        logger.exception("Error during startup index ensure: %s", ex)

def require_tenant(header_value: Optional[str]) -> str:
    if not header_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tenant header X-Tenant-Id")
    return header_value

@app.post("/documents", status_code=status.HTTP_201_CREATED, responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
def create_document(doc: DocumentIn, request: Request, x_tenant_id: Optional[str] = Header(None, alias=TENANT_HEADER)):
    tenant = require_tenant(x_tenant_id)
    # rate limit
    check_rate_limit(tenant)

    if not doc.id or not doc.title or not doc.content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing fields in body; required: id, title, content")

    stored = {
        "tenant": tenant,
        "docId": doc.id,
        "title": doc.title,
        "content": doc.content,
        "createdAt": datetime.utcnow().isoformat()
    }

    try:
        resp = index_document(tenant, doc.id, stored)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch unreachable")

    if resp.status_code in (200,201):
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"result": "created"})
    else:
        logger.error("OpenSearch index error: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch error")

@app.get("/search", responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
def search(q: Optional[str] = None, x_tenant_id: Optional[str] = Header(None, alias=TENANT_HEADER)):
    tenant = require_tenant(x_tenant_id)
    check_rate_limit(tenant)
    if not q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing query parameter 'q'")

    try:
        resp = search_documents(tenant, q, size=10)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch unreachable")

    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch error")

    body = resp.json()
    hits = []
    total = 0
    if "hits" in body:
        hits_section = body["hits"]
        total = hits_section.get("total", {}).get("value", 0) if isinstance(hits_section.get("total", {}), dict) else hits_section.get("total", 0)
        for h in hits_section.get("hits", []):
            _id = h.get("_id", "")
            # remove tenant prefix if present
            docId = _id.split(":",1)[1] if ":" in _id else _id
            hits.append({
                "docId": docId,
                "_score": h.get("_score"),
                "_source": h.get("_source")
            })

    return {
        "tenant": tenant,
        "query": q,
        "tookMs": body.get("took"),
        "total": total,
        "hits": hits
    }

@app.get("/documents/{doc_id}", responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
def get_doc(doc_id: str, x_tenant_id: Optional[str] = Header(None, alias=TENANT_HEADER)):
    tenant = require_tenant(x_tenant_id)
    check_rate_limit(tenant)
    try:
        resp = get_document(tenant, doc_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch unreachable")

    if resp.status_code == 200:
        body = resp.json()
        if body.get("found"):
            return body.get("_source")
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    elif resp.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    else:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch error")

@app.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
def delete_doc(doc_id: str, x_tenant_id: Optional[str] = Header(None, alias=TENANT_HEADER)):
    tenant = require_tenant(x_tenant_id)
    check_rate_limit(tenant)
    try:
        resp = delete_document(tenant, doc_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch unreachable")

    if resp.status_code == 200:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
    elif resp.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    else:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OpenSearch error")

@app.get("/health")
def health():
    # Check OpenSearch reachable
    try:
        resp = os_ping()
        opensearch_status = "UP" if resp.status_code == 200 else "DOWN"
    except Exception:
        opensearch_status = "DOWN"

    overall = "UP" if opensearch_status == "UP" else "DEGRADED"
    return {
        "overall": overall,
        "dependencies": {
            "opensearch": opensearch_status
        }
    }
