"""Write parsed broker transactions back out in the RAW format.

Two calculators reading the same Schwab export can disagree either because
they read the file differently or because they apply the rules differently.
Comparing only the final tax cannot tell those apart, and a match there may
mean both are right, both are wrong in the same way, or two errors cancelling.

Writing what each parser understood, in a format both can read back, puts a
seam between the two halves: the files are compared to each other, and then the
same file is fed to both engines.
"""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING

from .parsers.raw import COLUMNS

if TYPE_CHECKING:
    from pathlib import Path

    from .model import BrokerTransaction

# Prices are not rounded on the way out. A price is not money until it is
# multiplied by a quantity, and rounding it to pence moves a lot of 620 shares
# by over £3.
PRICE_DECIMALS = 8


def _number(value: object, decimals: int | None = None) -> str:
    if value is None:
        return ""
    if decimals is None:
        return str(value)
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def save_raw_transactions(
    transactions: list[BrokerTransaction],
    output_path: Path,
) -> None:
    """Write transactions to `output_path` in the RAW format.

    The result is readable by --raw-file, so the same file can be fed to
    another engine unchanged.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)

        for transaction in sorted(transactions, key=lambda t: t.date):
            writer.writerow(
                [
                    transaction.date.isoformat(),
                    transaction.action.name,
                    transaction.symbol or "",
                    _number(transaction.quantity),
                    _number(transaction.price, PRICE_DECIMALS),
                    _number(transaction.fees, 2),
                    transaction.currency,
                ]
            )
