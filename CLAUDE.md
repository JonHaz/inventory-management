# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

Factory Inventory Management System — a Claude Code workshop demo app. Full-stack: Vue 3 frontend, Python FastAPI backend, in-memory mock data loaded from JSON files (no database).

**Always document non-obvious logic changes with comments.** When a change isn't self-explanatory from the code alone — a workaround, a non-obvious ordering dependency, a calculation whose inputs aren't visible locally (e.g. the hardcoded revenue-goal math below) — leave a short comment explaining the *why*, not the *what*.

## Commands

**Install:**
```bash
cd server && uv venv && uv sync
cd client && npm install
```

**Run both servers** (one-command, macOS/Linux only):
```bash
./scripts/start.sh   # backend :8001, frontend :3000, logs to /tmp/inventory-*.log
./scripts/stop.sh
```

**Run individually:**
```bash
cd server && uv run python main.py   # http://localhost:8001, docs at /docs
cd client && npm run dev             # http://localhost:3000
```

**Tests** (backend only — no frontend test suite exists):
```bash
cd tests && uv run pytest -v                                                    # all tests
cd tests && uv run pytest backend/test_inventory.py -v                          # one file
cd tests && uv run pytest backend/test_inventory.py::TestInventoryEndpoints -v  # one class
cd tests && uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v  # one test
cd tests && uv run pytest --cov=../server --cov-report=html                     # coverage
```
Tests use `sys.path` injection (`tests/backend/conftest.py`) to import `server/main.py` directly — they don't depend on the server running.

**Build:**
```bash
cd client && npm run build   # output: client/dist/
```

## Architecture

**Data flow:** Vue filter state (`useFilters` composable) → query params → `client/src/api.js` (axios) → FastAPI route → `apply_filters()`/`filter_by_month()` in `server/main.py` → in-memory list filtering over data loaded from `server/data/*.json` by `server/mock_data.py` → Pydantic `response_model` validation → JSON → Vue computed properties derive chart/table data from raw refs.

**Filter system:** Four filters — Time Period, Warehouse, Category, Order Status — live as a *singleton* module-level state in `client/src/composables/useFilters.js` (refs declared outside the exported function, so every component sees the same instance). `getCurrentFilters()` maps UI state to the API's query param shape (e.g. `selectedPeriod` → `month`). Inventory endpoints don't support `month` — there's no time dimension on inventory records.

**Backend structure:** Single-file `server/main.py` — Pydantic models, filter helpers (`apply_filters`, `filter_by_month`), and all routes together. `QUARTER_MAP` translates `Q1-2025`..`Q4-2025` into constituent month strings for `filter_by_month`. Filtering is case-insensitive on category/status and mutates copies, never the loaded lists. `server/mock_data.py` loads each `server/data/*.json` file once at import time into module-level lists/dicts that every request reads.

**Known gap:** `client/src/api.js` calls `/api/tasks` (get/create/delete/toggle) and the task UI (`TasksModal.vue`, `useAuth.js`'s mock `currentUser.tasks`) expects it, but `server/main.py` defines no `/api/tasks` route — this 404s in the browser console on load. Whether to add it depends on the workshop exercise in play; don't "fix" it silently.

**i18n:** `client/src/composables/useI18n.js` is a from-scratch key-lookup translator (not vue-i18n) reading `client/src/locales/{en,ja}.js`, with English fallback for missing keys and separate helper functions (`translateProductName`, `translateCustomerName`, `translateWarehouse`) for translating *data* values (not just UI strings) since mock data itself has locale-specific rendering (e.g. Japanese customer/product names, city name maps). Locale persists to `localStorage['app-locale']`. Currency follows locale 1:1 (`en`→USD, `ja`→JPY) via `currentCurrency`, converted client-side in `client/src/utils/currency.js` using a hardcoded `USD_TO_JPY` rate — there's no live FX lookup.

**Routing:** Flat, single-level (`client/src/main.js`) — no nested routes, no route guards. Views: `/`, `/inventory`, `/orders`, `/demand`, `/spending`, `/reports`.

**Auth:** `useAuth.js` is fully mocked — `isAuthenticated` is hardcoded `true`, `logout()` just alerts. Don't build real auth flows against it without asking; it's a demo stand-in only.

## Subagents (this repo has project-specific ones)

- **vue-expert** (`.claude/agents/vue-expert.md`): **any** creation or significant modification of a `.vue` file must be delegated to this agent — that's a hard rule in the original CLAUDE.md this file supersedes, keep following it.
- **code-reviewer**: after writing significant code.
- **security-auditor**: fast pass over changed files only.
- **Explore** / **general-purpose**: codebase understanding and multi-step tasks.

## MCP tools

- Use `mcp__github__*` for all GitHub operations, **except** local branch creation — use `git checkout -b` (not `mcp__github__create_branch`).
- Use `mcp__playwright__*` for browser testing against `http://localhost:3000` (frontend) and `http://localhost:8001` (API).

## Common pitfalls specific to this codebase

1. `v-for` keys: use `sku`/`month`/other stable IDs, never array `index` — several views iterate re-sortable/filterable lists.
2. Validate dates before `.getMonth()`/`.getTime()` — order dates come from JSON and aren't guaranteed parseable.
3. Pydantic models in `server/main.py` must be updated in lockstep with `server/data/*.json` shape changes, or `response_model` validation breaks requests silently (empty coercions) or loudly (422s).
4. Revenue goal math is hardcoded in `Dashboard.vue`: $800K/month single-month view, $9.6M when viewing all 12 months — don't reintroduce this as a per-API-call fetch, it's intentionally a client constant.
