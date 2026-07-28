"""Write the cost figures of a run in a form another tool can read.

The printed report is for a person. Anything checking these numbers against a
separate calculation has to be given them without a human retyping them in
between, or the retyping becomes the weakest link: a transposed digit in a
hand-copied figure makes a cross-check pass that should have failed.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from .util import round_decimal

if TYPE_CHECKING:
    from pathlib import Path

    from .model import CapitalGainsReport


def save_cost_summary(report: CapitalGainsReport, output_path: Path) -> None:
    """Write this run's cost figures to `output_path` as JSON.

    One file describes one tax year, which is how this tool runs. A checker
    given a file per year can add the allowable costs together and take the
    pool from the last of them.

    `allowable_costs` includes the fees charged on disposal, which are an
    allowable cost in their own right — worth knowing when reconciling against
    acquisition cost alone.

    Gains, losses and the net of the two are all written out. Gains and losses
    go in separate boxes on SA108 rather than netted, so both are needed; but a
    file offering only those two invites reading `capital_gain` as the answer,
    when the answer is the net. The loss is written as a positive amount, as
    the printed report shows it, rather than as the negative it is held as
    internally — a signed loss beside an unsigned gain is a subtraction waiting
    to be done twice or not at all.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "tax_year": report.tax_year,
        "currency": "GBP",
        "disposal_count": report.disposal_count,
        "disposal_proceeds": float(round_decimal(report.disposal_proceeds, 2)),
        # Includes disposal fees.
        "allowable_costs": float(round_decimal(report.allowable_costs, 2)),
        # Before losses are set against it. SA108 box 26.
        "capital_gain": float(round_decimal(report.capital_gain, 2)),
        # A positive amount. SA108 box 27.
        "capital_loss": float(round_decimal(-report.capital_loss, 2)),
        # capital_gain less capital_loss. The figure the tax is worked out from.
        "net_gain": float(round_decimal(report.total_gain(), 2)),
        "pool_at_tax_year_end": {
            entry.symbol: {
                "quantity": float(entry.quantity),
                "cost": float(round_decimal(entry.amount, 2)),
            }
            for entry in report.portfolio
        },
    }

    output_path.write_text(json.dumps(payload, indent=2) + "\n")
