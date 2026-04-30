---
description: Start a new feature, bug fix, or tech task. Argument: $FEATURE_DESCRIPTION. Delegates to @Main for full orchestration.
---

You are starting a new task. Description: $FEATURE_DESCRIPTION

Hand off to `@Main` with the following prompt:

```
New task: $FEATURE_DESCRIPTION

Type: FEATURE (or clarify if this is BUG/TECH)
```

`@Main` will execute:
1. CLASSIFY & CLARIFY — ask clarifying questions in one message.
2. SEARCH — search KnowledgeOS on the topic.
3. PLAN — create requirements, spec, plan + stages via superpowers:writing-plans.
4. QA DRAFT — create test-plan.
5. CONFIRM — show summary to PO, wait for approve.
6. EXECUTE — implement via @CodeWriter → @CodeReviewer cycles.
7. QA FINAL — finalize test-plan.
8. CLOSE — documentation and checkpoint.

**Do not call @CodeWriter, @BugFixer or other agents directly — only @Main.**
