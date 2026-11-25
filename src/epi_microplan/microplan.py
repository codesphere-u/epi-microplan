"""WHO EPI session-driven open-vial wastage, cold-chain volume, and ILR/SDD capacity planner."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .catalog import VaccineSpec, get_vaccine_spec


def estimate_open_vial_wastage(
    spec: VaccineSpec,
    avg_children_per_session: float,
) -> float:
    """Estimate realistic open-vial wastage rate (fraction in [0, 0.95]) from session size.

    Lyophilized 6-hour discard vaccines (BCG, MR, Yellow Fever) discard all unused doses
    at session end; MDVP 28-day liquid vaccines retain opened vials across sessions.
    """
    if avg_children_per_session <= 0.0:
        raise ValueError("avg_children_per_session must be strictly positive")

    base_loss = spec.base_handling_wastage_pct / 100.0
    if spec.doses_per_vial == 1 or spec.mdvp_28_day_eligible:
        return min(0.95, base_loss)

    vials_opened = math.ceil(avg_children_per_session / spec.doses_per_vial)
    doses_opened = vials_opened * spec.doses_per_vial
    session_discard = max(0.0, 1.0 - (avg_children_per_session / doses_opened))
    # Combine session discard and closed-vial handling loss
    combined = 1.0 - (1.0 - session_discard) * (1.0 - base_loss)
    return min(0.95, combined)


@dataclass(frozen=True)
class FacilitySupplySpec:
    """Catchment demographics, delivery cadence, and existing cold-chain capacity."""

    facility_id: str
    catchment_population: int
    surviving_infant_pct: float = 3.8
    coverage_target_pct: float = 95.0
    supply_interval_months: float = 1.0
    buffer_stock_pct: float = 25.0
    avg_children_per_session: float = 8.0
    existing_fridge_net_liters: float = 45.0

    def __post_init__(self) -> None:
        if self.catchment_population <= 0:
            raise ValueError("catchment_population must be positive")
        if not (0.5 <= self.surviving_infant_pct <= 10.0):
            raise ValueError("surviving_infant_pct must be in [0.5, 10.0]")
        if not (10.0 <= self.coverage_target_pct <= 100.0):
            raise ValueError("coverage_target_pct must be in [10, 100]")
        if self.supply_interval_months <= 0.0 or self.buffer_stock_pct < 0.0:
            raise ValueError("Invalid supply interval or buffer stock")
        if self.existing_fridge_net_liters < 0.0:
            raise ValueError("existing_fridge_net_liters cannot be negative")


@dataclass(frozen=True)
class AntigenPlan:
    """Supply-cycle doses, vials, syringes, and cold-chain volume for one antigen."""

    vaccine_key: str
    display_name: str
    estimated_wastage_pct: float
    wastage_factor: float
    target_doses_administered: int
    total_doses_required: int
    vials_required: int
    vaccine_volume_liters: float
    diluent_chill_liters: float
    ad_syringes_required: int
    reconstitution_syringes_required: int
    freeze_sensitive: bool
    vial_size_tip: str | None


@dataclass(frozen=True)
class DistrictMicroplan:
    """Full immunization supply-cycle microplan and cold-chain deficit verdict."""

    facility_id: str
    annual_target_infants: int
    cycle_months: float
    antigen_plans: tuple[AntigenPlan, ...]
    total_vaccine_liters: float
    total_diluent_chill_liters: float
    total_required_cold_chain_liters: float
    existing_fridge_net_liters: float
    cold_chain_deficit_liters: float
    recommended_additional_sdd_45l_units: int
    outreach_carriers_2_6l_needed: int
    total_ad_syringes: int
    total_reconstitution_syringes: int
    safety_boxes_5l_required: int
    warnings: tuple[str, ...]


DEFAULT_EPI_SCHEDULE: tuple[str, ...] = (
    "bcg",
    "bopv",
    "ipv",
    "pentavalent",
    "pcv13",
    "rotavirus",
    "measles_rubella",
    "yellow_fever",
)


def build_district_microplan(
    facility: FacilitySupplySpec,
    *,
    antigens: Sequence[str] = DEFAULT_EPI_SCHEDULE,
) -> DistrictMicroplan:
    """Calculate doses, open-vial wastage, cold-chain liters, SDD units, and sharps safety boxes."""
    if not antigens:
        raise ValueError("At least one antigen is required")

    annual_infants = max(1, round(facility.catchment_population * (facility.surviving_infant_pct / 100.0)))
    cycle_frac = facility.supply_interval_months / 12.0
    coverage = facility.coverage_target_pct / 100.0
    buffer_mult = 1.0 + (facility.buffer_stock_pct / 100.0)

    plans: list[AntigenPlan] = []
    warnings: list[str] = []
    tot_vax_l = 0.0
    tot_dil_l = 0.0
    tot_ad = 0
    tot_recon = 0

    for key in antigens:
        spec = get_vaccine_spec(key)
        wastage = estimate_open_vial_wastage(spec, facility.avg_children_per_session)
        wf = 1.0 / (1.0 - wastage)
        admin_doses = max(1, math.ceil(annual_infants * spec.doses_per_child * coverage * cycle_frac))
        req_doses = math.ceil(admin_doses * wf * buffer_mult)
        vials = math.ceil(req_doses / spec.doses_per_vial)
        actual_doses = vials * spec.doses_per_vial

        vax_l = (actual_doses * spec.packed_volume_cm3_per_dose) / 1000.0
        # Only 1 session's worth (~15% of monthly cycle) of diluent must be pre-chilled inside fridge
        dil_l = (actual_doses * spec.diluent_volume_cm3_per_dose * 0.20) / 1000.0

        ad_syr = math.ceil(admin_doses * 1.10 * buffer_mult) if spec.injectable else 0
        recon_syr = math.ceil(vials * 1.10) if spec.reconstitution_syringe_per_vial else 0

        tip: str | None = None
        if not spec.mdvp_28_day_eligible and spec.doses_per_vial >= 10 and wastage >= 0.45:
            tip = (
                f"HIGH OPEN-VIAL WASTAGE ({wastage * 100:.0f}%): session size {facility.avg_children_per_session:.1f} "
                f"with {spec.doses_per_vial}-dose lyophilized vial; consider 5-dose vials or batched sessions."
            )
            warnings.append(f"{spec.key}: {tip}")

        tot_vax_l += vax_l
        tot_dil_l += dil_l
        tot_ad += ad_syr
        tot_recon += recon_syr

        plans.append(
            AntigenPlan(
                vaccine_key=spec.key,
                display_name=spec.display_name,
                estimated_wastage_pct=round(wastage * 100.0, 1),
                wastage_factor=round(wf, 3),
                target_doses_administered=admin_doses,
                total_doses_required=actual_doses,
                vials_required=vials,
                vaccine_volume_liters=round(vax_l, 3),
                diluent_chill_liters=round(dil_l, 3),
                ad_syringes_required=ad_syr,
                reconstitution_syringes_required=recon_syr,
                freeze_sensitive=spec.freeze_sensitive,
                vial_size_tip=tip,
            )
        )

    req_cold_l = tot_vax_l + tot_dil_l
    deficit = max(0.0, req_cold_l - facility.existing_fridge_net_liters)
    add_sdd = math.ceil(deficit / 45.0) if deficit > 0.0 else 0
    if deficit > 0.0:
        warnings.append(
            f"COLD-CHAIN DEFICIT: need {req_cold_l:.1f} L (+2..+8C) vs {facility.existing_fridge_net_liters:.1f} L "
            f"available (short {deficit:.1f} L; add {add_sdd}x 45L Solar Direct-Drive ILR unit(s))."
        )

    # Outreach session vaccine carriers (2.6 L net each) sized for ~1/4 of monthly stock per outreach push
    outreach_carriers = max(1, math.ceil((req_cold_l * 0.25) / 2.6))
    # WHO standard 5L sharps safety box holds 100 syringes
    safety_boxes = math.ceil((tot_ad + tot_recon) / 100.0)

    return DistrictMicroplan(
        facility_id=facility.facility_id,
        annual_target_infants=annual_infants,
        cycle_months=facility.supply_interval_months,
        antigen_plans=tuple(plans),
        total_vaccine_liters=round(tot_vax_l, 2),
        total_diluent_chill_liters=round(tot_dil_l, 2),
        total_required_cold_chain_liters=round(req_cold_l, 2),
        existing_fridge_net_liters=round(facility.existing_fridge_net_liters, 2),
        cold_chain_deficit_liters=round(deficit, 2),
        recommended_additional_sdd_45l_units=add_sdd,
        outreach_carriers_2_6l_needed=outreach_carriers,
        total_ad_syringes=tot_ad,
        total_reconstitution_syringes=tot_recon,
        safety_boxes_5l_required=safety_boxes,
        warnings=tuple(warnings),
    )
