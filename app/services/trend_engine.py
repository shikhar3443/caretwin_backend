"""
trend_engine.py — Week 6: AI/ML Trend Detection & Risk Flag Engine.

Detects consecutive rising (or falling for Hemoglobin) measurement streaks
and persists graduated risk alerts to the trend_alerts table.

Risk graduation:
    LOW    → 3 consecutive rises/falls
    MEDIUM → 4 consecutive rises/falls  OR value crosses first clinical threshold
    HIGH   → 5+ consecutive, OR value crosses hard danger threshold (WHO/AHA)

De-duplication: an alert is skipped if an un-acknowledged alert for the same
metric already exists for this family member.
"""

from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.models import Measurement, TrendAlert, RiskLevel


# ---------------------------------------------------------------------------
# Clinical danger thresholds  (value_numeric in the DB's natural unit)
# ---------------------------------------------------------------------------
DANGER_THRESHOLDS: Dict[str, float] = {
    "BP_SYS":           180.0,   # mmHg  — hypertensive crisis  (HIGH)
    "BP_DIA":           120.0,   # mmHg  — hypertensive crisis  (HIGH)
    "FASTING_GLUCOSE":  200.0,   # mg/dL — clearly diabetic     (HIGH)
    "HBA1C":              8.0,   # %     — poor glycaemic ctrl  (HIGH)
    "HEMOGLOBIN":         8.0,   # g/dL  — severe anaemia below threshold (HIGH)
    "CHOLESTEROL":       240.0,  # mg/dL — high cholesterol     (HIGH)
}

# Moderate thresholds → MEDIUM risk even if streak is only 3
MODERATE_THRESHOLDS: Dict[str, float] = {
    "BP_SYS":           135.0,
    "BP_DIA":            90.0,
    "FASTING_GLUCOSE":  126.0,
    "HBA1C":              7.0,
    "CHOLESTEROL":       200.0,
}

# For these metrics a FALLING trend is the clinical danger signal
FALLING_RISK_METRICS = {"HEMOGLOBIN"}

METRIC_LABELS: Dict[str, str] = {
    "BP_SYS":          "Systolic Blood Pressure",
    "BP_DIA":          "Diastolic Blood Pressure",
    "FASTING_GLUCOSE": "Fasting Blood Sugar",
    "HBA1C":           "HbA1c",
    "HEMOGLOBIN":      "Hemoglobin",
    "CHOLESTEROL":     "Total Cholesterol",
}

UNITS: Dict[str, str] = {
    "BP_SYS":          "mmHg",
    "BP_DIA":          "mmHg",
    "FASTING_GLUCOSE": "mg/dL",
    "HBA1C":           "%",
    "HEMOGLOBIN":      "g/dL",
    "CHOLESTEROL":     "mg/dL",
}

# All metric types we want to monitor
MONITORED_METRICS = list(METRIC_LABELS.keys())


def _compute_trailing_streak(values: List[float], falling: bool) -> int:
    """
    Counts how many consecutive steps at the tail of `values` are
    strictly increasing (or decreasing for falling metrics).
    Returns 1 if the last two readings don't continue the trend.
    """
    if len(values) < 2:
        return 1
    streak = 1
    for i in range(len(values) - 1, 0, -1):
        if falling:
            if values[i] < values[i - 1]:
                streak += 1
            else:
                break
        else:
            if values[i] > values[i - 1]:
                streak += 1
            else:
                break
    return streak


def _risk_level(metric_type: str, streak: int, latest: float) -> RiskLevel:
    danger = DANGER_THRESHOLDS.get(metric_type)
    moderate = MODERATE_THRESHOLDS.get(metric_type)
    falling = metric_type in FALLING_RISK_METRICS

    # Hard danger threshold
    if danger is not None:
        crossed_danger = (latest <= danger) if falling else (latest >= danger)
        if crossed_danger or streak >= 5:
            return RiskLevel.HIGH

    # Moderate threshold or long streak
    if moderate is not None:
        crossed_mod = (latest <= moderate) if falling else (latest >= moderate)
        if crossed_mod or streak >= 4:
            return RiskLevel.MEDIUM

    return RiskLevel.LOW


def _build_message(metric_type: str, readings: List[Measurement],
                   streak: int, risk: RiskLevel) -> str:
    label = METRIC_LABELS.get(metric_type, metric_type)
    unit = UNITS.get(metric_type, "")
    direction = "falling" if metric_type in FALLING_RISK_METRICS else "rising"

    # Show last 3 values in the message (most recent streak segment)
    tail = readings[-min(streak, 3):]
    trend_str = " → ".join(f"{int(r.value_numeric) if r.value_numeric == int(r.value_numeric) else r.value_numeric}" for r in tail)

    sev_emoji = {"LOW": "⚠️", "MEDIUM": "🔶", "HIGH": "🔴"}.get(risk.value, "")
    sev_label = {"LOW": "Mild", "MEDIUM": "Moderate", "HIGH": "High"}.get(risk.value, "")

    return (
        f"{sev_emoji} {sev_label} Risk — {label} has been {direction} for "
        f"{streak} consecutive readings ({trend_str} {unit}). "
        f"Please review with your healthcare provider."
    )


class TrendDetectionEngine:
    """
    Week 6: AI/ML Trend Detection & Risk Flag Engine.

    evaluate_family_member_trends(db, family_member_id):
        - Queries all monitored metrics for the given family member.
        - Detects 3+ consecutive rising/falling streaks.
        - Writes graduated TrendAlert rows to DB (de-duplicated).
        - Returns list of newly created TrendAlert objects.
    """

    @staticmethod
    def evaluate_family_member_trends(
        db: Session, family_member_id: int, min_streak: int = 3
    ) -> List[TrendAlert]:
        alerts_created: List[TrendAlert] = []

        for metric_type in MONITORED_METRICS:
            readings: List[Measurement] = (
                db.query(Measurement)
                .filter(
                    Measurement.family_member_id == family_member_id,
                    Measurement.metric_type == metric_type,
                )
                .order_by(Measurement.recorded_date.asc())
                .all()
            )

            if len(readings) < min_streak:
                continue

            values = [r.value_numeric for r in readings]
            falling = metric_type in FALLING_RISK_METRICS
            streak = _compute_trailing_streak(values, falling)

            if streak < min_streak:
                continue

            latest = values[-1]
            risk = _risk_level(metric_type, streak, latest)
            msg = _build_message(metric_type, readings, streak, risk)

            # De-duplicate: skip if an unacknowledged alert already exists
            existing = (
                db.query(TrendAlert)
                .filter(
                    TrendAlert.family_member_id == family_member_id,
                    TrendAlert.metric_type == metric_type,
                    TrendAlert.is_acknowledged == False,  # noqa: E712
                )
                .first()
            )
            if existing:
                # Update message + risk level in-place if streak grew
                existing.risk_level = risk
                existing.message = msg
                continue

            alert = TrendAlert(
                family_member_id=family_member_id,
                metric_type=metric_type,
                risk_level=risk,
                message=msg,
            )
            db.add(alert)
            alerts_created.append(alert)

        db.commit()
        return alerts_created
