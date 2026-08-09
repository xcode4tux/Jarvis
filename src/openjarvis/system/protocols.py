"""Structural protocols for substituting fakes in place of JarvisSystem."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from openjarvis.core.config import JarvisConfig
    from openjarvis.core.events import EventBus
    from openjarvis.engine._stubs import InferenceEngine
    from openjarvis.security.capabilities import CapabilityPolicy
    from openjarvis.sessions.session import SessionStore
    from openjarvis.tools._stubs import BaseTool
    from openjarvis.tools.storage._stubs import MemoryBackend
    from openjarvis.traces.collector import TraceCollector
    from openjarvis.traces.store import TraceStore


class OrchestratorDeps(Protocol):
    """Minimum surface of JarvisSystem that QueryOrchestrator depends on.

    Tests can satisfy this with a lightweight class — no need to construct
    the full JarvisSystem dataclass or materialize every subsystem.
    """

    config: JarvisConfig
    bus: EventBus
    engine: InferenceEngine
    engine_key: str
    model: str
    agent_name: str
    tools: list[BaseTool]
    memory_backend: MemoryBackend | None
    capability_policy: CapabilityPolicy | None
    session_store: SessionStore | None
    trace_store: TraceStore | None
    trace_collector: TraceCollector | None  # written by _run_agent

    # Optional attribute (getattr with default) — declared for type clarity.
    _skill_few_shot_examples: Any
