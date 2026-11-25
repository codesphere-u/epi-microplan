"""WHO PQS vaccine packed-volume, dosing schedule, and Multi-Dose Vial Policy (MDVP) catalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VaccineSpec:
    """WHO EPI antigen cold-chain and presentation parameters."""

    key: str
    display_name: str
    doses_per_child: int
    doses_per_vial: int
    packed_volume_cm3_per_dose: float
    diluent_volume_cm3_per_dose: float
    mdvp_28_day_eligible: bool  # False => lyophilized 6-hour discard after reconstitution
    freeze_sensitive: bool
    injectable: bool
    reconstitution_syringe_per_vial: bool = False
    base_handling_wastage_pct: float = 5.0


VACCINE_CATALOG: dict[str, VaccineSpec] = {
    "bcg": VaccineSpec(
        key="bcg",
        display_name="BCG (Tuberculosis)",
        doses_per_child=1,
        doses_per_vial=20,
        packed_volume_cm3_per_dose=1.2,
        diluent_volume_cm3_per_dose=0.7,
        mdvp_28_day_eligible=False,
        freeze_sensitive=False,
        injectable=True,
        reconstitution_syringe_per_vial=True,
    ),
    "bopv": VaccineSpec(
        key="bopv",
        display_name="bOPV (Oral Polio)",
        doses_per_child=4,
        doses_per_vial=20,
        packed_volume_cm3_per_dose=1.0,
        diluent_volume_cm3_per_dose=0.0,
        mdvp_28_day_eligible=True,
        freeze_sensitive=False,
        injectable=False,
        base_handling_wastage_pct=10.0,
    ),
    "ipv": VaccineSpec(
        key="ipv",
        display_name="IPV (Inactivated Polio)",
        doses_per_child=2,
        doses_per_vial=5,
        packed_volume_cm3_per_dose=2.5,
        diluent_volume_cm3_per_dose=0.0,
        mdvp_28_day_eligible=True,
        freeze_sensitive=True,
        injectable=True,
    ),
    "pentavalent": VaccineSpec(
        key="pentavalent",
        display_name="DTP-HepB-Hib (Pentavalent)",
        doses_per_child=3,
        doses_per_vial=10,
        packed_volume_cm3_per_dose=2.6,
        diluent_volume_cm3_per_dose=0.0,
        mdvp_28_day_eligible=True,
        freeze_sensitive=True,
        injectable=True,
    ),
    "pcv13": VaccineSpec(
        key="pcv13",
        display_name="PCV-13 (Pneumococcal)",
        doses_per_child=3,
        doses_per_vial=4,
        packed_volume_cm3_per_dose=4.8,
        diluent_volume_cm3_per_dose=0.0,
        mdvp_28_day_eligible=True,
        freeze_sensitive=True,
        injectable=True,
    ),
    "rotavirus": VaccineSpec(
        key="rotavirus",
        display_name="Rotavirus (Oral, 1-dose tube)",
        doses_per_child=2,
        doses_per_vial=1,
        packed_volume_cm3_per_dose=17.1,
        diluent_volume_cm3_per_dose=0.0,
        mdvp_28_day_eligible=True,
        freeze_sensitive=True,
        injectable=False,
        base_handling_wastage_pct=5.0,
    ),
    "measles_rubella": VaccineSpec(
        key="measles_rubella",
        display_name="Measles-Rubella (MR 10-dose)",
        doses_per_child=2,
        doses_per_vial=10,
        packed_volume_cm3_per_dose=2.1,
        diluent_volume_cm3_per_dose=3.1,
        mdvp_28_day_eligible=False,
        freeze_sensitive=False,
        injectable=True,
        reconstitution_syringe_per_vial=True,
    ),
    "measles_rubella_5dose": VaccineSpec(
        key="measles_rubella_5dose",
        display_name="Measles-Rubella (MR 5-dose)",
        doses_per_child=2,
        doses_per_vial=5,
        packed_volume_cm3_per_dose=3.5,
        diluent_volume_cm3_per_dose=4.2,
        mdvp_28_day_eligible=False,
        freeze_sensitive=False,
        injectable=True,
        reconstitution_syringe_per_vial=True,
    ),
    "yellow_fever": VaccineSpec(
        key="yellow_fever",
        display_name="Yellow Fever (10-dose)",
        doses_per_child=1,
        doses_per_vial=10,
        packed_volume_cm3_per_dose=2.5,
        diluent_volume_cm3_per_dose=2.5,
        mdvp_28_day_eligible=False,
        freeze_sensitive=False,
        injectable=True,
        reconstitution_syringe_per_vial=True,
    ),
    "malaria_r21": VaccineSpec(
        key="malaria_r21",
        display_name="Malaria R21/Matrix-M (2-dose)",
        doses_per_child=4,
        doses_per_vial=2,
        packed_volume_cm3_per_dose=6.5,
        diluent_volume_cm3_per_dose=0.0,
        mdvp_28_day_eligible=False,
        freeze_sensitive=True,
        injectable=True,
    ),
}


def get_vaccine_spec(key: str) -> VaccineSpec:
    norm = key.strip().lower().replace("-", "_").replace(" ", "_")
    if norm not in VACCINE_CATALOG:
        raise KeyError(f"Unknown vaccine '{key}'. Available: {', '.join(sorted(VACCINE_CATALOG))}")
    return VACCINE_CATALOG[norm]
