"""Framework adapters for contract-net-router."""
from .autogen_shim import AutoGenCNPAdapter
from .base import BaseCNPAdapter, InMemoryCNPAdapter, StubFrameworkAdapter
from .crewai_executor import CrewAICNPAdapter
from .dspy_adapter import DSPyCNPAdapter
from .haystack_adapter import HaystackCNPAdapter
from .langgraph_adapter import LangGraphCNPAdapter
from .llamaindex_adapter import LlamaIndexCNPAdapter
from .openai_agents_adapter import OpenAIAgentsCNPAdapter
from .semantic_kernel_adapter import SemanticKernelCNPAdapter

__all__ = [
    "AutoGenCNPAdapter",
    "BaseCNPAdapter",
    "CrewAICNPAdapter",
    "DSPyCNPAdapter",
    "HaystackCNPAdapter",
    "InMemoryCNPAdapter",
    "LangGraphCNPAdapter",
    "LlamaIndexCNPAdapter",
    "OpenAIAgentsCNPAdapter",
    "SemanticKernelCNPAdapter",
    "StubFrameworkAdapter",
]
