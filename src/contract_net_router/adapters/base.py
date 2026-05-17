"""Shared adapter primitives for framework-specific Contract Net bindings."""
from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import Dict, Iterable


class BaseCNPAdapter(ABC):
    """Common bid/award/audit interface for framework adapters."""

    framework_name = "framework"

    def __init__(
        self,
        agent_id: str,
        capability_keywords: Iterable[str] | None = None,
        estimated_cost: float = 1.0,
    ) -> None:
        self.agent_id = agent_id
        self.capability_keywords = [kw.lower() for kw in (capability_keywords or [])]
        self.estimated_cost = float(estimated_cost)
        self._audits: Dict[str, Dict] = {}

    def _task_text(self, task: dict) -> str:
        values = [
            str(task.get("task", "")),
            str(task.get("description", "")),
            " ".join(str(item) for item in task.get("keywords", [])),
            " ".join(str(item) for item in task.get("requirements", [])),
        ]
        return " ".join(values).strip().lower()

    def _task_id(self, task: dict) -> str:
        return str(task.get("task_id") or task.get("id") or f"{self.framework_name}-task")

    def _score_task(self, task: dict) -> float:
        if not self.capability_keywords:
            return 0.5
        tokens = set(re.findall(r"[a-z0-9_+-]+", self._task_text(task)))
        overlap = sum(1 for keyword in self.capability_keywords if keyword in tokens)
        if overlap == 0:
            return 0.0
        return min(1.0, overlap / len(self.capability_keywords))

    @abstractmethod
    def bid(self, task: dict) -> dict:
        """Return bid: {agent_id, capability_score, estimated_cost}."""

    @abstractmethod
    def award(self, task: dict, bid: dict) -> bool:
        """Accept awarded task. Return True on success."""

    @abstractmethod
    def audit(self, task_id: str) -> dict:
        """Return audit record: {task_id, status, timestamps, agent_id}."""


class InMemoryCNPAdapter(BaseCNPAdapter):
    """Minimal fully-functional adapter backed by an in-memory audit log."""

    def bid(self, task: dict) -> dict:
        return {
            "agent_id": self.agent_id,
            "capability_score": self._score_task(task),
            "estimated_cost": self.estimated_cost,
        }

    def award(self, task: dict, bid: dict) -> bool:
        if bid.get("agent_id") != self.agent_id:
            return False
        awarded_at = time.time()
        self._audits[self._task_id(task)] = {
            "task_id": self._task_id(task),
            "status": "awarded",
            "timestamps": {"awarded_at": awarded_at},
            "agent_id": self.agent_id,
        }
        return True

    def audit(self, task_id: str) -> dict:
        return self._audits.get(
            task_id,
            {
                "task_id": task_id,
                "status": "unknown",
                "timestamps": {},
                "agent_id": self.agent_id,
            },
        )


class StubFrameworkAdapter(BaseCNPAdapter):
    """Placeholder adapter for frameworks without a concrete integration yet."""

    def _unsupported(self) -> None:
        raise NotImplementedError(
            f"{self.framework_name} adapter is currently a stub. "
            "Implement framework-specific bid/award/audit wiring before use."
        )

    def bid(self, task: dict) -> dict:
        self._unsupported()

    def award(self, task: dict, bid: dict) -> bool:
        self._unsupported()

    def audit(self, task_id: str) -> dict:
        self._unsupported()
