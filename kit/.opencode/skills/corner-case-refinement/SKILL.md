---
name: corner-case-refinement
description: Systematic corner case discovery and refinement. Use during brainstorming and writing-plans to surface edge cases, boundary conditions, error states, and race conditions BEFORE implementation. Prevents rework by catching unknowns early.
---

# Corner Case Refinement Skill

Systematically discover, classify, and document corner cases before a single line of code is written. Integrates into the design → plan pipeline to eliminate late-cycle surprises.

## When to Use

Activate whenever any of these are true:

- **Brainstorming phase** — after design sections are approved, before writing spec
- **Writing-plans phase** — after file structure is mapped, before task decomposition
- **Review phase** — before approving an implementation plan
- **Debugging phase** — when a bug suggests systematic gaps in corner case analysis
- **ANY feature** where inputs come from users, network, filesystem, or external APIs

## Corner Case Categories

Use this taxonomy to systematically scan every aspect of the feature:

### 1. Input Space Boundary Analysis

For every input field, parameter, or data source:

| Condition | Check |
|-----------|-------|
| **Null / None** | What if the value is missing entirely? |
| **Empty** | Zero-length string, empty list, empty dict, zero? |
| **Minimum** | Smallest valid value — what about one less? |
| **Maximum** | Largest valid value — what about one more? |
| **Unicode / encoding** | Emojis, RTL text, combining characters, null bytes |
| **Type mismatch** | String where int expected, list where dict expected |
| **Injection** | SQL, HTML/JS/XSS, shell metacharacters, format strings |
| **Encoding drift** | Latin-1 in UTF-8 field, mixed line endings |

### 2. State & Lifecycle

For every stateful entity:

| Condition | Check |
|-----------|-------|
| **Initial** | What before any operation? Is default state valid? |
| **Transition** | Every state → every reachable state? |
| **Duplicate** | Same operation twice in a row? |
| **Out-of-order** | Operation B before required operation A? |
| **Interrupted** | What if process dies mid-operation? |
| **Idempotency** | Repeated operation yields same result? |

### 3. Concurrency & Timing

For shared resources and multi-user scenarios:

| Condition | Check |
|-----------|-------|
| **Race** | Two operations on same entity simultaneously? |
| **Deadlock** | Lock ordering — could A wait on B while B waits on A? |
| **Starvation** | Could a low-priority operation wait forever? |
| **Timeout** | What if downstream call takes 30s? 120s? Never responds? |
| **Clock skew** | What if system clocks differ across nodes? |
| **Partial failure** | Succeeded on node A, failed on node B? |

### 4. Error & Exception Paths

For every external dependency:

| Condition | Check |
|-----------|-------|
| **Network** | DNS failure, connection refused, TLS error, reset? |
| **Rate limit** | HTTP 429 at the worst possible moment? |
| **Auth** | Token expired mid-request, credentials revoked? |
| **Data corruption** | Truncated response, malformed JSON, wrong schema? |
| **Disk** | Disk full, permission denied, file locked by another process? |
| **Memory** | Out of memory during processing of large payload? |
| **Dependency version** | Library upgraded — breaking change in minor version? |

### 5. Scale & Load

For data-intensive operations:

| Condition | Check |
|-----------|-------|
| **Zero items** | List with zero elements — divide by zero? |
| **One item** | Edge of batch logic — off-by-one in pagination? |
| **Huge input** | 100k items, 1GB payload, 10k concurrent users? |
| **Batching** | What if total items not evenly divisible by batch size? |
| **Deeply nested** | Recursion limit, stack overflow, max depth exceeded? |
| **Degrade gracefully** | Does it fail fast or degrade under load? |

### 6. Domain-Specific Invariants

For business logic:

| Condition | Check |
|-----------|-------|
| **Negative** | Negative quantity, negative balance, negative time? |
| **Future / Past** | Date in 2099? Date in 1900? |
| **Identity** | Two entities with same unique key? |
| **Circular** | Parent references itself (org chart, folder, comment)? |
| **Cross-module** | Operation spans two modules — partial success? |
| **Rollback** | What if step 3 of 5 fails? How do we undo steps 1-2? |

## Systematic Discovery Process

### Step 1: Input Mapping

List every input entry point to the feature:
- API parameters (path, query, body, headers)
- User form fields
- File reads
- Database queries
- Environment variables
- Message queue payloads
- External API responses

For each input, run **boundary analysis** from category 1.

### Step 2: State Model Mapping

