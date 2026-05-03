---
genre: reference
title: Test Cases Template
topic: testing
triggers:
  - "test cases"
  - "test execution"
  - "manual testing"
  - "test run"
confidence: high
source: human
updated: {{ISO_TIMESTAMP_PLACEHOLDER}}
---

# Test Cases: [Feature Name]

**Module:** [module-name]
**Feature:** [feature-slug]
**Status:** Draft | Active | Completed
**Date:** DD.MM.YYYY
**Author:** @TestRunner (generated) / @QA
**Spec:** [[reference/<module>/spec/<feature>]]
**Requirements:** [[concepts/<module>/requirements/<feature>]]
**Test Plan:** [[reference/<module>/spec/<feature>-test-plan]]

---

## Environment

| Parameter | Value |
|-----------|-------|
| Environment | [dev / staging / prod] |
| Version / Build | [commit hash or version] |
| Tester | [PO name or "automated"] |
| Date started | DD.MM.YYYY HH:MM |

---

## Test Cases

### TC-001: [Short descriptive name]

| Field | Value |
|-------|-------|
| **ID** | TC-001 |
| **Priority** | HIGH / MEDIUM / LOW |
| **Type** | Happy path / Edge case / Error / Security / Performance |
| **Preconditions** | List of preconditions |
| **Steps** | 1. Step one<br>2. Step two<br>3. Step three |
| **Expected Result** | What should happen |
| **Actual Result** | [FILLED DURING EXECUTION] |
| **Status** | ⬜ Not Run / ✅ Pass / ❌ Fail / ⏭️ Blocked / ⚠️ Partial |
| **Defect** | [DEF-NNN or link, if Fail/Blocked] |
| **Notes** | Additional observations |

---

### TC-002: [Short descriptive name]

| Field | Value |
|-------|-------|
| ... | ... |

---

## Defects Log

> Defects found during test execution. Each defect is linked from the corresponding test case above.

### DEF-001: [Short defect title]

| Field | Value |
|-------|-------|
| **ID** | DEF-001 |
| **Severity** | CRITICAL / HIGH / MEDIUM / LOW |
| **Related TC** | TC-NNN |
| **Description** | Clear description of what went wrong |
| **Steps to Reproduce** | 1. ...<br>2. ... |
| **Expected Behavior** | What should happen |
| **Actual Behavior** | What actually happened |
| **Fix Status** | 🔴 Open / 🟡 In Progress / 🟢 Fixed / 🔵 Verified |
| **Fixed By** | [@agent or human name] |
| **Fix Commit** | [commit hash] |
| **Verification TC** | [TC-NNN that verifies the fix] |
| **Notes** | Root cause, impact, etc. |

---

### DEF-002: [Short defect title]

| Field | Value |
|-------|-------|
| ... | ... |

---

## Execution Summary

| Metric | Value |
|--------|-------|
| **Total Test Cases** | 0 |
| ✅ Passed | 0 |
| ❌ Failed | 0 |
| ⏭️ Blocked | 0 |
| ⚠️ Partial | 0 |
| ⬜ Not Run | 0 |
| **Pass Rate** | 0% |
| **Defects Found** | 0 |
| 🔴 Open Defects | 0 |
| 🟡 In Progress | 0 |
| 🟢 Fixed | 0 |

---

## Transaction Log

> Append-only log of all changes to this file. Each entry represents one transaction — an atomic operation on the test cases document. The AI or human updates this log whenever the file is modified.

| # | Timestamp | Type | Author | Details |
|---|-----------|------|--------|---------|
| 1 | DD.MM.YYYY HH:MM | CREATE | @TestRunner | Initial test cases generated from spec and requirements |
| 2 | DD.MM.YYYY HH:MM | UPDATE | @TestRunner | Rerun after DEF-001 fixed — TC-003 status: ❌→✅ |
| 3 | DD.MM.YYYY HH:MM | DEFECT_ADD | [PO name] | DEF-002 added — TC-005 status: ⬜→❌ |

---

### Transaction Types

| Type | Description |
|------|-------------|
| `CREATE` | Initial generation of test cases document |
| `UPDATE` | Status change, result update, note addition |
| `DEFECT_ADD` | New defect found and logged |
| `DEFECT_FIX` | Defect fixed, verification test case updated |
| `RERUN` | Full or partial re-execution of test cases |
| `TC_ADD` | New test case added (e.g., for a newly found edge case) |
| `TC_REMOVE` | Test case removed (e.g., duplicate or out of scope) |
| `AMEND` | Correction to existing test case steps or expected result |