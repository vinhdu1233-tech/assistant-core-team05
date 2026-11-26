# Lab 7 H1 — Real User Testing & Usability Improvement

**Owner:** lnmthi
**Issue:** #62
**Branch:** `feat/h1-lnmthi-lab07`
**Participant:** A student outside the project team (name not recorded)
**Test date:** Not recorded
**Duration:** Not recorded

## 1. Test objective

Evaluate whether a student outside the team can use the assistant to:
1. Determine whether a student with 118 accumulated credits can register a thesis.
2. Find where to replace a lost student card.

The participant was allowed to interact with the UI independently. The tester did not guide or explain the answers during the tasks.

## 2. Task results

| Task | Result | Evidence / answer |
|---|---|---|
| Check thesis eligibility with 118 credits | Completed successfully | The assistant returned the minimum requirement of 120 accumulated credits and a cumulative GPA of at least 2.0. Source: `H26#5.3 — 5.3 Thesis registration`. |
| Find where to replace a lost student card | Completed successfully | The assistant identified Student Affairs, room I.102. Source: `S26#3`. |

The participant completed both tasks. No three distinct participant-reported misunderstandings were recorded during this session. The observations below are therefore post-test heuristic improvement opportunities, not problems claimed to have been observed from the participant.

## 3. Feedback interaction

The participant tried the Like and Dislike feedback controls.

- Like displayed: "Thanks for your feedback!"
- Dislike displayed: "Thanks — we will look at this answer."

These messages confirm that the UI displayed feedback acknowledgements. They do not, by themselves, verify that feedback was persisted successfully.

## 4. Post-test improvement opportunities

| ID | Improvement opportunity | Proposed improvement |
|---|---|---|
| UO-1 | The thesis answer states the 120-credit requirement, but the student must calculate whether 118 credits meets it. | Add a direct eligibility conclusion and state the credit shortfall. |
| UO-2 | The lost-card answer identifies Student Affairs room I.102, but may not explain the next steps or required documents. | Provide further instructions only when supported by an authoritative source; otherwise advise the student to contact Student Affairs. |
| UO-3 | Source identifiers such as `H26#5.3` and `S26#3` may not be self-explanatory to new users. | Keep source titles prominent and identifiers secondary. |

## 5. Improvement implemented — UO-1

**Before:** The answer stated the policy requirement (at least 120 accumulated credits and a cumulative GPA of at least 2.0), but did not explicitly calculate the student's shortfall.

**After:** The UI adds a direct conclusion when a thesis-registration question includes a credit count below the minimum:

> Not eligible yet based on credits: 118 credits is 2 credits below the 120-credit minimum.

The original policy answer, including the GPA requirement and source, is preserved.

**Implementation files:**
- `ui/presentation.py`
- `ui/app.py`
- `tests/test_ui_presentation.py`

## 6. Validation

- [x] Thesis eligibility presentation test added.
- [x] Non-thesis answer remains unchanged.
- [x] Answer without a detectable credit threshold remains unchanged.
- [x] `python -m pytest -q tests/test_ui.py tests/test_ui_presentation.py` — 10 passed.
- [x] `python -m ruff check ui tests/test_ui_presentation.py` — All checks passed.
- [x] Manually verified the 118-credit answer in the UI.
- [ ] Add before/after screenshots to the PR or attach them to the issue.

## 7. Limitations

The participant completed both tasks, but the session did not produce three distinct observed misunderstandings. UO-1 to UO-3 are transparently documented as post-test heuristic opportunities rather than fabricated participant findings.

The exact test date, duration, and participant first name were not recorded.
