"""The machine-readable cost summary.

Its purpose is to be read by something else, so the risk is not that a figure
is wrong but that the wrong figure is easy to pick up. A file offering a gain
and a loss but no net invites reading the gain as the answer.
"""

from __future__ import annotations

from decimal import Decimal
import json
from typing import TYPE_CHECKING

from cgt_calc.cost_summary import save_cost_summary
from cgt_calc.model import CapitalGainsReport, PortfolioEntry

if TYPE_CHECKING:
    from pathlib import Path


def build_report(
    gain: str = "120000.00",
    loss: str = "-500.00",
) -> CapitalGainsReport:
    """Build a report with a gain and a loss, as held internally: loss negative."""
    return CapitalGainsReport(
        tax_year=2025,
        portfolio=[
            PortfolioEntry(
                symbol="NVDA",
                quantity=Decimal(1500),
                amount=Decimal("75000.00"),
                unrealized_gains=None,
            )
        ],
        disposal_count=3,
        disposal_proceeds=Decimal("200000.00"),
        allowable_costs=Decimal("80000.00"),
        capital_gain=Decimal(gain),
        capital_loss=Decimal(loss),
        capital_gain_allowance=Decimal(3000),
        dividend_allowance=Decimal(500),
        calculation_log={},
        calculation_log_yields={},
        total_uk_interest=Decimal(0),
        total_foreign_interest=Decimal(0),
        show_unrealized_gains=False,
    )


def written(tmp_path: Path, report: CapitalGainsReport) -> dict:
    """Write the summary and read it back."""
    path = tmp_path / "summary.json"
    save_cost_summary(report, path)
    return json.loads(path.read_text())


def test_the_three_figures_agree(tmp_path: Path) -> None:
    """Gain less loss must equal the net, or the file offers a choice."""
    payload = written(tmp_path, build_report())

    assert payload["capital_gain"] - payload["capital_loss"] == payload["net_gain"]


def test_the_net_is_present(tmp_path: Path) -> None:
    """Without it, the gain reads as the answer when it is not.

    Gains and losses go in separate boxes on SA108 rather than netted, so both
    have to be kept; the net has to be there too, or the file has no single
    figure to take.
    """
    payload = written(tmp_path, build_report())

    assert payload["net_gain"] == 119500.00


def test_the_loss_is_written_as_a_positive_amount(tmp_path: Path) -> None:
    """As the printed report shows it, not as the negative it is held as.

    A signed loss beside an unsigned gain is a subtraction waiting to be done
    twice or not at all.
    """
    payload = written(tmp_path, build_report())

    assert payload["capital_loss"] == 500.00


def test_a_year_with_no_losses(tmp_path: Path) -> None:
    """With no losses the net equals the gain, and nothing is ambiguous."""
    payload = written(tmp_path, build_report(loss="0"))

    assert payload["capital_loss"] == 0
    assert payload["net_gain"] == payload["capital_gain"]


def test_the_pool_is_recorded_per_symbol(tmp_path: Path) -> None:
    """The closing pool is what a conservation check needs from the last year."""
    payload = written(tmp_path, build_report())

    assert payload["pool_at_tax_year_end"]["NVDA"] == {
        "quantity": 1500.0,
        "cost": 75000.00,
    }
