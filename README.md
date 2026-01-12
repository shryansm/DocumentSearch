# DocumentSearch — Prototype

Overview
--------
DocumentSearch is a runnable prototype of a multi-tenant document search service that indexes and searches documents using an OpenSearch/Elasticsearch-compatible HTTP API. It is intentionally simplified for a reviewer-friendly prototype while demonstrating the key architecture, multi-tenancy contract, health, and resilience concerns.

Quick start
-----------
Prerequisites
- Docker Desktop (or docker + docker-compose)

Start the stack
```bash
docker compose up --build
```

The API will be available at: http://localhost:8080

API examples
------------
All requests MUST include the tenant as the `X-Tenant-Id` HTTP header (this prototype standardizes on a single tenant propagation mechanism).

1) Index a document
```bash
curl -v -X POST "http://localhost:8080/documents" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: tenant-a" \
  -d '{"id":"doc1","title":"Hello world","content":"This is a test document."}'
```
Returns 201 Created on success.

2) Search
```bash
curl -v "http://localhost:8080/search?q=test" -H "X-Tenant-Id: tenant-a"
```

3) Get a document
```bash
curl -v "http://localhost:8080/documents/doc1" -H "X-Tenant-Id: tenant-a"
```

4) Delete a document
```bash
curl -v -X DELETE "http://localhost:8080/documents/doc1" -H "X-Tenant-Id: tenant-a"
```

5) Health
```bash
curl -v "http://localhost:8080/health"
```

Tenant model
------------
- Tenant is required on every request via the `X-Tenant-Id` header.
- For the prototype tenant trust is assumed (no authentication). Production must derive tenant from verified credentials (JWT/API key, etc).
- Tenant isolation is enforced by encoding stored OpenSearch document `_id` as `{tenant}:{docId}` and by filtering queries on the `tenant` field.

Assumptions & trade-offs
-----------------------
- This prototype uses a single-node OpenSearch instance launched via Docker Compose and treats OpenSearch as the source of truth.
- Tenant identity is trusted input (explicitly bypassing authentication for speed).
- Rate limiting is an in-memory per-tenant counter (single-instance only).
- No distributed indexing pipeline nor production-grade rate limiting/caching are implemented (they are documented in docs/production-readiness.md).

Production Readiness Summary
----------------------------
See docs/production-readiness.md for an actionable checklist (monitoring, auth, distributed rate limiting, backups, HA OpenSearch, etc).

AI Tool Usage
-------------
- This prototype and documentation were scaffolded and drafted with the assistance of an AI coding assistant to speed iteration (implementation, README, and docs). Human review required before productionization.

Files of interest
-----------------
- docker-compose.yml — starts OpenSearch and the API
- Dockerfile — builds API container
- src/main/ — FastAPI application code
- docs/architecture.md — architecture notes and diagrams (concise)
- docs/production-readiness.md — production checklist
