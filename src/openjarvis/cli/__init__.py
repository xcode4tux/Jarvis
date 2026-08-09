"""Command-line interface for OpenJarvis (Click-based)."""

from __future__ import annotations

import importlib
import logging

import click

import openjarvis

logger = logging.getLogger(__name__)

# Command registry: ``name -> (module, attribute)``. Modules are imported
# lazily on first invocation so that ``jarvis --help`` and lightweight
# commands (config, doctor, self-update) don't pay the cost of the full
# engine/agent stack — the openai SDK alone costs ~1.3s to import.
_COMMANDS: dict[str, tuple[str, str]] = {
    "init": ("openjarvis.cli.init_cmd", "init"),
    "ask": ("openjarvis.cli.ask", "ask"),
    "chat": ("openjarvis.cli.chat_cmd", "chat"),
    "serve": ("openjarvis.cli.serve", "serve"),
    "model": ("openjarvis.cli.model", "model"),
    "memory": ("openjarvis.cli.memory_cmd", "memory"),
    "mine": ("openjarvis.cli.mine_cmd", "mine"),
    "pearl": ("openjarvis.cli.pearl_cmd", "pearl"),
    "telemetry": ("openjarvis.cli.telemetry_cmd", "telemetry"),
    "bench": ("openjarvis.cli.bench_cmd", "bench"),
    "channel": ("openjarvis.cli.channel_cmd", "channel"),
    "channels": ("openjarvis.cli.channels_cmd", "channels"),
    "scheduler": ("openjarvis.cli.scheduler_cmd", "scheduler"),
    "doctor": ("openjarvis.cli.doctor_cmd", "doctor"),
    "agents": ("openjarvis.cli.agent_cmd", "agent"),
    "workflow": ("openjarvis.cli.workflow_cmd", "workflow"),
    "skill": ("openjarvis.cli.skill_cmd", "skill"),
    "start": ("openjarvis.cli.daemon_cmd", "start"),
    "stop": ("openjarvis.cli.daemon_cmd", "stop"),
    "restart": ("openjarvis.cli.daemon_cmd", "restart"),
    "status": ("openjarvis.cli.daemon_cmd", "status"),
    "vault": ("openjarvis.cli.vault_cmd", "vault"),
    "add": ("openjarvis.cli.add_cmd", "add"),
    "operators": ("openjarvis.cli.operators_cmd", "operators"),
    "eval": ("openjarvis.cli.eval_cmd", "eval_group"),
    "host": ("openjarvis.cli.host_cmd", "host"),
    "quickstart": ("openjarvis.cli.quickstart_cmd", "quickstart"),
    "optimize": ("openjarvis.cli.optimize_cmd", "optimize_group"),
    "feedback": ("openjarvis.cli.feedback_cmd", "feedback_group"),
    "compose": ("openjarvis.cli.compose_cmd", "compose"),
    "gateway": ("openjarvis.cli.gateway_cmd", "gateway"),
    "tool": ("openjarvis.cli.tool_cmd", "tool"),
    "registry": ("openjarvis.cli.registry_cmd", "registry"),
    "config": ("openjarvis.cli.config_cmd", "config"),
    "scan": ("openjarvis.cli.scan_cmd", "scan"),
    "connect": ("openjarvis.cli.connect_cmd", "connect"),
    "digest": ("openjarvis.cli.digest_cmd", "digest"),
    "deep-research-setup": (
        "openjarvis.cli.deep_research_setup_cmd",
        "deep_research_setup",
    ),
    "research": ("openjarvis.cli.deep_research_setup_cmd", "deep_research_setup"),
    "self-update": ("openjarvis.cli.self_update_cmd", "self_update"),
    "_bootstrap": ("openjarvis.cli._bootstrap", "bootstrap_cmd"),
    "auth": ("openjarvis.cli.auth_cmd", "auth"),
    "tunnel": ("openjarvis.cli.tunnel_cmd", "tunnel"),
}


class _LazyGroup(click.Group):
    """Click group that imports command modules on first use.

    Defers the openai/httpx/rich stack until a command that actually needs
    it is invoked, keeping ``jarvis --help`` and lightweight commands fast.
    A command that fails to import (missing platform deps, broken numpy on
    Windows) is skipped instead of taking down the whole CLI.
    """

    def list_commands(self, ctx) -> list[str]:  # noqa: ARG002
        return sorted(_COMMANDS)

    def get_command(self, ctx, cmd_name):  # noqa: ARG002
        if cmd_name not in _COMMANDS:
            return None
        mod_name, attr = _COMMANDS[cmd_name]
        try:
            mod = importlib.import_module(mod_name)
            cmd = getattr(mod, attr)
        except Exception as exc:  # noqa: BLE001 — optional command, never fatal
            logger.debug(
                "Command %r unavailable (%s): %s",
                cmd_name,
                type(exc).__name__,
                exc,
            )
            return None
        self.add_command(cmd, cmd_name)
        return cmd


@click.group(
    cls=_LazyGroup,
    help="OpenJarvis — modular AI assistant backend",
    invoke_without_command=True,
)
@click.version_option(version=openjarvis.__version__, prog_name="jarvis")
@click.option("--verbose", is_flag=True, default=False, help="Enable debug logging")
@click.option("--quiet", is_flag=True, default=False, help="Suppress non-error output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """Top-level CLI group."""
    from openjarvis.cli.log_config import setup_logging

    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    setup_logging(verbose=verbose, quiet=quiet)

    # Check for updates on interactive commands. The banner is noise in
    # demo recordings of ``jarvis ask --research``, so skip it whenever
    # the research flag is in argv (cheap argv sniff — Click hasn't
    # parsed the subcommand's args yet at this point).
    import sys

    research_mode_active = "--research" in sys.argv
    if not quiet and ctx.invoked_subcommand and not research_mode_active:
        import threading

        from openjarvis.cli._version_check import check_for_updates

        # Run the PyPI version poll off the hot path: on a cache miss it does
        # a blocking urlopen (up to 3s) that otherwise delays every command,
        # notably `jarvis serve` startup (#263). It's best-effort and never
        # raises, and the nudge prints to stderr, so a daemon thread is safe —
        # for long-lived commands (serve) it finishes; for short commands that
        # exit first, the check is simply skipped this run (same as a miss).
        threading.Thread(
            target=check_for_updates,
            args=(ctx.invoked_subcommand,),
            daemon=True,
        ).start()

    # First-run guard — routes bare `jarvis` to chat or init.
    if ctx.invoked_subcommand is None:
        from openjarvis.cli._first_run import check_and_route

        check_and_route(ctx)


def main() -> None:
    """Entry point registered as ``jarvis`` console script."""
    import sys

    if sys.platform == "win32":
        for _stream in (sys.stdout, sys.stderr):
            if hasattr(_stream, "reconfigure"):
                try:
                    _stream.reconfigure(encoding="utf-8", errors="replace")
                except (AttributeError, OSError):
                    pass
    cli()


__all__ = ["cli", "main"]
