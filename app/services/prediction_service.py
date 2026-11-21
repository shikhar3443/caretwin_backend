"""
CareTwin AI Health Twin - Mortality Risk Prediction Service.
Integrates Dheeraj's trained XGBoost model + scikit-learn preprocessing pipeline.
Can run in-process or connect to an external microservice.
"""

import os
import math
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import datetime as dt

log = logging.getLogger("prediction_service")

ASSETS_DIR = Path(__file__).resolve().parent.parent / "ml_assets"
MODEL_PATH = ASSETS_DIR / "xgboost_mortality_model.json"
PREP_PATH = ASSETS_DIR / "preprocessing.joblib"
MISSING = "__MISSING__"

LAB_UNITS = {
    "Hemoglobin": ("g/dL", 0.0, 25.0),
    "Creatinine": ("mg/dL", 0.0, 30.0),
    "Potassium": ("mEq/L", 0.5, 12.0),
    "Urea Nitrogen": ("mg/dL", 0.0, 300.0),
    "Sodium": ("mEq/L", 80.0, 200.0),
    "Glucose": ("mg/dL", 0.0, 2000.0),
    "Calcium, Total": ("mg/dL", 0.0, 25.0),
}

DISCLAIMER = (
    "This score comes from a statistical model trained on hospital "
    "admission data and is not a diagnosis or medical advice. It must not be used to make "
    "care decisions without review by a qualified clinician."
)

_ml_state: Dict[str, Any] = {}


def _get_ml_state():
    """Lazy loads model assets once when first needed."""
    if not _ml_state:
        try:
            import joblib
            import xgboost as xgb

            if not PREP_PATH.exists() or not MODEL_PATH.exists():
                log.warning("ML assets not found at %s", ASSETS_DIR)
                return None

            prep = joblib.load(str(PREP_PATH))
            booster = xgb.Booster()
            booster.load_model(str(MODEL_PATH))

            feature_names = prep["feature_names"]
            encoder = prep["categorical_encoder"]
            encoded_names = list(encoder.get_feature_names_out())

            _ml_state.update({
                "prep": prep,
                "booster": booster,
                "feature_names": feature_names,
                "index": {n: i for i, n in enumerate(feature_names)},
                "encoded_names": encoded_names,
                "categories": {
                    c: [str(v) for v in cats]
                    for c, cats in zip(prep["categorical_columns"], encoder.categories_)
                },
            })
            log.info("ML Mortality Model initialized successfully with %d features", len(feature_names))
        except Exception as e:
            log.error("Failed to load ML mortality model: %s", e)
            return None
    return _ml_state


def get_prediction_schema() -> Dict[str, Any]:
    state = _get_ml_state()
    if state:
        prep = state["prep"]
        return {
            "predictionWindowHours": prep.get("prediction_window_hours", 48),
            "labs": {k: {"unit": v[0], "min": v[1], "max": v[2]} for k, v in LAB_UNITS.items()},
            "categories": state.get("categories", {}),
        }
    return {
        "predictionWindowHours": 48,
        "labs": {k: {"unit": v[0], "min": v[1], "max": v[2]} for k, v in LAB_UNITS.items()},
        "categories": {
            "admission_type": ["EMERGENCY", "URGENT", "ELECTIVE", "OBSERVATION"],
            "admission_location": ["EMERGENCY ROOM", "PHYSICIAN REFERRAL", "TRANSFER FROM HOSPITAL", "CLINIC REFERRAL"],
            "insurance": ["Medicare", "Medicaid", "Private", "Self Pay", "Other"],
            "language": ["ENGLISH", "SPANISH", "OTHER"],
            "marital_status": ["MARRIED", "SINGLE", "WIDOWED", "DIVORCED"],
            "race": ["WHITE", "BLACK/AFRICAN AMERICAN", "ASIAN", "HISPANIC/LATINO", "OTHER"],
            "gender": ["M", "F"],
            "admission_hour": [str(i) for i in range(24)],
            "admission_month": [str(i) for i in range(1, 13)],
            "admission_weekday": [str(i) for i in range(7)],
        },
    }


def predict_mortality(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Runs prediction on patient data using the XGBoost booster."""
    import numpy as np
    import pandas as pd
    import xgboost as xgb

    state = _get_ml_state()
    if not state:
        raise RuntimeError("ML Mortality Model is not available.")

    prep = state["prep"]
    index = state["index"]
    vec = np.zeros(len(state["feature_names"]), dtype=np.float32)

    labs = input_data.get("labs") or {}

    # Validate and pack labs
    for lab in prep["lab_names"]:
        values = labs.get(lab) or []
        stats = {
            "mean": float(np.mean(values)) if values else np.nan,
            "last": float(values[-1]) if values else np.nan,
            "count": float(len(values)),
        }
        for stat in prep["lab_statistics"]:
            vec[index[f"{lab}__{stat}"]] = stats[stat]

    age = float(input_data.get("age", 40))
    vec[index["age"]] = age

    # Parse dates
    adm_date_str = input_data.get("admissionDate") or input_data.get("admission_date")
    adm_time_str = input_data.get("admissionTime") or input_data.get("admission_time")

    adm_date = None
    adm_time = None
    if adm_time_str:
        try:
            adm_time = dt.datetime.fromisoformat(str(adm_time_str).replace("Z", "+00:00"))
            adm_date = adm_time.date()
        except Exception:
            pass

    if not adm_date and adm_date_str:
        try:
            adm_date = dt.date.fromisoformat(str(adm_date_str))
        except Exception:
            pass

    if not adm_date:
        adm_date = dt.date.today()

    raw = {
        "admission_type": input_data.get("admissionType") or input_data.get("admission_type"),
        "admission_location": input_data.get("admissionLocation") or input_data.get("admission_location"),
        "insurance": input_data.get("insurance"),
        "language": input_data.get("language"),
        "marital_status": input_data.get("maritalStatus") or input_data.get("marital_status"),
        "race": input_data.get("race"),
        "gender": input_data.get("gender"),
        "admission_hour": str(adm_time.hour) if adm_time else None,
        "admission_month": str(adm_date.month),
        "admission_weekday": str(adm_date.weekday()),
    }

    row = {}
    for col in prep["categorical_columns"]:
        val = raw.get(col)
        val = MISSING if val is None or str(val).strip() == "" else str(val)
        if val == MISSING and MISSING not in state["categories"][col]:
            val = None
        row[col] = val

    frame = pd.DataFrame([row], columns=prep["categorical_columns"], dtype=object)
    encoded = prep["categorical_encoder"].transform(frame)
    dense = encoded.toarray()[0] if hasattr(encoded, "toarray") else np.asarray(encoded)[0]
    for name, value in zip(state["encoded_names"], dense):
        vec[index[name]] = value

    dmat = xgb.DMatrix(vec.reshape(1, -1), feature_names=None)
    prob = float(state["booster"].predict(dmat)[0])
    threshold = float(prep.get("decision_threshold", 0.15))
    flagged = prob >= threshold

    warnings = []
    if age < 18:
        warnings.append("Age is below 18; the model was trained on adult admissions.")
    if not labs:
        warnings.append("No lab values supplied; the score relies on demographics and admission details only.")
    elif len(labs) < len(prep["lab_names"]):
        warnings.append("Some labs were not supplied and were treated as not measured.")

    return {
        "probability": round(prob, 4),
        "threshold": round(threshold, 4),
        "flagged": flagged,
        "riskLevel": "elevated" if flagged else "lower",
        "predictionWindowHours": prep.get("prediction_window_hours", 48),
        "target": prep.get("target", "hospital_mortality"),
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }
