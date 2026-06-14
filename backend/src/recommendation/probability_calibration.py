"""Runtime application of offline-validated admission probability calibration."""

from __future__ import annotations

from bisect import bisect_right
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from models.game_matrix import MajorGroupRow


class BetaCalibrationModel(BaseModel):
    """Logistic beta-calibration coefficients fitted on frozen outcomes."""

    intercept: float
    log_probability_coefficient: float
    log_one_minus_probability_coefficient: float
    blend_weight: float = Field(default=1.0, ge=0.0, le=1.0)


class ProbabilityCalibrationArtifact(BaseModel):
    """Serializable monotonic calibration artifact fitted offline."""

    version: str
    calibration_year: int
    source: str
    method: str = "isotonic"
    x_thresholds: list[float] = Field(default_factory=list)
    y_thresholds: list[float] = Field(default_factory=list)
    global_beta: BetaCalibrationModel | None = None
    subject_beta: dict[str, BetaCalibrationModel] = Field(default_factory=dict)
    subsequent_choice_hazard_scale: float = Field(ge=0.0, le=1.0)
    cross_validation: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_thresholds(self):
        if self.method == "beta_subject":
            if self.global_beta is None:
                raise ValueError("Subject beta calibration requires a global fallback model.")
            return self
        if len(self.x_thresholds) != len(self.y_thresholds) or len(self.x_thresholds) < 2:
            raise ValueError("Calibration thresholds must have equal length and at least two points.")
        if self.x_thresholds != sorted(self.x_thresholds):
            raise ValueError("Calibration x thresholds must be sorted.")
        if self.y_thresholds != sorted(self.y_thresholds):
            raise ValueError("Calibration y thresholds must be monotonic.")
        return self


def _normalize_subject_group(subject_group: str | None) -> str:
    text = str(subject_group or "").strip().lower()
    if "历史" in text or "history" in text:
        return "history"
    if "物理" in text or "physics" in text:
        return "physics"
    return "unknown"


def _apply_beta_model(raw: float, model: BetaCalibrationModel) -> float:
    clipped = max(1e-6, min(1.0 - 1e-6, raw))
    logit = (
        model.intercept
        + model.log_probability_coefficient * math.log(clipped)
        + model.log_one_minus_probability_coefficient * math.log(1.0 - clipped)
    )
    if logit >= 0:
        calibrated = 1.0 / (1.0 + math.exp(-logit))
    else:
        exp_logit = math.exp(logit)
        calibrated = exp_logit / (1.0 + exp_logit)
    return max(0.0, min(1.0, calibrated))


def calibrate_probability(
    raw_probability: float,
    artifact: ProbabilityCalibrationArtifact,
    *,
    subject_group: str | None = None,
) -> float:
    """Apply the artifact's historical calibration with a safe global fallback."""
    raw = max(0.0, min(1.0, float(raw_probability)))
    if artifact.method == "beta_subject" and artifact.global_beta is not None:
        global_value = _apply_beta_model(raw, artifact.global_beta)
        local_model = artifact.subject_beta.get(_normalize_subject_group(subject_group))
        if local_model is None:
            return round(global_value, 6)
        local_value = _apply_beta_model(raw, local_model)
        blended = (
            local_model.blend_weight * local_value
            + (1.0 - local_model.blend_weight) * global_value
        )
        return round(max(0.0, min(1.0, blended)), 6)

    xs = artifact.x_thresholds
    ys = artifact.y_thresholds
    if raw <= xs[0]:
        return round(float(ys[0]), 6)
    if raw >= xs[-1]:
        return round(float(ys[-1]), 6)
    right = bisect_right(xs, raw)
    left = right - 1
    width = xs[right] - xs[left]
    if width <= 0:
        return round(float(ys[right]), 6)
    fraction = (raw - xs[left]) / width
    calibrated = ys[left] + fraction * (ys[right] - ys[left])
    return round(max(0.0, min(1.0, calibrated)), 6)


def apply_group_probability_calibration(
    row: MajorGroupRow,
    artifact: ProbabilityCalibrationArtifact,
    *,
    subject_group: str | None = None,
) -> MajorGroupRow:
    """Replace the user-facing probability while preserving the raw model score."""
    raw = float(row.raw_admission_prob if row.raw_admission_prob is not None else row.admission_prob)
    row.raw_admission_prob = raw
    row.admission_prob = calibrate_probability(raw, artifact, subject_group=subject_group)
    row.probability_is_calibrated = True
    row.probability_method = (
        "historical_beta_subject"
        if artifact.method == "beta_subject"
        else "historical_isotonic"
    )
    row.probability_calibration_year = artifact.calibration_year
    row.probability_hazard_scale = artifact.subsequent_choice_hazard_scale
    row.probability_calibration_source = artifact.source
    return row


@lru_cache(maxsize=4)
def load_probability_calibration(path_text: str) -> ProbabilityCalibrationArtifact | None:
    path = Path(path_text)
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ProbabilityCalibrationArtifact.model_validate(payload)
