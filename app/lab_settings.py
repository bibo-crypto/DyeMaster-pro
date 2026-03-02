"""Shared lab parameters storage for UI windows and PDF export."""
import json
import os

from app.config import USER_DATA_DIR


DEFAULT_LAB_SETTINGS = {
    "sample_g": 10.0,
    "volume_ml": 150.0,
}


def _settings_path() -> str:
    return os.path.join(USER_DATA_DIR, "lab_settings.json")


def _safe_positive_float(value, fallback: float) -> float:
    try:
        parsed = float(value)
        if parsed > 0:
            return parsed
    except (TypeError, ValueError):
        pass
    return fallback


def load_lab_settings() -> dict:
    sample_g = DEFAULT_LAB_SETTINGS["sample_g"]
    volume_ml = DEFAULT_LAB_SETTINGS["volume_ml"]

    path = _settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sample_g = _safe_positive_float(data.get("sample_g"), sample_g)
            volume_ml = _safe_positive_float(data.get("volume_ml"), volume_ml)
        except Exception:
            pass

    return {"sample_g": sample_g, "volume_ml": volume_ml}


def save_lab_settings(sample_g: float, volume_ml: float) -> dict:
    sample_g = _safe_positive_float(sample_g, DEFAULT_LAB_SETTINGS["sample_g"])
    volume_ml = _safe_positive_float(volume_ml, DEFAULT_LAB_SETTINGS["volume_ml"])
    payload = {"sample_g": sample_g, "volume_ml": volume_ml}

    os.makedirs(USER_DATA_DIR, exist_ok=True)
    with open(_settings_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)

    return payload
