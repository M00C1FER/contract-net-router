"""Smoke tests for contract-net-router."""
import json
import os
import sys
import tempfile

import pytest


def test_import():
    from contract_net_router import ContractNetRouter, AgentCapability
    assert ContractNetRouter
    assert AgentCapability


def test_route_to_best_agent():
    from contract_net_router import ContractNetRouter, AgentCapability
    router = ContractNetRouter()
    router.register(AgentCapability(
        name="security", tier="tactical",
        specialties=["security"], keywords=["vulnerability", "CVE", "exploit"],
        autonomy="supervised",
    ))
    router.register(AgentCapability(
        name="data", tier="tactical",
        specialties=["data"], keywords=["CSV", "statistics", "dataframe"],
        autonomy="autonomous",
    ))
    result = router.route("analyze CSV for statistical outliers")
    assert result.winning_agent == "data"


def test_no_agents_returns_none():
    from contract_net_router import ContractNetRouter
    router = ContractNetRouter()
    result = router.route("some task")
    assert result.winning_agent is None or result.score == 0.0


# ── Determinism / tiebreaker ──────────────────────────────────────────────────

def test_tiebreaker_is_alphabetical():
    """Agents with identical scores must resolve to the lexicographically first name."""
    from contract_net_router import ContractNetRouter, AgentCapability

    cap = dict(tier="tactical", specialties=["coding"], keywords=["python", "code"],
               autonomy="supervised")
    router = ContractNetRouter()
    # Register in reverse alphabetical order — winner should still be "agent-a"
    router.register(AgentCapability(name="agent-z", **cap))
    router.register(AgentCapability(name="agent-a", **cap))
    router.register(AgentCapability(name="agent-m", **cap))

    result = router.route("python code task")
    assert result.winning_agent == "agent-a", (
        "Tiebreaker must be alphabetical (deterministic), not insertion-order"
    )


def test_same_input_same_output():
    """Identical router state + task must produce identical output every time."""
    from contract_net_router import ContractNetRouter, AgentCapability

    def build_router():
        r = ContractNetRouter()
        r.register(AgentCapability(
            name="alpha", tier="tactical",
            specialties=["nlp"], keywords=["text", "parse", "tokenize"],
            autonomy="autonomous",
        ))
        r.register(AgentCapability(
            name="beta", tier="strategic",
            specialties=["vision"], keywords=["image", "detect", "classify"],
            autonomy="supervised",
        ))
        return r

    task = "tokenize and parse text corpus"
    results = [build_router().route(task) for _ in range(10)]
    winners = {r.winning_agent for r in results}
    scores = {r.score for r in results}
    assert len(winners) == 1, f"Non-deterministic winners: {winners}"
    assert len(scores) == 1, f"Non-deterministic scores: {scores}"


# ── Zero-bid behaviour ────────────────────────────────────────────────────────

def test_zero_bid_returns_no_winner():
    """When no agent matches the task, winning_agent must be None."""
    from contract_net_router import ContractNetRouter, AgentCapability

    router = ContractNetRouter()
    router.register(AgentCapability(
        name="specialist", tier="tactical",
        specialties=["image recognition"], keywords=["pixel", "CNN", "vision"],
        autonomy="autonomous",
    ))
    # Task has nothing to do with vision
    result = router.route("bake a sourdough loaf at 230°C for 40 minutes")
    assert result.winning_agent is None, (
        "All-zero-bid case must not claim a false winner"
    )
    assert result.score == 0.0


def test_zero_bid_has_all_bids_populated():
    """all_bids must still list every agent even when no one wins."""
    from contract_net_router import ContractNetRouter, AgentCapability

    router = ContractNetRouter()
    router.register(AgentCapability(
        name="agent-x", tier="tactical", specialties=[], keywords=["foo"],
        autonomy="supervised",
    ))
    router.register(AgentCapability(
        name="agent-y", tier="tactical", specialties=[], keywords=["bar"],
        autonomy="supervised",
    ))
    result = router.route("completely unrelated query zzzzzz")
    assert "agent-x" in result.all_bids
    assert "agent-y" in result.all_bids


# ── YAML registry loading ─────────────────────────────────────────────────────

def test_load_registry_from_yaml():
    from contract_net_router.router import load_registry

    yaml_content = """
agents:
  - name: sec
    tier: tactical
    specialties:
      - penetration testing
    keywords: [exploit, CVE, pentest]
    autonomy: supervised
  - name: dev
    tier: tactical
    specialties:
      - software development
    keywords: [python, refactor, unit test]
    autonomy: autonomous
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name

    try:
        router = load_registry(path)
        agents = {a.name for a in router.list_agents()}
        assert agents == {"sec", "dev"}
        result = router.route("write a python unit test for the refactored module")
        assert result.winning_agent == "dev"
    finally:
        os.unlink(path)


# ── CLI smoke tests ───────────────────────────────────────────────────────────

def test_cli_route_json(monkeypatch, capsys):
    """cnr route --task TEXT --json must emit valid JSON with expected keys."""
    from contract_net_router.router import main

    monkeypatch.setattr(
        sys, "argv",
        ["cnr", "route", "--task", "analyze CSV for statistical outliers", "--json"],
    )
    main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "winning_agent" in data
    assert "score" in data
    assert "all_bids" in data


def test_cli_list_agents(monkeypatch, capsys):
    """cnr list-agents must print at least one agent from the built-in demo set."""
    from contract_net_router.router import main

    monkeypatch.setattr(sys, "argv", ["cnr", "list-agents"])
    main()
    out = capsys.readouterr().out
    assert "data-analyst" in out or "security-analyst" in out


def test_cli_no_command(monkeypatch, capsys):
    """cnr with no sub-command must print help and not crash."""
    from contract_net_router.router import main

    monkeypatch.setattr(sys, "argv", ["cnr"])
    main()  # Should not raise


# ── RouteResult fields ────────────────────────────────────────────────────────

def test_route_result_runner_up():
    """runner_up must be the second-best agent."""
    from contract_net_router import ContractNetRouter, AgentCapability

    router = ContractNetRouter()
    router.register(AgentCapability(
        name="best", tier="tactical",
        specialties=["data analysis"], keywords=["CSV", "statistics", "outlier"],
        autonomy="autonomous",
    ))
    router.register(AgentCapability(
        name="second", tier="tactical",
        specialties=["reporting"], keywords=["CSV", "report"],
        autonomy="supervised",
    ))
    router.register(AgentCapability(
        name="worst", tier="rapid",
        specialties=["triage"], keywords=["ping"],
        autonomy="supervised",
    ))
    result = router.route("calculate statistics for CSV outlier detection")
    assert result.winning_agent == "best"
    assert result.runner_up is not None
    assert result.runner_up != result.winning_agent


def test_score_bounded():
    """Score must always be in [0.0, 1.0]."""
    from contract_net_router import ContractNetRouter, AgentCapability

    router = ContractNetRouter()
    router.register(AgentCapability(
        name="generalist", tier="command",
        specialties=["everything"],
        keywords=["a", "b", "c", "d", "e", "f", "g", "h"],
        autonomy="autonomous",
    ))
    result = router.route("a b c d e f g h task with everything")
    assert 0.0 <= result.score <= 1.0

