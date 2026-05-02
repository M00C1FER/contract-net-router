# Reference Projects

Projects studied during the 2026-05-02 audit cycle for patterns and best practices.

| # | Repository | Stars | License | Pattern borrowed |
|---|-----------|-------|---------|-----------------|
| 1 | [microsoft/autogen](https://github.com/microsoft/autogen) | ★22k | MIT | **Deterministic agent selection**: AutoGen's `GroupChat.select_speaker()` uses a stable sort with an explicit name-based secondary key when speaker scores are tied, eliminating insertion-order non-determinism. We adopted the same `key=lambda x: (-x[1], x[0])` pattern in `ContractNetRouter.route()`. |
| 2 | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | ★21k | MIT | **Zero-bid guard**: crewAI's `TaskPlanner` raises a `NoAgentAvailableError` when no agent accepts a task, rather than returning a placeholder winner with score 0. We mirror this: `ContractNetRouter.route()` now returns `winning_agent=None` when all bids are zero. |
| 3 | [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | ★90k | MIT | **CLI via `argparse` sub-commands**: LangChain's `langchain` CLI uses `argparse` with sub-commands (`serve`, `run`, etc.) and a `--json` flag for machine-readable output. We followed the same structure for the `cnr route` / `cnr list-agents` CLI. |
| 4 | [pydantic/pydantic](https://github.com/pydantic/pydantic) | ★20k | MIT | **Dataclass field documentation**: pydantic documents every dataclass field in the class docstring with `Args:` entries. We extended the `AgentCapability` docstring to cover all fields for IDE discoverability. |
| 5 | [tiangolo/typer](https://github.com/tiangolo/typer) | ★16k | MIT | **Cross-platform install scripting**: Typer's `install.sh` detects `apk` (Alpine), `apt`, `dnf`, and `pacman` with explicit fallback ordering. We added the missing `apk` branch to our `install_deps_system()` function. |
