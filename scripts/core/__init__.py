from .version import KIT_VERSION, check_kit_version
from .credentials import check_credentials, looks_like_key
from .context import (
    build_context,
    _build_nested_context,
    _build_eval_template,
)
from .file_ops import (
    render,
    check_unresolved,
    get_target_path,
    collect_base_files,
    collect_editor_files,
    kit_path_to_target,
    create_docs_scaffold,
    print_postinstall_checklist,
)
from .verify import verify_output
from .schema import validate_manifest, print_schema_errors
from .models import (
    FileAction,
    ChangedFile,
    CodeWriterOutput,
    IssueSeverity,
    ReviewIssue,
    CodeReviewOutput,
    TestCase,
    TestPlanOutput,
    TaskType,
    MainClassificationOutput,
    BugFixReport,
)
from .telemetry import (
    AgentRun,
    TelemetryStore,
    get_telemetry,
    track_run,
)
from .prompts import (
    PROMPT_REGISTRY,
    PromptVersion,
    get_current_prompt_versions,
    bump_prompt_version,
)
from .plugins import (
    KitPlugin,
    discover_plugins,
    merge_plugin_files,
)
from .evaluation import (
    EvalCase,
    EvalResult,
    EvalSuite,
    load_suite,
)
from .costs import (
    CostTracker,
    ModelPricing,
    DEFAULT_PRICING,
    get_cost_tracker,
)

__all__ = [
    "KIT_VERSION",
    "check_kit_version",
    "check_credentials",
    "looks_like_key",
    "build_context",
    "_build_nested_context",
    "_build_eval_template",
    "render",
    "check_unresolved",
    "get_target_path",
    "collect_base_files",
    "collect_editor_files",
    "kit_path_to_target",
    "create_docs_scaffold",
    "print_postinstall_checklist",
    "verify_output",
    "validate_manifest",
    "print_schema_errors",
    "FileAction",
    "ChangedFile",
    "CodeWriterOutput",
    "IssueSeverity",
    "ReviewIssue",
    "CodeReviewOutput",
    "TestCase",
    "TestPlanOutput",
    "TaskType",
    "MainClassificationOutput",
    "BugFixReport",
    "AgentRun",
    "TelemetryStore",
    "get_telemetry",
    "track_run",
    "PROMPT_REGISTRY",
    "PromptVersion",
    "get_current_prompt_versions",
    "bump_prompt_version",
    "KitPlugin",
    "discover_plugins",
    "merge_plugin_files",
    "EvalCase",
    "EvalResult",
    "EvalSuite",
    "load_suite",
    "CostTracker",
    "ModelPricing",
    "DEFAULT_PRICING",
    "get_cost_tracker",
]
