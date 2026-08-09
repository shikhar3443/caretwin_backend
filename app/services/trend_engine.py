from typing import List
from sqlalchemy.orm import Session
from app.models.models import Measurement, TrendAlert, RiskLevel

class TrendDetectionEngine:
    """
    ML/Rules Trend Engine for Hypertension and Diabetes tracking.
    Evaluates chronological measurements and generates safe, non-diagnostic alerts.
    """

    @staticmethod
    def evaluate_family_member_trends(db: Session, family_member_id: int) -> List[TrendAlert]:
        alerts_created = []

        # 1. Evaluate Systolic Blood Pressure Trend
        bp_sys_records = (
            db.query(Measurement)
            .filter(Measurement.family_member_id == family_member_id, Measurement.metric_type == "BP_SYS")
            .order_by(Measurement.recorded_date.asc())
            .all()
        )

        if len(bp_sys_records) >= 3:
            recent_3 = bp_sys_records[-3:]
            v1, v2, v3 = recent_3[0].value_numeric, recent_3[1].value_numeric, recent_3[2].value_numeric
            if v1 < v2 < v3 and v3 >= 135:
                msg = f"Notice: Your Systolic Blood Pressure has risen consistently across your last 3 recorded visits ({int(v1)} -> {int(v2)} -> {int(v3)} mmHg). Consider discussing this trend with your physician."
                
                # Avoid duplicate alert if existing active alert with same message
                existing = db.query(TrendAlert).filter(
                    TrendAlert.family_member_id == family_member_id,
                    TrendAlert.metric_type == "BP_SYS",
                    TrendAlert.is_acknowledged == False
                ).first()

                if not existing:
                    alert = TrendAlert(
                        family_member_id=family_member_id,
                        metric_type="BP_SYS",
                        risk_level=RiskLevel.MEDIUM,
                        message=msg
                    )
                    db.add(alert)
                    alerts_created.append(alert)

        # 2. Evaluate Fasting Blood Glucose Trend
        glucose_records = (
            db.query(Measurement)
            .filter(Measurement.family_member_id == family_member_id, Measurement.metric_type == "FASTING_GLUCOSE")
            .order_by(Measurement.recorded_date.asc())
            .all()
        )

        if len(glucose_records) >= 3:
            recent_3 = glucose_records[-3:]
            g1, g2, g3 = recent_3[0].value_numeric, recent_3[1].value_numeric, recent_3[2].value_numeric
            if g1 < g2 < g3 and g3 >= 126:
                msg = f"Notice: Fasting Blood Glucose levels show a continuous upward trend across 3 visits ({int(g1)} -> {int(g2)} -> {int(g3)} mg/dL). Share this trend with your healthcare provider."
                
                existing = db.query(TrendAlert).filter(
                    TrendAlert.family_member_id == family_member_id,
                    TrendAlert.metric_type == "FASTING_GLUCOSE",
                    TrendAlert.is_acknowledged == False
                ).first()

                if not existing:
                    alert = TrendAlert(
                        family_member_id=family_member_id,
                        metric_type="FASTING_GLUCOSE",
                        risk_level=RiskLevel.HIGH if g3 > 140 else RiskLevel.MEDIUM,
                        message=msg
                    )
                    db.add(alert)
                    alerts_created.append(alert)

        db.commit()
        return alerts_created
