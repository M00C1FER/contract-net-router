"""Demo: contract lifecycle states and budget conservation."""
from contract_net_router import ContractNetRouter


def main() -> None:
    router = ContractNetRouter()

    parent = router.award_contract(
        task="Research and summarize a market landscape",
        bidder="manager",
        budget={"dollars": 1.0},
    )
    print(
        f"Parent {parent.contract_id} awarded with ${parent.budget.dollars:.2f} budget"
    )

    allocations = [
        ("researcher-a", "Find primary sources", 0.40),
        ("researcher-b", "Synthesize findings", 0.30),
        ("researcher-c", "Draft final brief", 0.30),
    ]
    children = []
    for bidder, task, dollars in allocations:
        child = router.award_contract(
            task=task,
            bidder=bidder,
            budget={"dollars": dollars},
            parent_contract_id=parent.contract_id,
        )
        children.append(child)
        print(
            f"  {child.contract_id} -> {bidder} awarded ${child.budget.dollars:.2f} "
            f"[{child.state.value}]"
        )

    print("Recursive conservation check:", router.check_budget_conservation(parent.contract_id))

    try:
        router.award_contract(
            task="Unplanned extra work",
            bidder="researcher-d",
            budget={"dollars": 0.05},
            parent_contract_id=parent.contract_id,
        )
    except ValueError as exc:
        print("Refused overallocation:", exc)

    router.report_consumption(children[1].contract_id, {"dollars": 0.31})
    overspent = router.get_contract(children[1].contract_id)
    print(
        f"Overspend demo: {overspent.contract_id} spent ${overspent.spent.dollars:.2f} "
        f"-> {overspent.state.value}"
    )


if __name__ == "__main__":
    main()
