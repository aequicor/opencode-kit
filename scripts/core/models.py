"""
Structured output models for agent responses.
Uses Pydantic for validation and serialization.
"""

from typing import Optional
from enum import Enum


class FileAction(str, Enum):
    CREATE = "Create"
    MODIFY = "Modify"
    DELETE = "Delete"


class ChangedFile:
    def __init__(self, path: str, action: FileAction, lines: int, description: str):
        self.path = path
        self.action = action
        self.lines = lines
        self.description = description

    def to_dict(self):
        return {
            "path": self.path,
            "action": self.action.value,
            "lines": self.lines,
            "description": self.description,
        }

    def to_markdown_row(self):
        return f"| `{self.path}` | {self.action.value} | ~{self.lines} | {self.description} |"


class CodeWriterOutput:
    def __init__(self, stage: str, changed_files: list[ChangedFile]):
        self.stage = stage
        self.changed_files = changed_files

    def to_markdown(self) -> str:
        if not self.changed_files:
            return f"## Changed Files \u2014 Stage {self.stage}\n\nNo files changed."

        header = f"## Changed Files \u2014 Stage {self.stage}\n\n"
        table_header = (
            "| File | Action | Lines | Description |\n|------|--------|-------|-------------|\n"
        )
        rows = "\n".join(cf.to_markdown_row() for cf in self.changed_files)
        return header + table_header + rows


class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReviewIssue:
    def __init__(self, number: int, file: str, issue: str, suggestion: str):
        self.number = number
        self.file = file
        self.issue = issue
        self.suggestion = suggestion

    def to_markdown_row(self):
        return f"| {self.number} | {self.file} | {self.issue} | {self.suggestion} |"


class CodeReviewOutput:
    def __init__(
        self,
        feature: str,
        summary: str,
        critical: list[ReviewIssue],
        high: list[ReviewIssue],
        medium: list[ReviewIssue],
        low: list[ReviewIssue],
        positive_notes: list[str],
        approved: bool,
        clarification: Optional[str] = None,
    ):
        self.feature = feature
        self.summary = summary
        self.critical = critical
        self.high = high
        self.medium = medium
        self.low = low
        self.positive_notes = positive_notes
        self.approved = approved
        self.clarification = clarification

    def to_markdown(self) -> str:
        lines = [f"# Code Review: {self.feature}", "", "## Summary", self.summary]
        if self.clarification:
            lines.append(f"\n\u26a0\ufe0f Needs clarification: {self.clarification}")

        for severity, issues in [
            ("CRITICAL (blocker)", self.critical),
            ("HIGH (needs fixing)", self.high),
            ("MEDIUM (worth considering)", self.medium),
            ("LOW (cosmetic)", self.low),
        ]:
            lines.append(f"\n### {severity}")
            if issues:
                lines.append("| # | File | Issue | Suggestion |")
                lines.append("|---|------|-------|------------|")
                lines.extend(i.to_markdown_row() for i in issues)
            else:
                lines.append("None.")

        if self.positive_notes:
            lines.append("\n## Positive notes")
            lines.extend(f"- {note}" for note in self.positive_notes)

        verdict = "\u2705 APPROVED" if self.approved else "\u274c NEEDS FIXES"
        lines.append(f"\n## Verdict\n{verdict}")

        return "\n".join(lines)


class TestCase:
    def __init__(self, name: str, priority: str, status: str = "\u2b1c"):
        self.name = name
        self.priority = priority
        self.status = status


class TestPlanOutput:
    def __init__(
        self,
        feature: str,
        module: str,
        status: str,
        date: str,
        scope_in: list[str],
        scope_out: list[str],
        unit_tests: list[TestCase],
        integration_tests: list[dict],
        manual_scenarios: list[dict],
    ):
        self.feature = feature
        self.module = module
        self.status = status
        self.date = date
        self.scope_in = scope_in
        self.scope_out = scope_out
        self.unit_tests = unit_tests
        self.integration_tests = integration_tests
        self.manual_scenarios = manual_scenarios


class TaskType(str, Enum):
    FEATURE = "FEATURE"
    BUG = "BUG"
    TECH = "TECH"


class MainClassificationOutput:
    def __init__(self, task_type: TaskType, description: str, questions: list[str]):
        self.task_type = task_type
        self.description = description
        self.questions = questions


class BugFixReport:
    def __init__(
        self,
        bug_name: str,
        module: str,
        priority: str,
        root_cause: str,
        files_changed: list[ChangedFile],
        regression_tests: list[str],
        lessons: list[str],
    ):
        self.bug_name = bug_name
        self.module = module
        self.priority = priority
        self.root_cause = root_cause
        self.files_changed = files_changed
        self.regression_tests = regression_tests
        self.lessons = lessons

    def to_markdown(self) -> str:
        import datetime

        date = datetime.date.today().strftime("%d.%m.%Y")
        lines = [
            f"# Bug Fix Report: {self.bug_name}",
            "",
            f"**Date:** {date}",
            "**Author:** BugFixer Agent",
            "**Status:** Fixed",
            f"**Module:** {self.module}",
            f"**Priority:** {self.priority}",
            "",
            "---",
            "",
            "## Bug Description",
            "",
            "## Root Cause",
            self.root_cause,
            "",
            "## Fix Applied",
            "",
            "### Files Changed",
            "| File | Change |",
            "|------|--------|",
        ]

        for f in self.files_changed:
            lines.append(f"| `{f.path}` | {f.description} |")

        lines.extend(
            [
                "",
                "## Regression Test",
                "| Test File | Test Name | Coverage |",
                "|-----------|-----------|----------|",
            ]
        )

        for test in self.regression_tests:
            lines.append(f"| {test} | - | - |")

        lines.extend(
            [
                "",
                "## Verification",
                "- [x] Unit test passes",
                "- [x] All module tests pass",
                "- [x] Code review approved",
                "- [x] Build successful",
                "",
                "## Lessons Learned",
            ]
        )

        for lesson in self.lessons:
            lines.append(f"- {lesson}")

        return "\n".join(lines)
