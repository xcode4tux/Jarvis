"""Bundle dataclasses that group cohesive subsystems of JarvisSystem."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openjarvis.agents._stubs import BaseAgent
    from openjarvis.agents.executor import AgentExecutor
    from openjarvis.agents.manager import AgentManager
    from openjarvis.agents.scheduler import AgentScheduler
    from openjarvis.scheduler.scheduler import TaskScheduler
    from openjarvis.scheduler.store import SchedulerStore
    from openjarvis.security.audit import AuditLogger
    from openjarvis.security.boundary import BoundaryGuard
    from openjarvis.security.capabilities import CapabilityPolicy
    from openjarvis.telemetry.gpu_monitor import GpuMonitor
    from openjarvis.telemetry.store import TelemetryStore
    from openjarvis.traces.collector import TraceCollector
    from openjarvis.traces.store import TraceStore


@dataclass
class SecurityContext:
    """Security policy, audit, and boundary enforcement."""

    capability_policy: CapabilityPolicy | None = None
    audit_logger: AuditLogger | None = None
    boundary_guard: BoundaryGuard | None = None


@dataclass
class Observability:
    """Telemetry, traces, and hardware monitoring."""

    telemetry_store: TelemetryStore | None = None
    trace_store: TraceStore | None = None
    trace_collector: TraceCollector | None = None
    gpu_monitor: GpuMonitor | None = None


@dataclass
class AgentRuntime:
    """Active agent and agent lifecycle managers."""

    agent: BaseAgent | None = None
    agent_name: str = ""
    manager: AgentManager | None = None
    scheduler: AgentScheduler | None = None
    executor: AgentExecutor | None = None


@dataclass
class Scheduling:
    """Task scheduler and its persistent store."""

    store: SchedulerStore | None = None
    runner: TaskScheduler | None = None
