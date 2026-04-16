"""
Base engine interface for the Equity Research Platform pipeline.

All engines inherit from BaseEngine and implement the run() method.
The orchestrator uses `requires` and `produces` to resolve execution order.
"""

from abc import ABC, abstractmethod


class BaseEngine(ABC):
    name: str = ""
    requires: list[str] = []
    produces: str = ""

    @abstractmethod
    def run(self, context: dict) -> dict:
        """Execute the engine logic.

        Args:
            context: Shared data bus dict. Read keys listed in `requires`,
                     return a dict that the orchestrator writes to
                     `context[self.produces]`.

        Returns:
            Dict to be stored under this engine's `produces` key.
        """
        raise NotImplementedError
