"""OpenJarvis — modular AI assistant backend with composable intelligence primitives."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    __version__ = _pkg_version("openjarvis")
except PackageNotFoundError:  # pragma: no cover — uninstalled source tree
    __version__ = "0.0.0+unknown"

__all__ = ["Jarvis", "JarvisSystem", "MemoryHandle", "SystemBuilder", "__version__"]

# Public SDK names are resolved lazily (PEP 562) so that ``import openjarvis``
# stays cheap — importing ``openjarvis.sdk`` eagerly pulls in the engine stack
# (openai SDK, httpx) and costs ~200ms on every CLI/script startup.
_SDK_EXPORTS = ("Jarvis", "JarvisSystem", "MemoryHandle", "SystemBuilder")


def __getattr__(name: str):
    """Lazily import SDK symbols on first attribute access."""
    if name in _SDK_EXPORTS:
        from openjarvis.sdk import (
            Jarvis,
            JarvisSystem,
            MemoryHandle,
            SystemBuilder,
        )

        _exports = {
            "Jarvis": Jarvis,
            "JarvisSystem": JarvisSystem,
            "MemoryHandle": MemoryHandle,
            "SystemBuilder": SystemBuilder,
        }
        return _exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
