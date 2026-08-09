"""Core data types for the evaluation framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvalRecord:
    """A single evaluation sample."""

    record_id: str
    problem: str
    reference: str
    category: str  # "chat" | "reasoning" | "rag" | "agentic"
    subject: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvalResult:
    """Result of evaluating a single sample."""

    record_id: str
    model_answer: str
    is_correct: bool | None = None
    score: float | None = None
    latency_seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    error: str | None = None
    scoring_metadata: dict[str, Any] = field(default_factory=dict)
    ttft: float = 0.0
    energy_joules: float = 0.0
    power_watts: float = 0.0
    gpu_utilization_pct: float = 0.0
    throughput_tok_per_sec: float = 0.0
    mfu_pct: float = 0.0
    mbu_pct: float = 0.0
    ipw: float = 0.0  # Intelligence Per Watt
    ipj: float = 0.0  # Intelligence Per Joule
    energy_per_output_token_joules: float = 0.0
    throughput_per_watt: float = 0.0
    mean_itl_ms: float = 0.0
    estimated_flops: float = 0.0
    trace_steps: int = 0
    trace_energy_joules: float = 0.0
    trace_data: dict[str, Any] | None = None
    # Spec §6.2 extended fields for cross-framework comparison
    framework: str = "openjarvis"
    framework_commit: str = ""
    tool_calls: int = 0
    turn_count: int = 0


@dataclass(slots=True)
class RunConfig:
    """Configuration for an evaluation run."""

    benchmark: str
    backend: str
    model: str
    max_samples: int | None = None
    max_workers: int = 4
    temperature: float = 0.0
    max_tokens: int = 2048
    judge_model: str = "gpt-5-mini-2025-08-07"
    judge_engine: str = "cloud"
    engine_key: str | None = None
    agent_name: str | None = None
    tools: list[str] = field(default_factory=list)
    output_path: str | None = None
    seed: int = 42
    dataset_split: str | None = None
    telemetry: bool = False
    gpu_metrics: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    warmup_samples: int = 0
    wandb_project: str = ""
    wandb_entity: str = ""
    wandb_tags: str = ""
    wandb_group: str = ""
    sheets_spreadsheet_id: str = ""
    sheets_worksheet: str = "Results"
    sheets_credentials_path: str = ""
    system_prompt: str = ""
    episode_mode: bool = False
    dataset_subset: str | None = None
    # Override the agent harness's max_turns budget. Default None means use
    # the JarvisConfig.agent.max_turns value (typically 10). Set higher when
    # running thinking/reasoning models that consume turns on intermediate
    # reasoning before producing tool calls.
    max_turns: int | None = None
    # Spec §6.2: backend-external endpoint config (for hermes/openclaw)
    base_url: str | None = None
    api_key: str | None = None
    # Filter dataset records by id. When set, only records whose record_id
    # appears in this list are processed. Used for surgical re-runs of
    # specific records (e.g. recovering silent-fake records without
    # re-running the entire benchmark).
    record_ids: list[str] | None = None


@dataclass(slots=True)
class MetricStats:
    """Descriptive statistics for a single metric across samples."""

    mean: float = 0.0
    median: float = 0.0
    min: float = 0.0
    max: float = 0.0
    std: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0


@dataclass(slots=True)
class RunSummary:
    """Summary statistics for a completed evaluation run."""

    benchmark: str
    category: str
    backend: str
    model: str
    total_samples: int
    scored_samples: int
    correct: int
    accuracy: float
    errors: int
    mean_latency_seconds: float
    total_cost_usd: float
    per_subject: dict[str, dict[str, float]] = field(default_factory=dict)
    started_at: float = 0.0
    ended_at: float = 0.0
    accuracy_stats: MetricStats | None = None
    latency_stats: MetricStats | None = None
    ttft_stats: MetricStats | None = None
    energy_stats: MetricStats | None = None
    power_stats: MetricStats | None = None
    gpu_utilization_stats: MetricStats | None = None
    throughput_stats: MetricStats | None = None
    mfu_stats: MetricStats | None = None
    mbu_stats: MetricStats | None = None
    ipw_stats: MetricStats | None = None
    ipj_stats: MetricStats | None = None
    energy_per_output_token_stats: MetricStats | None = None
    throughput_per_watt_stats: MetricStats | None = None
    itl_stats: MetricStats | None = None
    input_token_stats: MetricStats | None = None
    output_token_stats: MetricStats | None = None
    total_energy_joules: float = 0.0
    total_estimated_flops: float = 0.0
    flops_stats: MetricStats | None = None
    warmup_samples_excluded: int = 0
    steady_state_reached: bool = False
    energy_method: str = ""
    avg_power_watts: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    trace_step_type_stats: dict[str, dict[str, float]] = field(default_factory=dict)
    efficiency: dict[str, Any] | None = None
    normalized_statistics: dict[str, Any] | None = None
    normalized_efficiency: dict[str, Any] | None = None
    # Continuous-score reporting (added alongside binary accuracy so frontier
    # models do not saturate the metric on rubric-judge benchmarks).
    mean_continuous_score: float | None = None
    median_continuous_score: float | None = None
    pct_above_0_5: float | None = None
    pct_above_0_7: float | None = None
    pct_above_0_8: float | None = None
    pct_above_0_9: float | None = None
    # Internal fields set by the runner after construction
    _output_path: Path | None = None
    _traces_dir: Path | None = None


# ---------------------------------------------------------------------------
# Eval suite config dataclasses (TOML config system)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class MetaConfig:
    """Suite-level metadata."""

    name: str = ""
    description: str = ""


@dataclass(slots=True)
class DefaultsConfig:
    """Default generation parameters applied to all runs."""

    temperature: float = 0.0
    max_tokens: int = 2048


@dataclass(slots=True)
class JudgeConfig:
    """Configuration for the LLM judge."""

    model: str = "gpt-5-mini-2025-08-07"
    engine: str | None = None
    provider: str | None = None
    temperature: float = 0.0
    max_tokens: int = 1024


@dataclass(slots=True)
class ExecutionConfig:
    """Execution-level settings for the eval run."""

    max_workers: int = 4
    output_dir: str = "results/"
    seed: int = 42
    telemetry: bool = False
    gpu_metrics: bool = False
    warmup_samples: int = 0
    energy_vendor: str = ""
    wandb_project: str = ""
    wandb_entity: str = ""
    wandb_tags: str = ""
    wandb_group: str = ""
    sheets_spreadsheet_id: str = ""
    sheets_worksheet: str = "Results"
    sheets_credentials_path: str = ""
    # Override the agent harness's per-run max_turns budget. None falls back
    # to JarvisConfig.agent.max_turns (default 10). Bump to 30-50 for
    # thinking/reasoning models on agentic benchmarks (GAIA, LiveResearch).
    max_turns: int | None = None


@dataclass(slots=True)
class ModelConfig:
    """Configuration for a single model in the eval suite."""

    name: str = ""
    engine: str | None = None
    provider: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    param_count_b: float = 0.0
    active_params_b: float | None = None
    gpu_peak_tflops: float = 0.0
    gpu_peak_bandwidth_gb_s: float = 0.0
    num_gpus: int = 1


@dataclass(slots=True)
class BenchmarkConfig:
    """Configuration for a single benchmark in the eval suite."""

    name: str = ""
    backend: str = "jarvis-direct"
    max_samples: int | None = None
    split: str | None = None
    agent: str | None = None
    tools: list[str] = field(default_factory=list)
    judge_model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    subset: str | None = None
    record_ids: list[str] | None = None


@dataclass(slots=True)
class EvalSuiteConfig:
    """Top-level configuration for an eval suite (models x benchmarks)."""

    meta: MetaConfig = field(default_factory=MetaConfig)
    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    judge: JudgeConfig = field(default_factory=JudgeConfig)
    run: ExecutionConfig = field(default_factory=ExecutionConfig)
    models: list[ModelConfig] = field(default_factory=list)
    benchmarks: list[BenchmarkConfig] = field(default_factory=list)
    # Spec §6.2: optional [backend.external] section for hermes/openclaw
    # backends. Holds the OpenAI-compatible endpoint config.
    backend_external_base_url: str | None = None
    backend_external_api_key: str | None = None


__all__ = [
    "EvalRecord",
    "EvalResult",
    "MetricStats",
    "RunConfig",
    "RunSummary",
    "MetaConfig",
    "DefaultsConfig",
    "JudgeConfig",
    "ExecutionConfig",
    "ModelConfig",
    "BenchmarkConfig",
    "EvalSuiteConfig",
]
