# H1 — Real User Testing & Usability Improvement

**Owner:** lnmthi
**Issue:** #62
**Branch:** `feat/h1-lnmthi-lab07`
**Integrated implementation:** PR #71 / commit `bb017ce`

## 1. Test objective

Evaluate whether a student outside the project team can independently use the assistant to:

1. Determine whether a student with 118 accumulated credits can register a thesis.
2. Find where to replace a lost student card.
3. Understand the assistant's answer, source information, and feedback controls.

The participant was allowed to interact with the UI independently. The tester did not guide or explain the answers during the tasks.

## 2. Original user-testing session

**Participant:** A student outside the project team (first name not recorded)
**Test date:** Not recorded
**Duration:** Not recorded

| Task | Result | Evidence / answer |
|---|---|---|
| Check thesis eligibility with 118 credits | Completed successfully | The assistant returned the minimum requirement of 120 accumulated credits and a cumulative GPA of at least 2.0. Source: `H26#5.3 — 5.3 Thesis registration`. |
| Find where to replace a lost student card | Completed successfully | The assistant identified Student Affairs, room I.102. Source: `S26#3`. |

The participant completed both recorded tasks.

**Important limitation:** Three distinct participant-reported or directly observed usability difficulties were not recorded during this session. The improvement opportunities in Section 4 are therefore heuristic observations, not claims about participant behavior.

## 3. Feedback interaction

The participant tried the Like and Dislike feedback controls.

- Like displayed: "Thanks for your feedback!"
- Dislike displayed: "Thanks — we will look at this answer."

These messages confirm that the UI displayed feedback acknowledgements. They do not independently verify that feedback was persisted successfully.

## 4. Post-test heuristic improvement opportunities

| ID | Improvement opportunity | Proposed improvement |
|---|---|---|
| UO-1 | The thesis answer states the 120-credit requirement, but the student must calculate whether 118 credits meets it. | Add a direct eligibility conclusion and state the credit shortfall when the question is unambiguous. |
| UO-2 | The lost-card answer identifies Student Affairs room I.102, but may not explain the next steps or required documents. | Provide further instructions only when supported by an authoritative source; otherwise advise the student to contact Student Affairs. |
| UO-3 | Source identifiers such as `H26#5.3` and `S26#3` may not be self-explanatory to new users. | Keep source titles prominent and identifiers secondary. |

These are heuristic opportunities identified after the original session. They must not be represented as three observed participant difficulties.

## 5. Improvement implemented — UO-1

**Before:** The answer stated the policy requirement (at least 120 accumulated credits and a cumulative GPA of at least 2.0), but did not explicitly calculate the student's shortfall.

**After:** The UI adds a direct conclusion when the thesis-registration question contains one unambiguous credit count below the minimum.

> Not eligible yet based on credits: 118 credits is 2 credits below the 120-credit minimum.

The original policy answer, including the GPA requirement and source, is preserved.

The helper avoids adding a conclusion when the question contains multiple credit counts or does not match the supported unambiguous pattern. The UI also avoids applying the helper to escalated responses.

**Implementation files:**
- `ui/presentation.py`
- `ui/app.py`
- `tests/test_ui_presentation.py`

**Regression coverage:** The test for "I took 18 credits this semester and have 118 credits in total" verifies that the helper preserves the original answer rather than calculating a misleading shortfall from 18.

- [x] Thesis eligibility presentation test added.
- [x] Non-thesis answer remains unchanged.
- [x] Answer without a detectable credit threshold remains unchanged.
- [x] `python -m pytest -q tests/test_ui.py tests/test_ui_presentation.py` — 10 passed.
- [x] `python -m ruff check ui tests/test_ui_presentation.py` — All checks passed.
- [x] Manually verified the 118-credit answer in the UI.
- [x] Technical screenshots of the same question in a real browser: [before](../../docs/lab07/evidence/before.png) and [after](../../docs/lab07/evidence/after.png). The screenshots were taken during integration testing, separately from the participant session.

The thesis wording was introduced in [the M6 branch](https://github.com/vinhdu1233-tech/assistant-core-team05/pull/67/files). The [integration fix](https://github.com/vinhdu1233-tech/assistant-core-team05/commit/bb017ce) restricts the extra conclusion to a grounded, unambiguous question.

## 6. Technical validation

The following checks were run locally on the integrated `main` commit `623fbab`:

| Check | Result |
|---|---|
| `python -m pytest -q` | 310 passed, 2 dependency deprecation warnings |
| `python eval/compare_paths.py --first 20` | Completed |
| `python eval/compare_paths.py` | Completed |
| `python -m ruff check .` | All checks passed |
| `python -m ruff format --check .` | 64 files already formatted |
| GitHub Actions CI #293 on `main` | Success |

The evaluation commands completed successfully as processes. Their reported incorrect benchmark cases remain evaluation accuracy results and are not represented as zero benchmark failures.

**Technical screenshots:**
- Before: `docs/lab07/evidence/before.png`
- After: `docs/lab07/evidence/after.png`

These screenshots were taken during integration testing, separately from the original participant session. They are technical before/after evidence, not participant-session screenshots.

## 7. Follow-up user-testing session — pending

A follow-up session is required to collect genuine usability observations and address the review request.

**Participant first name:** [Fill in after the session]
**Date:** [Fill in after the session]
**Duration:** [Fill in after the session]

### Tasks

1. Ask the participant to determine whether a student with 118 accumulated credits can register a thesis.
2. Ask the participant to find where to replace a lost student card.
3. Ask the participant to ask a follow-up question and interpret the answer's source information.

Do not explain the interface or lead the participant toward a particular answer. Record what the participant actually does and says.

### Three observed difficulties

| No. | Actual observed difficulty | Evidence (action, hesitation, or participant statement) | Related improvement |
|---|---|---|---|
| 1 | [Record only if observed] | [Record actual evidence] | [Link to a real fix, if applicable] |
| 2 | [Record only if observed] | [Record actual evidence] | [Proposed improvement] |
| 3 | [Record only if observed] | [Record actual evidence] | [Proposed improvement] |

If fewer than three difficulties are observed, report the actual number. Do not invent findings to fill the table.

### Follow-up evidence checklist

- [ ] Record participant first name only.
- [ ] Record test date and duration.
- [ ] Record actual observations and participant feedback.
- [ ] Capture relevant screenshots without exposing unnecessary personal information.
- [ ] Link at least one observed difficulty to an implemented improvement, if supported by the findings.
- [ ] Add the improvement commit or PR link.
- [ ] Re-run relevant tests after any new code changes.

## 8. Limitations and status

The original participant completed both recorded tasks. However, the original session did not record three distinct observed usability difficulties, the participant's first name, the exact test date, or the session duration.

UO-1 to UO-3 are explicitly classified as post-test heuristic opportunities, not fabricated participant findings.

The technical implementation has been integrated into `main` and the latest reported CI run is successful. The follow-up user-testing evidence remains pending and must be completed before claiming that all H1 review requirements have been satisfied.
