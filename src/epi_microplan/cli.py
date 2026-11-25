"""CLI entrypoint for epi-microplan."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .microplan import DEFAULT_EPI_SCHEDULE, FacilitySupplySpec, build_district_microplan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="epi-microplan",
        description="WHO EPI district vaccine microplanning, open-vial wastage, and cold-chain volume CLI.",
    )
    parser.add_argument("--facility", default="HC3-KASESE", help="Facility or district identifier.")
    parser.add_argument("--population", type=int, default=45000, help="Catchment total population.")
    parser.add_argument("--infant-pct", type=float, default=3.8, help="Surviving infants percent of population.")
    parser.add_argument("--session-size", type=float, default=8.0, help="Average children per immunization session.")
    parser.add_argument("--fridge-liters", type=float, default=45.0, help="Existing +2..+8C net fridge liters.")
    parser.add_argument("--cycle-months", type=float, default=1.0, help="Resupply cycle in months.")
    parser.add_argument(
        "--antigens",
        nargs="+",
        default=list(DEFAULT_EPI_SCHEDULE),
        help="List of vaccine keys from WHO catalog.",
    )
    args = parser.parse_args(argv)

    plan = build_district_microplan(
        FacilitySupplySpec(
            facility_id=args.facility,
            catchment_population=args.population,
            surviving_infant_pct=args.infant_pct,
            avg_children_per_session=args.session_size,
            existing_fridge_net_liters=args.fridge_liters,
            supply_interval_months=args.cycle_months,
        ),
        antigens=args.antigens,
    )
    print(json.dumps(asdict(plan), indent=2))
    return 0 if plan.cold_chain_deficit_liters == 0.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
