"""
BaseEngine — Abstract interface contract for all pipeline engines.
=================================================================

Every engine must subclass BaseEngine and implement:
    - name:     Unique string identifier (e.g., "engine_1")
    - requires: List of bus keys the engine reads from
    - produces: Bus key the engine writes to
    - run():    Core logic — receives full bus context, returns dict for its key

The orchestrator uses `requires` and `produces` to resolve execution order
automatically via topological sort. Engines never import or call each other.
"""

from abc import ABC, abstractmethod


class BaseEngine(ABC):
    """Abstract base class that all pipeline engines must implement."""

    name: str
    requires: list[str]
    produces: str

    @abstractmethod
    def run(self, context: dict) -> dict:
        """Execute engine logic.

        Reads from context (the shared data bus), returns a dict that
        the orchestrator will write to context[self.produces].

        Args:
            context: The shared data bus dictionary.

        Returns:
            A dict matching the schema for self.produces bus key.
        """
        raise NotImplementedError
