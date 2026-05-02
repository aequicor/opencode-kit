---
description: Run the full AI-driven requirements pipeline for a new feature. Chains BA → CornerCaseReviewer → QA → CoverageChecker → SA → CornerCaseReviewer (tech) → ConsistencyChecker. Only PO sign-off required at the end. Argument: $FEATURE_DESCRIPTION
---

You are starting the requirements pipeline for a new feature.

Feature description: $FEATURE_DESCRIPTION

Hand off to `@RequirementsPipeline` with the following prompt:

```
New requirements pipeline task.

Feature description: $FEATURE_DESCRIPTION
```

`@RequirementsPipeline` will execute the full automated pipeline:

1. **INTAKE** — parse feature name and module from description.
2. **BA DRAFT** — @BusinessAnalyst generates requirements document.
3. **CC BUSINESS** — @CornerCaseReviewer attacks requirements (up to 3 iterations with @BusinessAnalyst).
4. **QA DRAFT** — @RequirementsQA generates test cases from requirements + corner cases.
5. **COVERAGE** — @CoverageChecker verifies all requirements and corner cases have test cases.
6. **SA DRAFT** — @SystemAnalyst generates technical spec from requirements + test cases.
7. **CC TECHNICAL** — @CornerCaseReviewer attacks tech spec (up to 3 iterations with @SystemAnalyst).
8. **CONSISTENCY** — @ConsistencyChecker verifies spec does not contradict requirements.
9. **SIGN-OFF** — presents complete artifact package to PO for `/approve`.

After `/approve`, the artifacts are ready to hand to `@Main` for development planning via `/new-feature`.

**Do not call individual pipeline agents directly — only @RequirementsPipeline.**
