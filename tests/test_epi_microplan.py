"""Tests for epi-microplan."""

from __future__ import annotations

import json

import pytest

from epi_microplan import (
    FacilitySupplySpec,
    build_district_microplan,
    estimate_open_vial_wastage,
    get_vaccine_spec,
)
from epi_microplan.cli import main as cli_main


def test_small_session_lyophilized_wastage_exceeds_5dose_and_mdvp() -> None:
    mr10 = get_vaccine_spec("measles_rubella")
    mr5 = get_vaccine_spec("measles_rubella_5dose")
    penta = get_vaccine_spec("pentavalent")

    w_mr10 = estimate_open_vial_wastage(mr10, avg_children_per_session=3.0)
    w_mr5 = estimate_open_vial_wastage(mr5, avg_children_per_session=3.0)
    w_penta = estimate_open_vial_wastage(penta, avg_children_per_session=3.0)

    # 3 children from a 10-dose 6h vial wastes >= 70%
    assert w_mr10 > 0.70
    # 5-dose vial cuts wastage dramatically to ~43%
    assert w_mr5 < 0.45
    # MDVP 28-day liquid pentavalent stays at base handling loss (5%)
    assert w_penta == pytest.approx(0.05)


def test_cold_chain_deficit_triggers_sdd_recommendation() -> None:
    spec = FacilitySupplySpec(
        facility_id="DIST-MBALE",
        catchment_population=350000,
        supply_interval_months=1.0,
        avg_children_per_session=4.0,
        existing_fridge_net_liters=30.0,
    )
    plan = build_district_microplan(spec)
    assert plan.total_required_cold_chain_liters > 30.0
    assert plan.cold_chain_deficit_liters > 0.0
    assert plan.recommended_additional_sdd_45l_units >= 1
    assert plan.safety_boxes_5l_required >= 50
    assert any("COLD-CHAIN DEFICIT" in w for w in plan.warnings)
    assert any("HIGH OPEN-VIAL WASTAGE" in w for w in plan.warnings)


def test_rotavirus_dominates_packed_volume() -> None:
    plan = build_district_microplan(
        FacilitySupplySpec(facility_id="HC3", catchment_population=30000, existing_fridge_net_liters=90.0),
        antigens=["bopv", "pentavalent", "rotavirus"],
    )
    vols = {a.vaccine_key: a.vaccine_volume_liters for a in plan.antigen_plans}
    assert vols["rotavirus"] > vols["pentavalent"] > vols["bopv"]
    assert plan.cold_chain_deficit_liters == 0.0


def test_cli_exit_codes(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli_main(["--population", "25000", "--fridge-liters", "60", "--session-size", "12"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["cold_chain_deficit_liters"] == 0.0

    rc_def = cli_main(["--population", "500000", "--fridge-liters", "20"])
    assert rc_def == 1
    out2 = json.loads(capsys.readouterr().out)
    assert out2["recommended_additional_sdd_45l_units"] >= 1
