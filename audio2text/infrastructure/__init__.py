"""
Audio2Text infrastructure layer.

Single import site for cenf_core. Business modules MUST depend on
Protocols exposed here, never on cenf_core adapters directly.
"""

from audio2text.infrastructure.bootstrap import bootstrap
from audio2text.infrastructure.registry import ManagerRegistry

__all__ = ["bootstrap", "get_registry", "ManagerRegistry"]

_registry: ManagerRegistry | None = None


def get_registry() -> ManagerRegistry:
    """Return the global registry, bootstrapping on first call if needed."""
    global _registry
    if _registry is None:
        _registry = bootstrap({})
    return _registry
