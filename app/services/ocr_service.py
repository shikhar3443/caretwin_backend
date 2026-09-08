import re
from datetime import datetime
from typing import List, Dict, Any, Optional

class OCRService:
    """
    Medical NLP and OCR Parsing Service.
    Extracts structured clinical metrics (BP, Fasting/Random Glucose, HbA1c, Hemoglobin, Cholesterol)
    from raw text or OCR JSON payloads. Designed for easy teammate integration.
    """

    @staticmethod
    def extract_metrics_from_text(text: str, recorded_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        extracted = []
        doc_date = recorded_date or datetime.utcnow()

        # 1. Systolic & Diastolic Blood Pressure (e.g. "BP: 138/88 mmHg", "140/90", "Blood Pressure - 128 / 82")
        bp_matches = re.finditer(
            r'(?:BP|Blood\s*Pressure)?\s*:?\s*(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmHg)?',
            text,
            re.IGNORECASE
        )
        for bp_match in bp_matches:
            sys_val = float(bp_match.group(1))
            dia_val = float(bp_match.group(2))
            # Basic sanity range check for human BP values
            if 60 <= sys_val <= 250 and 40 <= dia_val <= 150:
                extracted.append({"metric_type": "BP_SYS", "value_numeric": sys_val, "unit": "mmHg", "recorded_date": doc_date})
                extracted.append({"metric_type": "BP_DIA", "value_numeric": dia_val, "unit": "mmHg", "recorded_date": doc_date})
                break  # Take primary match

        # 2. Fasting Blood Glucose (e.g. "Fasting Glucose: 126 mg/dL", "FBS: 110", "Fasting Blood Sugar 135")
        fbs_match = re.search(
            r'(?:Fasting\s*(?:Blood)?\s*(?:Glucose|Sugar)|FBS)\s*:?\s*(\d{2,3}(?:\.\d)?)\s*(?:mg/dL)?',
            text,
            re.IGNORECASE
        )
        if fbs_match:
            extracted.append({
                "metric_type": "FASTING_GLUCOSE",
                "value_numeric": float(fbs_match.group(1)),
                "unit": "mg/dL",
                "recorded_date": doc_date
            })

        # 3. HbA1c / Glycated Hemoglobin (e.g. "HbA1c: 6.8%", "Glycated Hemoglobin 7.1")
        hba1c_match = re.search(
            r'(?:HbA1c|Glycated\s*Hemoglobin)\s*:?\s*(\d{1,2}(?:\.\d)?)\s*(?:%)?',
            text,
            re.IGNORECASE
        )
        if hba1c_match:
            extracted.append({
                "metric_type": "HBA1C",
                "value_numeric": float(hba1c_match.group(1)),
                "unit": "%",
                "recorded_date": doc_date
            })

        # 4. Hemoglobin (e.g. "Hemoglobin: 13.5 g/dL", "Hb - 14.2")
        hb_match = re.search(
            r'(?:Hemoglobin|Hb)\s*:?\s*(\d{1,2}(?:\.\d)?)\s*(?:g/dL)?',
            text,
            re.IGNORECASE
        )
        if hb_match and not hba1c_match:  # Ensure not confused with HbA1c
            extracted.append({
                "metric_type": "HEMOGLOBIN",
                "value_numeric": float(hb_match.group(1)),
                "unit": "g/dL",
                "recorded_date": doc_date
            })

        # 5. Total Cholesterol (e.g. "Total Cholesterol: 210 mg/dL", "Cholesterol 195")
        chol_match = re.search(
            r'(?:Total\s*)?Cholesterol\s*:?\s*(\d{2,3}(?:\.\d)?)\s*(?:mg/dL)?',
            text,
            re.IGNORECASE
        )
        if chol_match:
            extracted.append({
                "metric_type": "CHOLESTEROL",
                "value_numeric": float(chol_match.group(1)),
                "unit": "mg/dL",
                "recorded_date": doc_date
            })

        return extracted
