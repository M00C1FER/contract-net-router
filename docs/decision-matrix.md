# When to use contract-net-router vs CrewAI / AutoGen

| Scenario | Use contract-net-router | Use CrewAI / AutoGen |
|---|---|---|
| Agents in different runtimes (Python + Go + Rust) | Yes | No — Python lock |
| Formal audit trail of bid/award decisions | Yes | No |
| Coalition formation (subset agrees on scope) | Yes | No — hand-rolled |
| Standard research/writing pipeline, homogeneous Python agents | No | Yes — faster, more scaffolding |
| Rapid prototyping under deadline | No | Yes — lower boilerplate |
| Capability-based bidding with health-aware penalty scoring | Yes | No |
