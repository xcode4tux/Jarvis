"""JarvisSystem — the fully wired system dataclass."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from openjarvis.core.config import JarvisConfig
from openjarvis.core.events import EventBus
from openjarvis.core.types import Message, Role
from openjarvis.engine._stubs import InferenceEngine
from openjarvis.system.bundles import (
    AgentRuntime,
    Observability,
    Scheduling,
    SecurityContext,
)
from openjarvis.tools._stubs import BaseTool, ToolExecutor

if TYPE_CHECKING:
    from openjarvis.agents._stubs import BaseAgent
    from openjarvis.agents.executor import AgentExecutor
    from openjarvis.agents.manager import AgentManager
    from openjarvis.agents.scheduler import AgentScheduler
    from openjarvis.channels._stubs import BaseChannel
    from openjarvis.learning._stubs import RouterPolicy
    from openjarvis.learning.learning_orchestrator import LearningOrchestrator
    from openjarvis.mcp.client import MCPClient
    from openjarvis.mcp.server import MCPServer
    from openjarvis.operators.manager import OperatorManager
    from openjarvis.sandbox.runner import ContainerRunner
    from openjarvis.scheduler.scheduler import TaskScheduler
    from openjarvis.scheduler.store import SchedulerStore
    from openjarvis.security.audit import AuditLogger
    from openjarvis.security.boundary import BoundaryGuard
    from openjarvis.security.capabilities import CapabilityPolicy
    from openjarvis.sessions.session import SessionStore
    from openjarvis.skills.manager import SkillManager
    from openjarvis.speech._stubs import SpeechBackend
    from openjarvis.system.orchestrator import QueryOrchestrator
    from openjarvis.telemetry.gpu_monitor import GpuMonitor
    from openjarvis.telemetry.store import TelemetryStore
    from openjarvis.tools.storage._stubs import MemoryBackend
    from openjarvis.traces.collector import TraceCollector
    from openjarvis.traces.store import TraceStore
    from openjarvis.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)


@dataclass
class JarvisSystem:
    """Fully wired system -- the single source of truth for primitive composition."""

    config: JarvisConfig
    bus: EventBus
    engine: InferenceEngine
    engine_key: str
    model: str
    agent: BaseAgent | None = None
    agent_name: str = ""
    tools: list[BaseTool] = field(default_factory=list)
    tool_executor: ToolExecutor | None = None
    memory_backend: MemoryBackend | None = None
    channel_backend: BaseChannel | None = None
    router: RouterPolicy | None = None
    mcp_server: MCPServer | None = None
    telemetry_store: TelemetryStore | None = None
    trace_store: TraceStore | None = None
    trace_collector: TraceCollector | None = None
    gpu_monitor: GpuMonitor | None = None
    scheduler_store: SchedulerStore | None = None
    scheduler: TaskScheduler | None = None
    container_runner: ContainerRunner | None = None
    workflow_engine: WorkflowEngine | None = None
    session_store: SessionStore | None = None
    capability_policy: CapabilityPolicy | None = None
    audit_logger: AuditLogger | None = None
    boundary_guard: BoundaryGuard | None = None
    operator_manager: OperatorManager | None = None
    agent_manager: AgentManager | None = None
    agent_scheduler: AgentScheduler | None = None
    agent_executor: AgentExecutor | None = None
    speech_backend: SpeechBackend | None = None
    skill_manager: SkillManager | None = None
    _learning_orchestrator: LearningOrchestrator | None = None
    _mcp_clients: list[MCPClient] = field(default_factory=list)

    @property
    def security(self) -> SecurityContext:
        return SecurityContext(
            capability_policy=self.capability_policy,
            audit_logger=self.audit_logger,
            boundary_guard=self.boundary_guard,
        )

    @property
    def observability(self) -> Observability:
        return Observability(
            telemetry_store=self.telemetry_store,
            trace_store=self.trace_store,
            trace_collector=self.trace_collector,
            gpu_monitor=self.gpu_monitor,
        )

    @property
    def agents(self) -> AgentRuntime:
        return AgentRuntime(
            agent=self.agent,
            agent_name=self.agent_name,
            manager=self.agent_manager,
            scheduler=self.agent_scheduler,
            executor=self.agent_executor,
        )

    @property
    def scheduling(self) -> Scheduling:
        return Scheduling(
            store=self.scheduler_store,
            runner=self.scheduler,
        )

    def _get_orchestrator(self) -> QueryOrchestrator:
        orch = self.__dict__.get("_orchestrator")
        if orch is None:
            from openjarvis.system.orchestrator import QueryOrchestrator

            orch = QueryOrchestrator(self)
            self.__dict__["_orchestrator"] = orch
        return orch

    def ask(
        self,
        query: str,
        *,
        context: bool = True,
        temperature: float | None = None,
        max_tokens: int | None = None,
        agent: str | None = None,
        tools: list[str] | None = None,
        system_prompt: str | None = None,
        operator_id: str | None = None,
        prior_messages: list[Message] | None = None,
    ) -> dict[str, Any]:
        return self._get_orchestrator().ask(
            query,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
            agent=agent,
            tools=tools,
            system_prompt=system_prompt,
            operator_id=operator_id,
            prior_messages=prior_messages,
        )

    def _detect_agent_intent(self, query: str) -> str | None:
        return self._get_orchestrator()._detect_agent_intent(query)

    def _build_tools(self, tool_names: list[str]) -> list[BaseTool]:
        return self._get_orchestrator()._build_tools(tool_names)

    def _run_agent(
        self,
        query,
        messages,
        agent_name,
        tool_names,
        temperature,
        max_tokens,
        *,
        system_prompt=None,
        operator_id=None,
        prior_messages=None,
    ) -> dict[str, Any]:
        return self._get_orchestrator()._run_agent(
            query,
            messages,
            agent_name,
            tool_names,
            temperature,
            max_tokens,
            system_prompt=system_prompt,
            operator_id=operator_id,
            prior_messages=prior_messages,
        )

    def wire_channel(self, channel_bridge: Any) -> None:
        """Register a message handler on *channel_bridge* that routes every
        incoming message through this system (agent or engine) and replies.

        Sessions are isolated per ``"<channel>:<conversation_id>"`` key so
        each chat retains its own history.

        Parameters
        ----------
        channel_bridge:
            A connected :class:`~openjarvis.channels._stubs.BaseChannel`
            instance whose ``on_message`` method accepts a callable.
        """
        from openjarvis.core.types import Message
        from openjarvis.sessions.session import SessionStore

        if self.session_store is None:
            from pathlib import Path

            self.session_store = SessionStore(
                db_path=Path(self.config.sessions.db_path).expanduser(),
                max_age_hours=self.config.sessions.max_age_hours,
                consolidation_threshold=self.config.sessions.consolidation_threshold,
            )

        _system = self  # capture for closure

        def _on_channel_message(cm) -> None:
            session_key = f"{cm.channel}:{cm.conversation_id}"
            session = _system.session_store.get_or_create(
                session_key,
                channel=cm.channel,
                channel_user_id=cm.sender,
            )

            prior_msgs: list[Message] = []
            for sm in session.messages:
                try:
                    role = Role(sm.role)
                except ValueError:
                    role = Role.USER
                prior_msgs.append(Message(role=role, content=sm.content))

            reply = ""
            try:
                if _system.agent_name and _system.agent_name != "none":
                    result = _system.ask(
                        cm.content,
                        context=False,
                        agent=_system.agent_name,
                        prior_messages=prior_msgs,
                    )
                    reply = result.get("content", "")
                else:
                    result = _system.ask(
                        cm.content,
                        context=False,
                        prior_messages=prior_msgs,
                    )
                    reply = result.get("content", "")
            except Exception:
                logger.exception("Channel message handler error")
                reply = "Sorry, I encountered an error processing your message."

            try:
                _system.session_store.save_message(
                    session.session_id,
                    "user",
                    cm.content,
                    channel=cm.channel,
                )
                _system.session_store.save_message(
                    session.session_id,
                    "assistant",
                    reply,
                    channel=cm.channel,
                )
            except Exception:
                logger.debug("Session save error", exc_info=True)

            if reply:
                try:
                    channel_bridge.send(
                        cm.channel,
                        reply,
                        conversation_id=cm.conversation_id,
                    )
                except Exception:
                    logger.exception("Channel send error")

        channel_bridge.on_message(_on_channel_message)

    def _close_mcp_clients(self) -> None:
        """Close all persistent MCP client connections."""
        for client in self._mcp_clients:
            try:
                client.close()
            except Exception:
                logger.debug("Error closing MCP client", exc_info=True)

    def close(self) -> None:
        """Release resources."""
        if self.scheduler and hasattr(self.scheduler, "stop"):
            self.scheduler.stop()
        for resource in (
            self.scheduler_store,
            self.engine,
            self.gpu_monitor,
            self.telemetry_store,
            self.trace_store,
            self.memory_backend,
            self.session_store,
            self.channel_backend,
            self.workflow_engine,
            self.container_runner,
        ):
            if resource and hasattr(resource, "close"):
                resource.close()
        if self.agent_manager is not None:
            self.agent_manager.close()
        if self.agent_scheduler is not None:
            self.agent_scheduler.stop()
        self._close_mcp_clients()

    def __enter__(self) -> JarvisSystem:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


__all__ = ["JarvisSystem"]
