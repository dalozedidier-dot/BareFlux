"""MCS - Modele de Coherence Systemique.

Indice de Marge Systemique M(t), dette invisible D(t) et pre-rupture.
Implementation du document de travail de Didier Daloze.

Avertissement : cadre exploratoire et pedagogique, confrontable aux
donnees. Ce n'est PAS un outil de diagnostic clinique, psychologique
ou organisationnel valide.
"""

from .core import (
    DEFAULT_THRESHOLDS,
    HysteresisClassifier,
    Zone,
    bounded_margin_index,
    capacity,
    classify,
    debt_rest_level,
    debt_update,
    leak,
    margin,
    margin_index,
    margin_uncertainty,
    overflow,
    total_load,
)
from .extensions import (
    ControlParams,
    RecoveryParams,
    ThetaParams,
    alpha_runaway,
    control_command,
    debt_update_with_repayment,
    effective_feedback,
    effective_load,
    effective_recovery,
    normalized_debt,
    optimal_control,
    repayment_rate,
    rescale_time_step,
    theta_target,
    theta_update,
    viability_repayment_threshold,
)
from .network import NetworkConfig, saturation, simulate_network
from .simulator import SimConfig, SimResult, simulate

__version__ = "0.1.0"
__all__ = [
    "DEFAULT_THRESHOLDS", "HysteresisClassifier", "Zone",
    "bounded_margin_index", "capacity", "classify", "debt_rest_level",
    "debt_update", "leak", "margin", "margin_index", "margin_uncertainty",
    "overflow", "total_load",
    "ControlParams", "RecoveryParams", "ThetaParams", "alpha_runaway",
    "control_command", "debt_update_with_repayment", "effective_feedback",
    "effective_load", "effective_recovery", "normalized_debt",
    "optimal_control", "repayment_rate", "rescale_time_step",
    "theta_target", "theta_update", "viability_repayment_threshold",
    "NetworkConfig", "saturation", "simulate_network",
    "SimConfig", "SimResult", "simulate",
]
