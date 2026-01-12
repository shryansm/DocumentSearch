# Production Readiness Notes

This file lists the primary changes and concerns required to move from this prototype to a production-ready service.

Authentication & Authorization
- Replace trusting `X-Tenant-Id` header with verified credentials:
  - Use JWTs (issued by an auth service / OIDC) or API keys.
  - Validate token signature, expiry; extract tenant (sub/tenant claim).
  - Enforce RBAC where necessary.

Multi-instance & Rate limiting
- Replace in-memory rate limiter with distributed enforcement:
  - Use Redis or API Gateway (CloudFront + Lambda@Edge / API Gateway throttling).
  - Support per-tenant quotas and bursts.
- Persist counters/metrics in a time-series DB for observability.

OpenSearch & Data durability
- Use a managed OpenSearch (or Elasticsearch) cluster with:
  - Multiple data nodes for HA
  - Snapshot backups to S3-compatible storage
  - Proper index lifecycle management (ILM)
- Secure the cluster:
  - TLS for traffic
  - Authentication + authorization (role mapping)
  - Network access control (VPC, private subnets)

Indexing pipeline & scale
- For production, decouple ingestion from the API:
  - API should validate and enqueue documents to a durable queue (Kafka/SQS/RabbitMQ).
  - Indexers (consumers) perform transformation and indexing, supporting retries and backpressure.
- Make indexing idempotent by deterministic document IDs.

Search reliability & performance
- Implement caching:
  - Query result cache (Redis) for hot queries (respect tenant isolation).
  - HTTP-level cache where appropriate (CDN) for public results.
- Monitor query latency, error rates, and tail latencies.
- Tune mappings and analyzers for target languages.

Observability & SRE
- Centralized logging (structured logs), distributed tracing (OpenTelemetry).
- Metrics: requests/tenant, search latency P50/P95/P99, OpenSearch health.
- Alerting: high error rates, index blockages, cluster red/yellow.

Security & Compliance
- Data encryption at rest and in transit.
- Secrets management for credentials.
- GDPR/data retention — ability to remove tenant data on request.

Deployment & CI/CD
- Blue/green or rolling deployments with health checks.
- Integration tests that run against an ephemeral OpenSearch test cluster.

Operational playbooks
- Runbooks for cluster recovery, index restore, scaling nodes, and dealing with index corruption.

Notes about prototype choices
- Rate-limiter and caching are single-instance and for dev convenience only.
- Tenant is trusted input only for rapid prototyping and review; production must not trust headers.
