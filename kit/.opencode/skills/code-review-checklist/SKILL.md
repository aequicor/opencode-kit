---
name: code-review-checklist
description: Systematic pre-commit code review checklist. Ensures all changes are reviewed before commit.
---

# Code Review Checklist

When reviewing a pull request or changeset, walk through every item.

## Functionality

- [ ] All acceptance criteria from the spec are addressed
- [ ] Edge cases are handled (null, empty, boundary values)
- [ ] Corner case register reviewed — every Critical item has a test
- [ ] Corner case register reviewed — every High item has an explicit decision (test or defer)
- [ ] Error states are handled with appropriate messages
- [ ] No regressions — existing functionality continues to work

## Code Quality

- [ ] Functions are small and single-purpose
- [ ] No magic numbers — use named constants
- [ ] Meaningful variable and function names
- [ ] No dead code, commented-out blocks, or unused imports
- [ ] Consistent formatting (auto-formatter applied)

## Architecture

- [ ] No circular dependencies between modules
- [ ] Correct layering: domain → service → controller/presentation
- [ ] Dependency injection used where appropriate
- [ ] Interfaces defined at module boundaries

## Testing

- [ ] Unit tests cover happy path + error cases
- [ ] Integration tests cover API contracts
- [ ] Tests are deterministic (no Thread.sleep, real network calls)
- [ ] All tests pass: `{{TEST_COMMAND_TEMPLATE}}`

## Security

- [ ] Input validation on all external inputs
- [ ] SQL via parameterized queries only
- [ ] No tokens, passwords, or PII in logs
- [ ] Authentication/authorization checks not weakened
- [ ] No sensitive data in error responses

## Performance

- [ ] No N+1 queries in loops
- [ ] Appropriate caching strategy
- [ ] Resources closed properly (connections, files, streams)
- [ ] No blocking calls on UI/main threads

## Documentation

- [ ] Public API documented
- [ ] Complex logic has inline comments explaining WHY, not WHAT
- [ ] Spec/requirements match implementation
- [ ] Any new guidelines saved to `.vault/guidelines/[module]/`
