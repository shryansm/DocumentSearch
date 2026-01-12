# Architecture (concise)

Purpose
-------
Describe the minimal architecture needed to review the prototype and reasoning behind simplifications.

Components
----------
1. API Service (FastAPI)
   - Exposes REST endpoints required by the spec.
   - Enforces tenant header `X-Tenant-Id` presence.
   - Implements a simple in-memory rate limiter per tenant.
   - Interacts with OpenSearch over HTTP (index, get, delete, search).
   - Auto-creates the index with required mapping at startup (best UX for reviewers).

2. OpenSearch (single-node)
   - Stores documents in a single index `documents`.
   - Mapping enforces `tenant` and `docId` as `keyword` for exact-match filtering.
   - `title` and `content` are `text` for full-text search. `title` is boosted at query time.

Multi-tenancy model
-------------------
- Tenant must be supplied via `X-Tenant-Id`.
- All docs stored with `_id` = `{tenant}:{docId}` and a `tenant` field.
- All reads/searches filter on `tenant` field so a tenant cannot see others' documents.

Index mapping
-------------
- index: `documents`
- fields:
  - tenant: keyword
  - docId: keyword
  - title: text
  - content: text
  - createdAt: date

Resilience & operational considerations (prototype)
--------------------------------------------------
- Single-node OpenSearch is used only for local evaluation.
- Health endpoint pings OpenSearch to report dependency status.
- Rate limiting is in-memory and thus only suitable for single-instance prototypes.

Diagram (text)
--------------
[client] -> [API (FastAPI)] -> [OpenSearch]
- API exposes endpoints and enforces tenant header
- API encodes tenant into OpenSearch _id and filters every read/search by tenant

Notes
-----
- Security (authz/authn) intentionally omitted for the prototype. Production must derive tenant from verified credentials.
- The prototype favors reviewer UX: docker compose self-contained, minimal friction.
