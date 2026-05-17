"""Adapter registry and smoke tests."""
from __future__ import annotations

import importlib

import pytest

from contract_net_router import ADAPTERS
from contract_net_router.adapters.autogen_shim import AutoGenCNPAdapter
from contract_net_router.adapters.crewai_executor import CrewAICNPAdapter
from contract_net_router.adapters.dspy_adapter import DSPyCNPAdapter
from contract_net_router.adapters.haystack_adapter import HaystackCNPAdapter
from contract_net_router.adapters.langgraph_adapter import LangGraphCNPAdapter
from contract_net_router.adapters.llamaindex_adapter import LlamaIndexCNPAdapter
from contract_net_router.adapters.openai_agents_adapter import OpenAIAgentsCNPAdapter
from contract_net_router.adapters.semantic_kernel_adapter import SemanticKernelCNPAdapter


def test_adapter_registry_covers_all_frameworks():
    assert set(ADAPTERS) == {
        "autogen",
        "crewai",
        "langgraph",
        "openai_agents",
        "semantic_kernel",
        "haystack",
        "dspy",
        "llamaindex",
    }
    for module_path in ADAPTERS.values():
        importlib.import_module(f"contract_net_router.{module_path}")


def test_autogen_adapter_bid_award_audit_roundtrip():
    adapter = AutoGenCNPAdapter(
        agent_id="autogen-agent",
        capability_keywords=["analysis", "report", "csv"],
        estimated_cost=2.5,
    )
    task = {"task_id": "task-1", "description": "analysis report for csv data"}
    bid = adapter.bid(task)
    assert bid == {
        "agent_id": "autogen-agent",
        "capability_score": pytest.approx(1.0),
        "estimated_cost": pytest.approx(2.5),
    }
    assert adapter.award(task, bid) is True
    audit = adapter.audit("task-1")
    assert audit["task_id"] == "task-1"
    assert audit["status"] == "awarded"
    assert audit["agent_id"] == "autogen-agent"
    assert "awarded_at" in audit["timestamps"]


def test_crewai_adapter_rejects_other_agent_award():
    adapter = CrewAICNPAdapter(agent_id="crewai-agent", capability_keywords=["router"])
    task = {"task_id": "task-2", "description": "router governance task"}
    foreign_bid = {"agent_id": "other-agent", "capability_score": 0.9, "estimated_cost": 1.0}
    assert adapter.award(task, foreign_bid) is False
    assert adapter.audit("task-2")["status"] == "unknown"


@pytest.mark.parametrize(
    "adapter_cls",
    [
        LangGraphCNPAdapter,
        OpenAIAgentsCNPAdapter,
        SemanticKernelCNPAdapter,
        HaystackCNPAdapter,
        DSPyCNPAdapter,
        LlamaIndexCNPAdapter,
    ],
)
def test_stub_adapters_raise_not_implemented(adapter_cls):
    adapter = adapter_cls(agent_id="stub-agent")
    with pytest.raises(NotImplementedError):
        adapter.bid({"task_id": "task", "description": "test"})
