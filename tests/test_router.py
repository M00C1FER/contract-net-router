"""Smoke tests for contract-net-router."""
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
