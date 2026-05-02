# Contract Net Router

> Capability-based task routing for multi-agent AI systems — agents bid on tasks they're qualified for, and the best-match wins.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20WSL%20%7C%20Termux-lightgrey)](install.sh)

## What It Does

Static routing tables break as agent rosters evolve. Contract Net Router implements the FIPA Contract Net Protocol: a manager broadcasts a task, agents evaluate it against their capabilities and submit bids with confidence scores, and the router selects the highest-scoring match. Agents are defined in a YAML registry — no code changes needed to add or reconfigure agents.

**Key capabilities:**
- FIPA Contract Net bidding (broadcast → bid → award)
- YAML-defined agent capability registries
- Keyword-based and tier-aware scoring
- Deny-list enforcement per agent
- Programmatic and CLI interfaces

## Quick Start

```bash
bash install.sh
cnr --help
cnr route --task "analyze this binary for vulnerabilities"
cnr list-agents
```

## Installation

| Platform | Method |
|----------|--------|
| Linux / WSL | `bash install.sh` |
| Termux (Android) | `bash install.sh` (no sudo) |
| pip | `pip install .` |

```bash
git clone https://github.com/M00C1FER/contract-net-router
cd contract-net-router
bash install.sh
```

## Usage

```python
from contract_net_router import ContractNetRouter

router = ContractNetRouter.from_yaml("agents.yaml")

result = router.route("Analyze this CSV for outliers and generate a summary report")

print(result.winning_agent)      # "data-analyst"
print(result.score)              # 0.87
print(result.tier)               # "tactical"
print(result.runner_up)          # "report-writer" at 0.71
```

## Agent Registry Format

```yaml
# agents.yaml
agents:
  - name: security-analyst
    tier: tactical
    specialties:
      - binary analysis
      - vulnerability assessment
      - reverse engineering
    keywords: [binary, vulnerability, CVE, exploit, disassemble]
    autonomy: supervised
    deny_tools: []

  - name: data-analyst
    tier: tactical
    specialties:
      - data processing
      - statistical analysis
    keywords: [CSV, dataframe, outlier, statistics, pandas]
    autonomy: autonomous
```

## Architecture (MOSA)

```
contract-net-router/
├── src/contract_net_router/
│   ├── router.py          # Contract Net bidding engine
│   └── __init__.py
├── install.sh             # Cross-platform wizard
├── examples/
│   ├── demo.py            # Multi-agent routing demo
│   └── agents.yaml        # Example agent registry
└── TOOLS.md
```

## Scoring Algorithm

Each agent produces a bid score in [0.0, 1.0]:

```
base  = (keyword_overlap × 0.6) + (specialty_match × 0.4)
score = min(1.0, base × tier_weight)
```

Tier weights: `command` 1.30 → `strategic` 1.15 → `tactical` 1.00 → `rapid` 0.80.

When all agents score 0.0 (no keywords or specialties matched), the router
returns `winning_agent=None`. Ties at equal score are broken alphabetically
by agent name, guaranteeing deterministic output for identical input.

## Cross-Platform Notes

Pure Python stdlib — runs on Linux, WSL, and Termux identically.

## License

[MIT](LICENSE)