Identify every stateful entity:
- Entities with lifecycle (created → active → suspended → deleted)
- Workflow states (draft → review → approved → published)
- Connection states (disconnected → connecting → connected → reconnecting)
- Transaction states (pending → committed → rolled back)

For each entity-state pair, run **state & lifecycle analysis** from category 2.

### Step 3: Dependency Graph

Map every external call:
- Database queries
- HTTP/gRPC calls
- Message queue publish/consume
- Filesystem operations
- Cache reads/writes

For each dependency, run **error & exception analysis** from category 4.

### Step 4: Concurrency Scan

Identify shared mutable state:
- Database rows updated by multiple flows
- In-memory caches
- File writes from concurrent threads
- Global counters or aggregations

For each shared resource, run **concurrency analysis** from category 3.

### Step 5: Scale Projection

For each data collection point:
- What is the expected size? The maximum size? The pathological size?
- Does any algorithm have O(n²) or worse complexity?
- Are there unbounded collections (no pagination, no limit)?

Run **scale & load analysis** from category 5.

### Step 6: Invariant Check

List every business rule:
- "Quantity must be positive"
- "Users can only edit their own resources"
- "Orders must have at least one line item"

For each invariant, run **domain-specific analysis** from category 6.

## Output Format

Produce a structured corner case register:

```markdown
## Corner Case Register — [Feature Name]

### Critical (would cause data loss, security breach, or system crash)

| # | Category | Condition | Expected Behavior | Test Coverage |
|---|----------|-----------|-------------------|---------------|
| 1 | Boundary | Empty request body → POST /orders | Return 400 with validation error | ❌ |
| 2 | Concurrency | Two simultaneous updates to same order | Last-write-wins or optimistic lock error | ❌ |

### High (would cause incorrect behavior visible to user)

| # | Category | Condition | Expected Behavior | Test Coverage |
|---|----------|-----------|-------------------|---------------|
| 3 | Error | Payment gateway timeout after 30s | Retry with idempotency key, max 3 attempts | ❌ |

### Medium (edge cases unlikely but possible)

| # | Category | Condition | Expected Behavior | Test Coverage |
|---|----------|-----------|-------------------|---------------|

### Low (cosmetic or non-functional)

| # | Category | Condition | Expected Behavior | Test Coverage |
|---|----------|-----------|-------------------|---------------|
```

## Integration with Writing Plans

After producing the corner case register, hand it off to `writing-plans`:

1. **Every Critical item MUST become a test task in the plan** — do not proceed without test coverage for critical corner cases.
2. **Every High item SHOULD become a test task** — PO can decide to defer, but the decision is explicit.
3. **Medium and Low items** are noted in the plan for awareness but not mandatory.

The corner case register is saved alongside the plan:
- Plan: `.vault/concepts/<module>/plans/<feature>-plan.md`
- Corner cases: `.vault/concepts/<module>/plans/<feature>-corner-cases.md`

## Principles

- **Discover before you build.** Every corner case found during implementation is a failure of planning.
- **Zero surprises.** If you cannot say "we knew about that case and decided to handle it this way," the analysis was incomplete.
- **Explicit over implicit.** "Handle edge cases" is not a plan. Name every edge case.
- **Severity-driven priority.** Not all corner cases are equal — focus on data loss, security, and user-visible errors first.
- **Test coverage is proof.** A corner case without a test is a wish, not evidence.
- **No false precision.** Don't fabricate corner cases for completeness. Only list cases that can actually occur given the system architecture.
- **YAGNI for corners.** Don't handle scale-5 corners on a scale-1 system. But DO document why they're excluded.

## Red Flags

- **"This is simple, no corner cases"** — Simple features have the most hidden assumptions. At minimum run input boundary analysis.
- **Skipping the register** — Undocumented corner cases are invisible corner cases. They will bite you.
- **All corner cases are Medium or Low** — If nothing is Critical or High, you haven't looked hard enough.
- **No test tasks for Critical items** — The plan is incomplete. Stop and add them.

## Self-Review

After producing the register, verify:

1. **Coverage:** Did you run all 6 categories? If a category doesn't apply, write why.
2. **Severity calibration:** Are Critical items truly critical (data loss, security, crash)? Are High items truly user-visible incorrectness?
3. **Testability:** Can each corner case be turned into a concrete test? If not, rephrase until it can.
4. **No vagueness:** "Handle edge cases" → reject. "Return 409 Conflict when duplicate order ID submitted" → accept.
