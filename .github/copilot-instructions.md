# Copilot Coding Agent — Instructions

## Project context

`contract-net-router` is a Python implementation of FIPA Contract Net Protocol (Smith 1980) for LLM agent dispatch. Capability-based bidding, coalition formation, health-aware penalty scoring. **Protocol layer, not a framework** — positioned as a primitive that frameworks (CrewAI, AutoGen, LangGraph) could be built on top of, not a competitor to them.

The 2025 paper *Agent Contracts* (arxiv 2601.08815, COINE 2026) explicitly notes none of the 8 major LLM agent frameworks (LangGraph, AutoGen, CrewAI, OpenAI Agents SDK, Google ADK, Amazon Bedrock, LlamaIndex, smolagents) implement formal governance mechanisms. This repo's goal is to fill that gap.

## Coding rules

- Python 3.10+.
- Use `enum.Enum` (or `StrEnum` if 3.11+ assumed) for state machines, never raw strings.
- State transition logic must be encapsulated in a `validate_transition(from_state, to_state)` helper, not scattered through caller code.
- Type hints on every public function. Prefer `TypedDict` or `dataclasses.dataclass` over loose dicts for structured payloads.
- No global mutable state. Routing state is held in router instance; bidder state is held in bidder instances.
- Imports sorted: stdlib, third-party, local.
- Audit log entries are append-only — never mutate prior entries.

## Tests

- Every new public function: unit test.
- Every new state transition: unit test for legal transition + unit test for illegal transition (must raise).
- Recursive logic (e.g., budget conservation across nested contracts): explicit test for at least 3-level nesting.
- Tests run via `pytest` from repo root.
- Test fixture for budget conservation must demonstrate: parent $1.00 → 3 children with $0.40 / $0.30 / $0.30 sum = $1.00; over-spend triggers `ContractState.VIOLATED`.

## File naming

- Snake_case Python modules.
- New protocol primitives go under `contract_net_router/` package.
- Examples / demos go under `examples/` with self-contained scripts.
- Decision matrix doc goes at `docs/decision-matrix.md` per issue #3 spec.

## Don't touch

- Existing public API of `Router.dispatch()` and `Bidder.bid()` — only extend, don't break.
- `LICENSE`, `pyproject.toml` version (handled separately).
- `.github/workflows/` unless issue explicitly says so.

## Acceptance signal

A PR is ready for review when:
1. `pytest` passes locally with all new tests included.
2. Recursive logic has explicit fixture coverage.
3. README cites Smith 1980 + arxiv 2601.08815 with correct hyperlinks.
4. State machine has `from_state, to_state, allowed: bool` table documented in code (or markdown).
5. Backward compatibility: existing examples in `examples/` still run unchanged.
