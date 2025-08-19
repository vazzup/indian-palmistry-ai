# Project Rules

## Overview
This document defines the rules for an AI-first, modular, and scalable codebase. It consolidates constraints and practices from `project-overview.md`, `user-flow.md`, `tech-stack.md`, `ui-rules.md`, and `theme-rules.md`. All guidance here is binding for code, docs, and tooling.

## Core Principles

- **AI-first**: Small, composable modules; predictable patterns; rich metadata to help AI tools read and modify code safely.
- **Readable by default**: Descriptive file and symbol names; explicit control flow; early returns; minimal nesting.
- **Single responsibility**: Each file and function does one thing well.
- **Hard limits**: Files must not exceed 500 lines. Split before you reach the limit.
- **Documentation**: Every file begins with a header explaining its purpose and contents. Every function has a docstring (JSDoc/TSDoc or Python docstring) describing intent, parameters, return values, and errors.
- **Deterministic structure**: Standardized directory layout; consistent naming; versioned APIs; stable DTOs.

## Repository Structure

```
astrology-backend/
├── app/                               # FastAPI backend
│   ├── main.py                        # FastAPI app factory and startup hooks
│   ├── api/
│   │   ├── deps.py                    # Shared dependencies (auth/session/db)
│   │   └── v1/                        # API v1 (path-based versioning)
│   │       ├── auth.py                # Login/logout/register endpoints
│   │       ├── analyses.py            # Create/list/get analyses (2 images max)
│   │       └── conversations.py       # CRUD and chat, scoped to analysis
│   ├── core/
│   │   ├── config.py                  # Settings from .env
│   │   ├── security.py                # Cookie/session, CSRF, hashing
│   │   ├── database.py                # SQLite + SQLAlchemy (WAL, pragmas)
│   │   └── logging.py                 # Structured JSON logging
│   ├── models/                        # SQLAlchemy models
│   │   ├── user.py
│   │   ├── analysis.py
│   │   └── conversation.py
│   ├── schemas/                       # Pydantic v2 DTOs
│   │   ├── auth.py
│   │   ├── analyses.py
│   │   └── conversations.py
│   ├── services/                      # Business logic (pure functions preferred)
│   │   ├── openai_service.py          # gpt-4.1-mini image + chat helpers
│   │   ├── file_service.py            # JPEG/PNG validation; disk storage
│   │   ├── auth_service.py            # Sessions; bcrypt; CSRF helpers
│   │   └── analysis_service.py        # Orchestration for analyses
│   ├── utils/                         # Small helpers (no app coupling)
│   │   ├── validators.py
│   │   └── ids.py                     # UUID/ULID helpers
│   └── exceptions/                    # App-specific exceptions
│       ├── auth_exceptions.py
│       ├── file_exceptions.py
│       └── service_exceptions.py
├── frontend/                          # Next.js app (App Router)
│   ├── app/
│   │   ├── (marketing)/page.tsx
│   │   ├── (app)/analyses/page.tsx
│   │   ├── (app)/analyses/[id]/page.tsx
│   │   ├── (app)/login/page.tsx
│   │   └── layout.tsx
│   ├── components/
│   └── lib/
├── tests/                             # Backend tests (pytest)
│   ├── test_api/
│   ├── test_services/
│   └── test_models/
├── _docs/                             # Documentation (this folder)
└── .env.example                       # Example environment configuration
```

Notes:
- Frontend is entirely in Next.js per decisions. Conversations are accessed through analyses; analyses list is paginated (most recent first, page size 5).
- Single container deployment is permitted; prefer supervisor + reverse proxy with health checks.

## File Naming and Size Rules

- Names must be descriptive and specific. Avoid generic names like `utils.py` unless scoped (e.g., `app/utils/validators.py`).
- Use language-idiomatic casing: Python uses `snake_case.py`, TypeScript uses `camelCase` for files in components and `kebab-case` for routes if preferred by Next.
- Suffixes communicate roles: `*_service.py`, `*_schema.py`, `*_model.py`, `*_exceptions.py`.
- Hard limit: 500 lines per file (including imports and comments). Split into modules when approaching 450 lines.

## File Headers and Docstrings

Every source file starts with a header comment explaining:
- File name and purpose
- Module responsibilities and key exported symbols
- Dependencies (internal and external)
- Example usage (when helpful)

Function standards:
- Python: triple-quoted docstrings describing purpose, parameters, return type, raised exceptions, and examples where relevant.
- TypeScript: TSDoc for all exported functions, hooks, and components. Include prop descriptions and usage notes.

## Coding Standards

- Prefer pure functions; avoid classes unless modeling rich domain entities.
- Explicit types: Pydantic v2 for DTOs; SQLAlchemy typed models; TS types and Zod schemas on the frontend.
- Control flow: guard clauses and early returns; keep nesting shallow; handle error/edge cases first.
- Error handling: raise specific exceptions; never swallow errors silently; centralize HTTP error mapping.
- Naming: verbs for functions; nouns for variables and files; avoid abbreviations; use full words.
- Do not introduce enums in Python; use maps/dicts. In TypeScript, use object maps or const unions.

## API and Domain Rules

- Versioning: all backend routes under `/api/v1`.
- Analyses: accept up to two images (left/right). Post-analysis summary is visible unauthenticated; full results and conversation require login.
- Conversations: are scoped under an analysis; support list (most recent first, page size 5), update (rename/edit metadata/append messages), and delete (cascade).
- Deletion: removing an analysis deletes its images and all related conversations.

## Data and Storage Rules

- Database: SQLite with WAL; short transactions; indexes on `user_id`, `analysis_id`, `created_at`.
- Files: JPEG/PNG only; max 15 MB each; stored at `/data/images/{user_id}/{analysis_id}/` with UUID filenames; EXIF stripped.
- Config: environment via `.env`; provide `.env.example`. Never check in real secrets.

## Frontend (Next.js) Rules

- App Router with Server Components by default; Client Components for interactivity.
- Data fetching: use native `fetch` in server components for reads; TanStack Query for client mutations and chat.
- Forms: React Hook Form + Zod; validate constraints (max 2 images, types, size) in UI.
- Accessibility: follow `ui-rules.md` (touch targets, breakpoints, icon labeling) and `theme-rules.md` (contrast, color usage).

## Logging, Performance, and Limits

- Logging: JSON to stdout; include correlation IDs; no secrets or raw images in logs.
- Rate limiting: basic per-process limiter acceptable for single-container MVP.
- Caching: in-memory TTL caches for hot paths; document invalidation.
- Performance budgets: mobile-first; optimize for low bandwidth; avoid heavy client bundles.

## Testing and Linting

- Backend: pytest + httpx + pytest-asyncio; temp SQLite DB; factory fixtures.
- Frontend: Playwright for E2E; Vitest + RTL for components; MSW for network mocks.
- Linters/formatters: Black, Ruff, mypy on backend; ESLint/Prettier on frontend. CI must fail on lints/tests.

## Commit and Branching Rules

- Conventional commits: `type(scope): description`.
- Branch naming: `feature/*`, `fix/*`, `docs/*`, `test/*`, `refactor/*`.

## Review Checklist (per PR)

- Files < 500 lines and well named
- File header present; exported symbols documented
- Functions have docstrings/TSDoc with parameter and return docs
- No mixed sync/async in FastAPI handlers; no blocking work on event loop
- DTOs validated; errors mapped consistently; logs are structured and sanitized
- UI follows `ui-rules.md`; theme usage adheres to `theme-rules.md`

These rules ensure a consistent, maintainable, and AI-friendly project that reflects our user flow, tech stack, UI principles, and cultural minimalistic theme.
