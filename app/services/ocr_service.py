import re
from datetime import datetime
from typing import List, Dict, Any

class OCRService:
    """
    Interface service for OCR/NLP teammate integration.
    Contains fallback regex parsing rules for demo purposes and 
    provides a clean method hook where the OCR model payload can be passed.
    """

    @staticmethod
    def extract_metrics_from_text(text: str) -> List[Dict[str, Any]]:
        extracted = []
        now = datetime.utcnow()

        # Systolic & Diastolic BP regex (e.g. 138/88 mmHg or BP: 140/90)
        bp_match = re.search(r'(?:BP|Blood Pressure)?\s*:?\s*(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmHg)?', text, re.IGNORECASE)
        if bp_match:
            sys_val = float(bp_match.group(1))
            dia_val = float(bp_match.group(2))
            extracted.append({"metric_type": "BP_SYS", "value_numeric": sys_val, "unit": "mmHg", "recorded_date": now})
            extracted.append({"metric_type": "BP_DIA", "value_numeric": dia_val, "unit": "mmHg", "recorded_date": now})

        # Fasting Glucose regex (e.g. Glucose: 130 mg/dL)
        glucose_match = re.search(r'(?:Fasting Glucose|FBS|Blood Sugar)\s*:?\s*(\d{2,3})\s*(?:mg/dL)?', text, re.IGNORECASE)
        if glucose_match:
            extracted.append({"metric_type": "FASTING_GLUCOSE", "value_numeric": float(glucose_match.group(1)), "unit": "mg/dL", "recorded_date": now})

        # HbA1c regex (e.g. HbA1c: 6.8 %)
        hba1c_match = re.search(r'(?:HbA1c|Glycated Hemoglobin)\s*:?\s*(\d{1,2}(?:\.\d)?)\s*(?:%)?', text, re.IGNORECASE)
        if hba1c_match:
            extracted.append({"metric_type": "HBA1C", "value_numeric": float(hba1c_match.group(1)), "unit": "%", "recorded_date": now})

        # Hemoglobin regex (e.g. Hb: 13.5 g/dL)
        hb_match = re.search(r'(?:Hemoglobin|Hb)\s*:?\s*(\d{1,2}(?:\.\d)?)\s*(?:g/dL)?', text, re.IGNORECASE)
        if hb_match:
            extracted.append({"metric_type": "HEMOGLOBIN", "value_numeric": float(hb_match.group(1)), "unit": "g/dL", "recorded_date": now})

        return extracted
