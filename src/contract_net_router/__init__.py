"""contract-net-router — Contract-net bidding protocol agent router."""
__version__ = "1.0.0"

ADAPTERS = {
    "autogen": "adapters.autogen_shim",
    "crewai": "adapters.crewai_executor",
    "langgraph": "adapters.langgraph_adapter",
    "openai_agents": "adapters.openai_agents_adapter",
    "semantic_kernel": "adapters.semantic_kernel_adapter",
    "haystack": "adapters.haystack_adapter",
    "dspy": "adapters.dspy_adapter",
    "llamaindex": "adapters.llamaindex_adapter",
}

from contract_net_router.router import (
    AgentCapability,
    ContractBudget,
    ContractNetRouter,
    ContractRecord,
    ContractState,
    RouteResult,
    RoutingLog,
    validate_contract_transition,
)

__all__ = [
    "ADAPTERS",
    "AgentCapability",
    "ContractBudget",
    "ContractNetRouter",
    "ContractRecord",
    "ContractState",
    "RouteResult",
    "RoutingLog",
    "validate_contract_transition",
]
