"""Demo: route three tasks to the best matching agent."""
import tempfile
from pathlib import Path
from contract_net_router import ContractNetRouter, AgentCapability

router = ContractNetRouter()
router.register(AgentCapability(
    name="security-analyst",
    tier="tactical",
    specialties=["binary analysis", "vulnerability assessment"],
    keywords=["binary", "vulnerability", "CVE", "exploit", "malware"],
    autonomy="supervised",
))
router.register(AgentCapability(
    name="data-analyst",
    tier="tactical",
    specialties=["data processing", "statistical analysis"],
    keywords=["CSV", "dataframe", "outlier", "statistics", "pandas"],
    autonomy="autonomous",
))
router.register(AgentCapability(
    name="sre",
    tier="tactical",
    specialties=["infrastructure", "monitoring"],
    keywords=["latency", "CPU", "memory", "disk", "alert", "incident"],
    autonomy="supervised",
))

tasks = [
    "Analyze this binary for CVE vulnerabilities",
    "Parse the CSV and find statistical outliers",
    "The API is returning high latency — diagnose the incident",
]

for task in tasks:
    result = router.route(task)
    print(f"Task    : {task[:50]}...")
    print(f"  → {result.winning_agent} (score {result.score:.2f})")
    print()
