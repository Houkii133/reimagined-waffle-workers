# Architecture Overview

The Reimagined Job Board is a monorepo with a FastAPI backend and a Next.js frontend that orchestrate an AI recommendation engine.

## Request Lifecycle

1. **User Interaction** – The React-based UI (Next.js App Router) renders pages and client components using Tailwind CSS and shadcn-inspired primitives. React Query manages data fetching.
2. **API Requests** – Client components call typed REST endpoints under `/api/v1` with JWT authentication headers. The `apiFetch` helper centralizes base URL configuration.
3. **Backend Handling** – FastAPI routers authenticate requests, validate payloads with Pydantic schemas, and interact with SQLModel ORM models persisted in PostgreSQL.
4. **AI Integration** – Data flows through `engine_service`, which maps SQLModel instances to the `ai_job_matcher` domain models and invokes `JobMatchEngine` methods. Responses are serialized back to clients with rationale and gap explanations.
5. **Feedback Loop** – Feedback events are persisted in the database, forwarded to the engine, and React Query optimistically updates cached recommendation lists.
6. **Background Tasks** – Celery workers ingest new jobs and refresh engine caches. Redis acts as the broker/result backend, ensuring asynchronous processing.
7. **Admin Telemetry** – Admin endpoints expose aggregated engine metrics and feature flag management. The admin dashboard polls these metrics for observability.

## Data Model Highlights

- `users` table stores authentication and role metadata. Related tables `user_profiles`, `jobs`, `feedback_events`, etc., capture structured attributes for matching.
- Array-like fields are persisted via SQLModel `List[str]` columns for rapid prototyping; production deployments can normalize into association tables if needed.
- Feature flags are persisted in the database and may be hydrated from `config/feature_flags.yaml` during startup.

## Security

- Passwords are hashed via Passlib (`bcrypt`).
- OAuth2 password flow issues JWT access tokens with configurable expiry.
- Admin routes require the `is_admin` flag. Rate limiting and CSRF protection can be layered via ASGI middleware.

## Extensibility

- Additional background tasks (daily recommendation refresh, telemetry export) can be plugged into Celery.
- The frontend design system is componentized under `frontend/components`, enabling rapid UI expansion.
- The engine wrapper isolates the AI dependency, allowing drop-in replacement with a hosted service.
