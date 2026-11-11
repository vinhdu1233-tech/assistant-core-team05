# Lab 5 — Member 1 (Issue #31): Persistent Feedback Repository

**Owner:** M1 `vinhdu1233-tech`  
**Base:** `setup/lab05-data` (not `main`)  
**Scope:** R1–R2 in `src/assistant_api/db.py`, plus focused tests and evidence.

## Requirement-to-implementation checklist

| Requirement | Evidence |
| --- | --- |
| R1 checks that `request_id` belongs to a real `Interaction` | `Repository.add_feedback()` queries `Interaction.request_id`; returns `None` on unknown IDs |
| R1 persists valid feedback | Instantiates `Feedback`, adds it, commits and refreshes, then returns the saved row |
| DB generates feedback ID | `db.refresh(fb)` after `db.commit()`; confirmed in `test_r1_saves_all_valid_ratings_with_database_id_and_fields` |
| R2 lists most recent first | `select(Feedback).order_by(Feedback.created_at.desc())` |
| R2 limits results, default 100 | `limit(limit)`; tested for 0, 1, 2, 100 and 200; verifies the 100 **newest** rather than the oldest |
| R2 protects against negative limits | Rejects `limit < 0` with `ValueError` to prevent SQLite's `LIMIT -1` (unbounded read) |
| Feedback can survive process restart | `test_r1_feedback_survives_reopening_file_backed_sqlite` closes the first SQLite engine, reopens the same DB file, and reads saved data |
| Privacy | `record_interaction()` remains unchanged; tests confirm a salted session hash and no raw-message columns |
| Lab 4 regression safety | No changes to `main.py`, `schemas.py`, `record_interaction()`, migrations, SQL exercises or teammate files |

The implementation intentionally follows the official tutorial's **Part E.4–E.5** examples. Existing SQLModel models and database initialization were **not** rewritten.

### Focused M1 test matrix

The additional regression cases in `tests/test_lab05_feedback_m1.py` cover:

| Area | Cases |
| --- | --- |
| Unknown feedback ID | Empty DB; DB with two existing interactions; SQL-like input; no orphan rows or consumed IDs |
| R1 saved data | Ratings -1/0/1, optional comment, DB-generated IDs, exact request association, foreign-key relationship |
| Multiple feedback records | Two ratings can reference one interaction, as permitted by the starter's one-to-many model |
| Text handling | Full 32-character request ID; 500-character optional comment; Unicode and SQL-looking characters retained as data |
| Created time | Compare persisted `created_at` with an actual UTC time window; account for SQLite's naive datetime deserialization |
| R2 ordering | Deterministic timestamps, descending order, 0/1/2/100/200 limits, newest 100 out of 105, empty DB |
| Negative limits | `limit=-1` / `-10` rejected instead of SQLite treating them as unlimited |
| Transaction safety | Synthetic commit exception leaves no partial Feedback row; existing Interaction remains |
| Restart persistence | File-backed SQLite engine disposed, recreated and data read back |
| Privacy | Salted session ID is stored instead of raw session; schema has no raw question column |

All tests use synthetic data. As required by Issue #31, **R1 relies on API validation** for ratings and comment length. The R1 repository implementation itself does not impose application-level Pydantic constraints; the SQL migration file provides a `CHECK` constraint when applied by the migration system. The test fixture using `SQLModel.metadata.create_all()` does not automatically reproduce every migration-specific constraint.


## How to run tests

From the repository root, after installing requirements:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q tests/test_db.py tests/test_lab05_feedback_m1.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
```

The added tests use in-memory SQLite except the persistence test, which uses a temporary file provided by pytest's `tmp_path`. They do not use real student information, live network calls, or credentials.

## Cross-member HTTP acceptance (M3 integration dependency)

**Important:** On the initial `setup/lab05-data` starter, the FastAPI endpoints still store feedback in a Python list. M3 (Issue #30) owns wiring `Repository` into the real FastAPI app. Completing R1/R2 **does not itself switch the API to persistent storage**, and this PR does not modify `main.py`.

Once M3 integrates repository access into FastAPI, verify all of the following **using a test SQLite database**:

1. Start API with an isolated on-disk `DATABASE_URL`, a non-production `SESSION_SALT` and a local `API_ADMIN_KEY`.
2. `POST /v1/chat` with a valid message; copy **its actual returned** `request_id`.
3. `POST /v1/feedback` with that request ID and `rating: 1`: expect **201**, a database-generated `id`, and matching `request_id`.
4. `POST /v1/feedback` with a made-up, nonexistent request ID: expect **404**; no row must be saved.
5. `GET /v1/feedback` without `X-API-Key` or with an incorrect key: expect **401**.
6. `GET /v1/feedback` with the correct `X-API-Key`: expect **200**, most recent feedback first, at most the configured `limit`.
7. Stop and restart the server **against the same DB file**, then repeat the authorized GET: feedback must still exist.
8. Confirm `/v1/chat`, Offices, Weather, existing Lab 4 tests and the enabled Rate Limiting test still pass.

Example payloads:

```json
{"message":"tuition for 18 credits and 2 retake","session_id":"demo-only"}
```

```json
{"request_id":"<actual id returned by POST /v1/chat>","rating":1,"comment":"Helpful"}
```

Do **not** reuse this placeholder `request_id` literally. No screenshots or live HTTP test results are claimed in this PR before M3's integration is complete.

## Data handling

- Persist: generated IDs, a hashed session ID, intent/topic/outcome/latency metadata, ratings and optional feedback comment.
- Do not persist: full student questions, raw session IDs, phone numbers or user names.
- Never commit `.env`, a real `SESSION_SALT`, API keys, or SQLite database files.
- `Repository.add_feedback()` expects API-layer Pydantic validation for ratings `-1, 0, 1` and comment length; this matches the starter contract. The migration's SQL `CHECK` constraint provides an additional safeguard **only on databases where the migration has been applied**.

## Team ownership / integration

- **M1 (#31):** R1–R2 repository logic, focused repository tests, this documentation.
- **M2 (#32):** Python SQLite D1–D3.
- **M3 (#30):** FastAPI database wiring, review/merge and `v0.5-data` tag.
- **M4 (#33):** migrations and additional database tests.
- **M5 (#34):** school SQL Q1–Q15.
- **M6 (#35):** assistant analytics F1–F3 and H2.

**Do not merge this feature directly to `main`.** Submit it for review into `setup/lab05-data` and have M3 verify the end-to-end API acceptance after integration.

## AI assistance disclosure

ChatGPT assisted with completing the two tutorial TODOs, test design, documentation and PR preparation. The repository's CI results and human review should be used to verify the submitted work.
