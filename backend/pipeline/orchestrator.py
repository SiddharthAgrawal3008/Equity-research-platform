"""
Pipeline Orchestrator — Stage resolution and parallel execution.
================================================================

Resolves the dependency graph from engine declarations, groups engines
into sequential stages, and executes them. Within a stage, engines run
in parallel via ThreadPoolExecutor. Between stages, all engines must
complete before the next stage begins.

Stage resolution uses topological sorting:
    Stage 1: E1 (requires ticker)         — sequential
    Stage 2: E2, E3, E4 (require E1 data) — parallel
    Stage 3: E5 (requires all)            — sequential
"""

import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.pipeline.base_engine import BaseEngine
from backend.pipeline.context import create_context

logger = logging.getLogger(__name__)


class CyclicDependencyError(Exception):
    """Raised when engine dependencies cannot be resolved."""


def resolve_stages(
    engines: list[BaseEngine],
    initial_keys: set[str] | None = None,
) -> list[list[BaseEngine]]:
    """Group engines into sequential stages via topological sort.

    Engines whose `requires` are fully satisfied by available keys
    are grouped into the same stage and can run in parallel.

    Args:
        engines:      List of engine instances to schedule.
        initial_keys: Keys available before any engine runs (default: {"ticker"}).

    Returns:
        A list of stages, where each stage is a list of engines.

    Raises:
        CyclicDependencyError: If dependencies cannot be resolved.
    """
    if initial_keys is None:
        initial_keys = {"ticker"}

    available = set(initial_keys)
    remaining = list(engines)
    stages: list[list[BaseEngine]] = []

    while remaining:
        stage = [e for e in remaining if all(r in available for r in e.requires)]

        if not stage:
            unresolved = [e.name for e in remaining]
            raise CyclicDependencyError(
                f"Cannot resolve dependencies for: {unresolved}. "
                f"Available keys: {available}"
            )

        stages.append(stage)
        for engine in stage:
            available.add(engine.produces)
            remaining.remove(engine)

    return stages


def _safe_run(engine: BaseEngine, context: dict) -> None:
    """Execute a single engine with error capture.

    On success: writes result to context[engine.produces], sets status to "success".
    On failure: sets status to "failed", appends error details to context["errors"].

    Args:
        engine:  The engine instance to run.
        context: The shared data bus.
    """
    try:
        context["status"][engine.name] = "running"
        result = engine.run(context)
        context[engine.produces] = result
        context["status"][engine.name] = "success"
        logger.info(f"Engine {engine.name} completed successfully")
    except Exception as exc:
        context["status"][engine.name] = "failed"
        context["errors"].append({
            "engine": engine.name,
            "error": str(exc),
            "type": type(exc).__name__,
        })
        logger.error(f"Engine {engine.name} failed: {exc}")


def _run_stage(engines: list[BaseEngine], context: dict) -> None:
    """Execute all engines in a stage.

    Single engine: runs directly (no thread overhead).
    Multiple engines: runs in parallel via ThreadPoolExecutor.

    Args:
        engines: The engines in this stage.
        context: The shared data bus.
    """
    if len(engines) == 1:
        _safe_run(engines[0], context)
    else:
        with ThreadPoolExecutor(max_workers=len(engines)) as pool:
            futures = {
                pool.submit(_safe_run, engine, context): engine
                for engine in engines
            }
            for future in as_completed(futures):
                # Re-raise any unexpected executor-level errors
                future.result()


def run_pipeline(ticker: str, engines: list[BaseEngine]) -> dict:
    """Execute the full equity research pipeline.

    Creates a fresh context, resolves stages, and runs each stage
    sequentially. Within each stage, engines run in parallel.

    Special handling:
        - If Engine 1 (financial_data) fails, the pipeline halts
          immediately since all downstream engines depend on it.

    Args:
        ticker:  Stock ticker to analyze (e.g., "AAPL").
        engines: List of engine instances to run.

    Returns:
        The complete context dict (data bus) after pipeline execution.
    """
    context = create_context(ticker)
    context["metadata"]["started_at"] = (
        datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    stages = resolve_stages(engines)

    for stage_num, stage in enumerate(stages, start=1):
        # E1 failure is fatal — halt if financial_data was never produced
        if stage_num > 1 and context["status"].get("engine_1") == "failed":
            logger.error(
                "Engine 1 (financial_data) failed — halting pipeline. "
                "No downstream engines can run without financial data."
            )
            break

        logger.info(
            f"Stage {stage_num}: running {[e.name for e in stage]}"
        )
        _run_stage(stage, context)
        context["metadata"]["stages_completed"].append(stage_num)

    context["metadata"]["completed_at"] = (
        datetime.datetime.now(datetime.timezone.utc).isoformat()
    )

    return context
