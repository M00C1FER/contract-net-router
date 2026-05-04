"""CI quality level tracking (Green Contract).

Inspired by claw-code's green_contract.rs — tracks whether test suites pass
at various levels and feeds into SIGMA verification gates.
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", str(Path(__file__).resolve().parents[3])))


class GreenLevel(IntEnum):
    """Ordinal quality levels — higher is stricter."""

    NONE = 0
    TARGETED = 1   # Specific tests pass
    PACKAGE = 2    # Package-level tests pass
    WORKSPACE = 3  # Full workspace tests pass
    MERGE_READY = 4  # All tests + lint + type-check pass


@dataclass
class GreenContractOutcome:
    """Result of evaluating a green contract."""

    satisfied: bool
    required_level: GreenLevel
    observed_level: GreenLevel
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "satisfied": self.satisfied,
            "required_level": self.required_level.name,
            "observed_level": self.observed_level.name,
            "details": self.details,
        }


@dataclass
class GreenContract:
    """Defines a required quality level and evaluates against observed state."""

    required_level: GreenLevel = GreenLevel.WORKSPACE

    def evaluate(self, observed: Optional[GreenLevel]) -> GreenContractOutcome:
        if observed is None:
            return GreenContractOutcome(
                satisfied=False,
                required_level=self.required_level,
                observed_level=GreenLevel.NONE,
                details="No test results available",
            )
        return GreenContractOutcome(
            satisfied=observed >= self.required_level,
            required_level=self.required_level,
            observed_level=observed,
            details="" if observed >= self.required_level
            else f"Observed {observed.name} < required {self.required_level.name}",
        )

    def is_satisfied_by(self, observed: GreenLevel) -> bool:
        return observed >= self.required_level


def run_test_suite(
    test_dir: Optional[Path] = None,
    pattern: str = "test_*.py",
    timeout: int = 120,
) -> GreenLevel:
    """Run pytest and return the achieved green level."""
    test_dir = test_dir or (PROJECT_ROOT / "tests")
    if not test_dir.exists():
        logger.warning("Test directory not found: %s", test_dir)
        return GreenLevel.NONE

    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", str(test_dir), "-q", "--tb=no", "-x"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            return GreenLevel.WORKSPACE
        # Partial pass — at least some tests ran
        if "passed" in result.stdout:
            return GreenLevel.TARGETED
        return GreenLevel.NONE
    except subprocess.TimeoutExpired:
        logger.warning("Test suite timed out after %ds", timeout)
        return GreenLevel.NONE
    except FileNotFoundError:
        logger.warning("pytest not found")
        return GreenLevel.NONE


@dataclass
class GreenContractRegistry:
    """Tracks green contract history for trend analysis."""

    history: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, outcome: GreenContractOutcome, context: str = "") -> None:
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "satisfied": outcome.satisfied,
            "required": outcome.required_level.name,
            "observed": outcome.observed_level.name,
            "context": context,
        })

    @property
    def pass_rate(self) -> float:
        if not self.history:
            return 0.0
        return sum(1 for h in self.history if h["satisfied"]) / len(self.history)

    @property
    def latest(self) -> Optional[Dict[str, Any]]:
        return self.history[-1] if self.history else None
