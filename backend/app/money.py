"""Money helpers. All money is integer rupees; this formats it the Indian way."""


def format_inr(amount: int, symbol: str = "₹") -> str:
    """280000 -> '₹2,80,000' (last three digits, then groups of two)."""
    digits = str(abs(int(amount)))
    head, tail = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    text = ",".join(groups + [tail])
    return ("-" if amount < 0 else "") + symbol + text
