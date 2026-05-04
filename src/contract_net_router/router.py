"""
Contract Net Router — MOSA-compliant multi-agent task routing.

Implements the Contract Net Protocol (CNP, Smith 1980) as a Python library.
Agents advertise capabilities; the router scores all registered agents against
a task description and selects the best match via keyword + semantic scoring.

Architecture (MOSA):
  AgentCapability  — advertised skills, tier, keywords, autonomy level
  RouteResult      — routing decision with scores and rationale
  ContractNetRouter — the broker (bid, award, dispatch abstraction)

No external dependencies required for basic routing.
Optional: install sentence-transformers for semantic scoring.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger("contract_net_router")

# ── Agent tier ────────────────────────────────────────────────────────────────

class AgentTier(str, Enum):
    """Priority tier for agent selection ordering."""
    STRATEGIC = "strategic"   # Deep reasoning, architecture
    TACTICAL  = "tactical"    # Code generation, data, domain experts
    RAPID     = "rapid"       # Triage, classification, quick lookups
    COMMAND   = "command"     # Orchestrators (highest priority)


# ── Data types ────────────────────────────────────────────────────────────────

@dataclass
class AgentCapability:
    """
    Capability advertisement broadcast by an agent.

    Args:
        name:        unique agent identifier
        tier:        routing priority tier
        specialties: free-text list of domains this agent handles
        keywords:    token list used for keyword-overlap scoring
        autonomy:    "autonomous" | "supervised" | "restricted"
        deny_tools:  list of tool names this agent must NOT use
        metadata:    arbitrary extra info for downstream systems
    """
    name: str
    tier: str = AgentTier.TACTICAL.value
    specialties: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    autonomy: str = "supervised"
    deny_tools: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class RouteResult:
    """Routing decision returned by ContractNetRouter.route()."""
    winning_agent: Optional[str]
    score: float                          # 0.0–1.0
    runner_up: Optional[str] = None
    runner_up_score: float = 0.0
    rationale: str = ""
    all_bids: Dict[str, float] = field(default_factory=dict)


# ── Router ────────────────────────────────────────────────────────────────────

class ContractNetRouter:
    """
    Contract Net Protocol broker.

    1. Agents call ``register()`` to advertise their capabilities.
    2. When a task arrives, ``route(task)`` solicits bids from all agents.
    3. Bids are scored by keyword overlap + tier weight.
    4. The highest-scoring agent is awarded the task.

    Optional semantic scoring (requires ``sentence-transformers``):
        router = ContractNetRouter(use_semantic=True)
    """

    # Tier weight boosts applied to the base keyword score
    _TIER_WEIGHTS: Dict[str, float] = {
        AgentTier.COMMAND.value:   1.30,
        AgentTier.STRATEGIC.value: 1.15,
        AgentTier.TACTICAL.value:  1.00,
        AgentTier.RAPID.value:     0.80,
    }

    def __init__(self, use_semantic: bool = False) -> None:
        self._agents: Dict[str, AgentCapability] = {}
        self._use_semantic = use_semantic
        self._embedder = None
        if use_semantic:
            self._embedder = self._load_embedder()

    # ── Registry ──────────────────────────────────────────────────────────────

    def register(self, cap: AgentCapability) -> None:
        """Register (or update) an agent capability."""
        self._agents[cap.name] = cap
        logger.debug("Registered agent '%s' tier=%s keywords=%d",
                     cap.name, cap.tier, len(cap.keywords))

    def unregister(self, name: str) -> bool:
        """Remove an agent from the registry. Returns True if found."""
        return self._agents.pop(name, None) is not None

    def list_agents(self) -> List[AgentCapability]:
        """Return a copy of all registered agents."""
        return list(self._agents.values())

    # ── Routing ───────────────────────────────────────────────────────────────

    def route(self, task: str) -> RouteResult:
        """
        Select the best agent for ``task``.

        Returns:
            RouteResult with winning_agent (None if no agents registered)
            and score in [0.0, 1.0].
        """
        if not self._agents:
            return RouteResult(winning_agent=None, score=0.0,
                               rationale="No agents registered")

        task_tokens = _tokenize(task)
        bids: Dict[str, float] = {}

        for name, cap in self._agents.items():
            bids[name] = self._bid(task, task_tokens, cap)

        # Sort descending by score; break ties by agent name for determinism.
        sorted_bids = sorted(bids.items(), key=lambda x: (-x[1], x[0]))
        winner, win_score = sorted_bids[0]
        runner_up = sorted_bids[1][0] if len(sorted_bids) > 1 else None
        runner_score = sorted_bids[1][1] if len(sorted_bids) > 1 else 0.0

        # No agent matched the task — all scores are zero.
        if win_score == 0.0:
            return RouteResult(
                winning_agent=None,
                score=0.0,
                runner_up=None,
                runner_up_score=0.0,
                rationale="No agent matched the task (all bids were zero)",
                all_bids={n: round(s, 4) for n, s in bids.items()},
            )

        rationale = self._explain(winner, self._agents[winner], task_tokens,
                                  win_score)
        return RouteResult(
            winning_agent=winner,
            score=round(win_score, 4),
            runner_up=runner_up,
            runner_up_score=round(runner_score, 4),
            rationale=rationale,
            all_bids={n: round(s, 4) for n, s in bids.items()},
        )

    def query_capable(self, task: str, top_k: int = 3) -> List[RouteResult]:
        """
        Return the top-k agents for a task as a ranked list.
        """
        if not self._agents:
            return []
        task_tokens = _tokenize(task)
        scored = sorted(
            [(name, self._bid(task, task_tokens, cap))
             for name, cap in self._agents.items()],
            key=lambda x: x[1], reverse=True,
        )
        results = []
        all_bids = {n: round(s, 4) for n, s in scored}
        for name, score in scored[:top_k]:
            results.append(RouteResult(
                winning_agent=name,
                score=round(score, 4),
                rationale=self._explain(name, self._agents[name],
                                        task_tokens, score),
                all_bids=all_bids,
            ))
        return results

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _bid(self, task: str, task_tokens: List[str],
             cap: AgentCapability) -> float:
        """Compute a bid score for one agent."""
        keyword_score = self._keyword_overlap(task_tokens, cap)
        specialty_score = self._specialty_overlap(task, cap)
        tier_weight = self._TIER_WEIGHTS.get(cap.tier, 1.0)

        base = 0.6 * keyword_score + 0.4 * specialty_score
        score = min(1.0, base * tier_weight)

        if self._use_semantic and self._embedder is not None:
            sem = self._semantic_score(task, cap)
            score = 0.5 * score + 0.5 * sem

        return score

    def _keyword_overlap(self, task_tokens: List[str],
                          cap: AgentCapability) -> float:
        """Jaccard-inspired keyword overlap."""
        if not cap.keywords:
            return 0.0
        kw = {k.lower() for k in cap.keywords}
        matches = sum(1 for t in task_tokens if t in kw)
        return matches / math.sqrt(len(kw)) if kw else 0.0

    def _specialty_overlap(self, task: str, cap: AgentCapability) -> float:
        """Substring match of specialties in the task description."""
        if not cap.specialties:
            return 0.0
        task_lower = task.lower()
        hits = sum(1 for s in cap.specialties if s.lower() in task_lower)
        return hits / len(cap.specialties)

    def _semantic_score(self, task: str, cap: AgentCapability) -> float:
        """Optional cosine similarity via sentence-transformers."""
        try:
            import numpy as np
            combined = " ".join(cap.specialties + cap.keywords)
            vecs = self._embedder.encode([task, combined],
                                          convert_to_numpy=True,
                                          normalize_embeddings=True)
            return float(np.dot(vecs[0], vecs[1]))
        except Exception:
            return 0.0

    def _explain(self, name: str, cap: AgentCapability,
                 task_tokens: List[str], score: float) -> str:
        kw = {k.lower() for k in cap.keywords}
        matched = [t for t in task_tokens if t in kw]
        return (f"Selected '{name}' (tier={cap.tier}, score={score:.2f}). "
                f"Matched keywords: {matched[:6]}")

    def _load_embedder(self):
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence-transformers not installed; "
                           "falling back to keyword-only scoring")
            return None


# ── YAML registry loader ───────────────────────────────────────────────────────

def load_registry(path: str) -> ContractNetRouter:
    """
    Build a ContractNetRouter from a YAML capability registry file.

    Expected YAML format::

        agents:
          - name: security-analyst
            tier: tactical
            specialties: [binary analysis, vulnerability assessment]
            keywords: [binary, CVE, exploit, malware]
            autonomy: supervised

    Returns:
        Populated ContractNetRouter.
    """
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to load a registry file. "
            "Install it with: pip install pyyaml"
        ) from exc

    with open(path, "r", encoding="utf-8") as fh:
        try:
            data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ValueError(f"Malformed YAML registry at '{path}': {exc}") from exc

    router = ContractNetRouter()
    for entry in data.get("agents", []):
        router.register(AgentCapability(**entry))
    return router


# ── Persistence (optional) ────────────────────────────────────────────────────

class RoutingLog:
    """
    Optional SQLite log of routing decisions for audit and analysis.

    db_path defaults to ``~/.local/share/contract_net_router/routing.db``
    (XDG-compliant, no hard-coded system paths).
    """

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS routing_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        winning_agent TEXT,
        score REAL DEFAULT 0.0,
        runner_up TEXT,
        runner_up_score REAL DEFAULT 0.0,
        rationale TEXT,
        created_at REAL NOT NULL
    );
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            data_dir = os.environ.get(
                "XDG_DATA_HOME",
                os.path.join(os.path.expanduser("~"), ".local", "share"),
            )
            db_dir = os.path.join(data_dir, "contract_net_router")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "routing.db")
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, timeout=5.0)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.executescript(self._SCHEMA)
        return self._conn

    def record(self, task: str, result: RouteResult) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO routing_decisions "
            "(task, winning_agent, score, runner_up, runner_up_score, "
            "rationale, created_at) VALUES (?,?,?,?,?,?,?)",
            (task[:500], result.winning_agent, result.score,
             result.runner_up, result.runner_up_score,
             result.rationale[:500], time.time()),
        )
        conn.commit()

    def recent(self, limit: int = 20) -> List[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT task, winning_agent, score, rationale, created_at "
            "FROM routing_decisions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"task": r[0], "winning_agent": r[1], "score": r[2],
                 "rationale": r[3], "created_at": r[4]} for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ── Utilities ─────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Lower-case word tokenizer (no NLTK dependency)."""
    return re.findall(r"[a-z0-9]+", text.lower())


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Command-line interface for contract-net-router.

    Sub-commands:
      route       --task TEXT [--registry PATH] [--json]
      list-agents [--registry PATH]
    """
    parser = argparse.ArgumentParser(
        prog="cnr",
        description="Contract Net Router — capability-matched agent task dispatch",
    )
    parser.add_argument(
        "--registry",
        default=None,
        metavar="PATH",
        help="Path to agents.yaml (overrides $CONTRACT_NET_AGENT_REGISTRY)",
    )
    subparsers = parser.add_subparsers(dest="command")

    # route
    route_p = subparsers.add_parser("route", help="Route a task to the best agent")
    route_p.add_argument("--task", required=True, help="Task description text")
    route_p.add_argument(
        "--json", dest="as_json", action="store_true", help="Output as JSON"
    )

    # list-agents
    subparsers.add_parser("list-agents", help="List registered agents")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # ── Load registry ──────────────────────────────────────────────────────
    registry_path = args.registry or os.environ.get("CONTRACT_NET_AGENT_REGISTRY")
    if registry_path:
        router = load_registry(registry_path)
    else:
        # Built-in demo agents so `cnr route --task X` works out of the box
        router = ContractNetRouter()
        router.register(AgentCapability(
            name="security-analyst", tier="tactical",
            specialties=["binary analysis", "vulnerability assessment"],
            keywords=["binary", "vulnerability", "CVE", "exploit", "disassemble"],
            autonomy="supervised",
        ))
        router.register(AgentCapability(
            name="data-analyst", tier="tactical",
            specialties=["data processing", "statistical analysis"],
            keywords=["CSV", "dataframe", "outlier", "statistics", "pandas"],
            autonomy="autonomous",
        ))

    # ── Dispatch ───────────────────────────────────────────────────────────
    if args.command == "route":
        result = router.route(args.task)
        if args.as_json:
            print(json.dumps({
                "winning_agent": result.winning_agent,
                "score": result.score,
                "runner_up": result.runner_up,
                "runner_up_score": result.runner_up_score,
                "rationale": result.rationale,
                "all_bids": result.all_bids,
            }))
        else:
            print(f"Winner:    {result.winning_agent}")
            print(f"Score:     {result.score:.4f}")
            if result.runner_up:
                print(f"Runner-up: {result.runner_up} ({result.runner_up_score:.4f})")
            print(f"Rationale: {result.rationale}")

    elif args.command == "list-agents":
        agents = router.list_agents()
        if not agents:
            print("No agents registered.")
            return
        for a in agents:
            print(
                f"  {a.name}  tier={a.tier}  "
                f"keywords={len(a.keywords)}  specialties={len(a.specialties)}"
            )
