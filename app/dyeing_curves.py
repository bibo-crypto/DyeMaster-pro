"""
منطق تحديد طريقة الصباغة وبيانات الـ Curve
Dyeing Process Determination & Curve Data
Based on: Indanthren C Plus technical manual
"""
from typing import List, Dict, Tuple


# ─── Dye Classification Table (from book) ────────────────────────────────────
DYE_CLASSIFICATION = {
    "IW":         {"exhaustion_temp": 45,  "alkalinity": "medium", "electrolyte": True,  "remarks": "medium affinity"},
    "IN":         {"exhaustion_temp": 60,  "alkalinity": "high",   "electrolyte": False, "remarks": "high affinity"},
    "IN SPECIAL": {"exhaustion_temp": 60,  "alkalinity": "high",   "electrolyte": False, "remarks": "high affinity, start 80°C"},
    "SP":         {"exhaustion_temp": 80,  "alkalinity": "high",   "electrolyte": False, "remarks": "for black shades"},
    "SP*":        {"exhaustion_temp": 85,  "alkalinity": "medium", "electrolyte": False, "remarks": "sensitive to auxiliaries"},
}

# ─── Priority order for mixed recipes ────────────────────────────────────────
DYE_GROUP_PRIORITY = {
    "INDANTHREN IN SP":      8,
    "INDANTHREN IN SPECIAL": 8,
    "INDANTHREN SP":         7,
    "INDANTHREN SP*":        7,
    "INDANTHREN RS":         6,
    "INDANTHREN RRN":        5,
    "INDANTHREN BLACK":      7,
    "INDANTHREN ROSA R":     5,
    "INDANTHREN IN":         3,
    "INDANTHREN IW":         2,
    "REATTIVI CALDI":        1,
    "REATTIVI FREDDI":       1,
    "REATTIVI OLTRI":        1,
}


def _normalize_dye_type(dye_type: str) -> str:
    return dye_type.upper().strip()


def determine_process(selected_colors: List[Dict]) -> Tuple[str, str, str]:
    """
    Determine dyeing process from colors list.
    Returns: (process_key, process_name, process_description)
    """
    if not selected_colors:
        return ("ISODOS", "ISODOS® Process (IW)", "Standard Winch/Jet dyeing — exhaust at 45°C with Glauber's salt")

    type_totals: Dict[str, float] = {}
    for color in selected_colors:
        raw = _normalize_dye_type(color.get("dye_type", ""))
        type_totals[raw] = type_totals.get(raw, 0) + color.get("percentage", 0)

    dominant = max(
        type_totals.keys(),
        key=lambda t: (DYE_GROUP_PRIORITY.get(t, 0), type_totals[t])
    )

    if "ROSA" in dominant or "RRN" in dominant or "SP*" in dominant:
        return ("SP_STAR", "SP* Process — Pink R / Red Violet RRN",
                "80–90°C exhaustion — medium-high alkalinity — sensitive to auxiliaries")
    if "IN SP" in dominant or "IN SPECIAL" in dominant:
        return ("LEUCO_IN_SP", "RoDos® Process (IN Special)",
                "Pigmentation 80°C → caustic+Rongal linear dosing → hydrosulfite at end")
    if "BLACK" in dominant or ("SP" in dominant and "SP*" not in dominant):
        return ("SP_PROCESS", "SP Process — Black Shades",
                "Bath exhaustion 80°C — high alkalinity — no electrolyte")
    if "RS" in dominant:
        return ("RS_PROCESS", "RS Reduction Process",
                "Controlled reduction — avoid over-reduction — exhaust 50°C")
    if "IN" in dominant and "IW" not in dominant:
        return ("LEUCO_IN", "Leuco Process — Jig / Pad-Jig (IN)",
                "Bath exhaustion 60°C — high alkalinity — no electrolyte")
    if "IW" in dominant:
        return ("ISODOS", "ISODOS® Process (IW)",
                "Bath exhaustion 45°C — medium alkalinity — Glauber's salt required")
    if any(k in dominant for k in ["CALDI", "FREDDI", "OLTRI", "REATTIVI"]):
        pname = "Reactive Exhaust Dyeing"
        if "CALDI" in dominant:
            pname = "Reactive Caldi Process"
        elif "FREDDI" in dominant:
            pname = "Reactive Freddi Process"
        return ("REATTIVI", pname,
                "Salt + soda ash fixation — exhaust at 60°C")
    return ("ISODOS", "ISODOS® Process (IW)", "Standard Winch/Jet dyeing")


def get_curve_data(process_key: str, total_percentage: float = 1.0) -> Dict:
    dispatch = {
        "ISODOS":      _curve_isodos,
        "LEUCO_IN":    _curve_leuco_in,
        "LEUCO_IN_SP": _curve_leuco_in_sp,
        "SP_PROCESS":  _curve_sp,
        "SP_STAR":     _curve_sp_star,
        "RS_PROCESS":  _curve_rs,
        "PRE_PIGMENT": _curve_pre_pigment,
        "REATTIVI":    _curve_reattivi,
    }
    fn = dispatch.get(process_key, _curve_isodos)
    return fn(total_percentage)


def get_program_text(curve: Dict) -> List[Dict]:
    """
    Build step-by-step program text grouped by phase.
    Returns: [{phase, color, lines:[str]}, ...]
    """
    if not curve:
        return []
    phases_grouped = []
    for step in curve.get("steps", []):
        phase = step.get("phase", "")
        col   = step.get("color", "#999")
        st    = step["start_temp"]
        et    = step["end_temp"]
        dur   = step["end_time"] - step["start_time"]
        if dur <= 0:
            continue
        temp_str = f"{st}°C" if st == et else f"{st}°C  →  {et}°C"
        line = f"{temp_str}   for   {dur} min"
        phase_display = {
            "dyeing":     "Dyeing",
            "reduction":  "Reduction / Vatting",
            "oxidation":  "Oxidation",
            "soaping":    "Soaping",
            "rinse":      "Rinse",
            "neutralize": "Rinse / Neutralise",
        }.get(phase, phase.title())
        if phases_grouped and phases_grouped[-1]["phase"] == phase_display:
            phases_grouped[-1]["lines"].append(line)
        else:
            phases_grouped.append({"phase": phase_display, "color": col, "lines": [line]})
    return phases_grouped


# ─── CURVE DEFINITIONS ────────────────────────────────────────────────────────

def _curve_isodos(pct: float) -> Dict:
    """ISODOS® — IW — exhaust 45°C — electrolyte required"""
    return {
        "process_name": "ISODOS® Process (IW)",
        "total_time": 220, "max_temp": 100,
        "classification": {"group": "IW", "exhaustion_temp": "45°C",
                           "alkalinity": "Medium", "electrolyte": "Yes — Glauber's salt required"},
        "steps": [
            {"label": "Bath Prep\n& Pigmentation", "start_time": 0,   "end_time": 20,
             "start_temp": 80, "end_temp": 80,  "color": "#2196F3", "phase": "dyeing"},
            {"label": "Linear Dye\nDosing",         "start_time": 20,  "end_time": 40,
             "start_temp": 80, "end_temp": 80,  "color": "#1565C0", "phase": "dyeing"},
            {"label": "Vatting\n(Reduction)",        "start_time": 40,  "end_time": 70,
             "start_temp": 80, "end_temp": 45,  "color": "#9C27B0", "phase": "reduction"},
            {"label": "Leuco\nAbsorption",           "start_time": 70,  "end_time": 110,
             "start_temp": 45, "end_temp": 45,  "color": "#673AB7", "phase": "reduction"},
            {"label": "Oxidation",                   "start_time": 110, "end_time": 135,
             "start_temp": 45, "end_temp": 55,  "color": "#FF9800", "phase": "oxidation"},
            {"label": "",                            "start_time": 135, "end_time": 150,
             "start_temp": 55, "end_temp": 40,  "color": "#FF9800", "phase": "oxidation"},
            {"label": "Soaping",                     "start_time": 150, "end_time": 175,
             "start_temp": 40, "end_temp": 95,  "color": "#F44336", "phase": "soaping"},
            {"label": "",                            "start_time": 175, "end_time": 195,
             "start_temp": 95, "end_temp": 95,  "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse &\nNeutralise",         "start_time": 195, "end_time": 220,
             "start_temp": 95, "end_temp": 40,  "color": "#4CAF50", "phase": "rinse"},
        ],
        "annotations": [
            {"number": 1, "time": 10, "temp": 85, "chemicals": [
                "1 g/l   Sera Foam M-MO", "2 g/l   Sera Sperse C-SN",
                "1 g/l   Sera Quest C-PX", "3–5 g/l Sera Lube M-CF",
                "Glauber's salt (electrolyte — see recipe)",
                "2/3  Caustic soda (Optidye CI)", "1–3 g/l Sera Gal C-VP",
                "1/3  Caustic soda", "... g/l Hydrosulfite (Optidye CI)",
                "3 g/l   Glucose (sensitive dyes only)",
            ]},
            {"number": 2, "time": 30, "temp": 85, "chemicals": [
                "...%  Indanthren IW dye", "(linear dosing into bath over 20 min)",
            ]},
            {"number": 3, "time": 90, "temp": 50, "chemicals": ["10–15 g/l  Sera Con M-LU"]},
            {"number": 4, "time": 120, "temp": 52, "chemicals": ["2–4 ml/l  Hydrogen peroxide 50%"]},
            {"number": 5, "time": 162, "temp": 100, "chemicals": ["1 g/l  Sera Sperse C-SN"]},
            {"number": 6, "time": 207, "temp": 45, "chemicals": ["Rinse and neutralise pH 6–7"]},
        ],
        "notes": [
            "IW group: medium affinity — bath exhaustion at 45°C",
            "Glauber's salt (electrolyte) REQUIRED — improves bath exhaustion",
            "Dye metered linearly into bath (ISODOS method)",
            "Hydrosulfite: use Optidye CI grade",
            "Glucose (3 g/l) only for dyes sensitive to over-reduction",
        ]
    }


def _curve_leuco_in(pct: float) -> Dict:
    """Leuco process — IN — exhaust 60°C — no electrolyte"""
    return {
        "process_name": "Leuco Process — Jig / Pad-Jig (IN)",
        "total_time": 185, "max_temp": 130,
        "classification": {"group": "IN", "exhaustion_temp": "60°C",
                           "alkalinity": "High", "electrolyte": "No"},
        "steps": [
            {"label": "Dyeing\n(Vatted)",    "start_time": 0,   "end_time": 40,
             "start_temp": 105, "end_temp": 105, "color": "#2196F3", "phase": "dyeing"},
            {"label": "",                    "start_time": 40,  "end_time": 55,
             "start_temp": 105, "end_temp": 30,  "color": "#2196F3", "phase": "dyeing"},
            {"label": "Red. Rinse",          "start_time": 55,  "end_time": 70,
             "start_temp": 30,  "end_temp": 30,  "color": "#9C27B0", "phase": "reduction"},
            {"label": "Oxidation",           "start_time": 70,  "end_time": 90,
             "start_temp": 20,  "end_temp": 50,  "color": "#FF9800", "phase": "oxidation"},
            {"label": "",                    "start_time": 90,  "end_time": 100,
             "start_temp": 50,  "end_temp": 20,  "color": "#FF9800", "phase": "oxidation"},
            {"label": "Remove\nSuperficial", "start_time": 100, "end_time": 115,
             "start_temp": 20,  "end_temp": 20,  "color": "#795548", "phase": "soaping"},
            {"label": "Soaping",             "start_time": 115, "end_time": 150,
             "start_temp": 20,  "end_temp": 60,  "color": "#F44336", "phase": "soaping"},
            {"label": "",                    "start_time": 150, "end_time": 165,
             "start_temp": 60,  "end_temp": 60,  "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse",               "start_time": 165, "end_time": 175,
             "start_temp": 60,  "end_temp": 40,  "color": "#2196F3", "phase": "rinse"},
            {"label": "Rinse /\nNeutralise", "start_time": 175, "end_time": 185,
             "start_temp": 40,  "end_temp": 40,  "color": "#4CAF50", "phase": "neutralize"},
        ],
        "annotations": [
            {"number": 1, "time": 20, "temp": 112, "chemicals": [
                "2 g/l   Sera Sperse C-SN", "1 g/l   Sera Quest C-PX",
                "1 g/l   Sera Sperse M-IS", "...%    Indanthren IN dyes",
                "... ml/l Caustic soda (Optidye CI)", "1–3 g/l Sera Gal C-VP",
                "3 g/l   Glucose (sensitive dyes)", "... g/l Hydrosulfite (Optidye CI)",
            ]},
            {"number": 2, "time": 63, "temp": 35, "chemicals": [
                "2–3 ml/l  Caustic soda 38°Bé", "2–3 g/l   Hydrosulfite",
                "1 g/l     Sera Sperse M-IS",
            ]},
            {"number": 3, "time": 80, "temp": 40, "chemicals": [
                "10 g/l   Sera Con M-LU", "2 ml/l   Hydrogen peroxide 50%",
            ]},
            {"number": 4, "time": 108, "temp": 25, "chemicals": [
                "For dyeings > 3%:", "0.3 g/l  Sera Sperse M-VP",
            ]},
            {"number": 5, "time": 132, "temp": 65, "chemicals": ["1 g/l  Sera Sperse C-SN"]},
            {"number": 6, "time": 180, "temp": 45, "chemicals": ["Neutralise pH 7"]},
        ],
        "notes": [
            "IN group: high affinity — bath exhaustion at 60°C",
            "No electrolyte required",
            "Primarily for dark shades — dyes vatted in long liquor",
            "High temp (>100°C) ensures penetration at crossover points",
        ]
    }


def _curve_leuco_in_sp(pct: float) -> Dict:
    """RoDos® — IN Special — 80→60°C — no electrolyte — strictest"""
    return {
        "process_name": "RoDos® Process (IN Special)",
        "total_time": 200, "max_temp": 130,
        "classification": {"group": "IN Special", "exhaustion_temp": "80°C → 60°C",
                           "alkalinity": "High", "electrolyte": "No"},
        "steps": [
            {"label": "Pre-pigmentation\n80°C — 10 min",  "start_time": 0,   "end_time": 15,
             "start_temp": 80, "end_temp": 80, "color": "#2196F3", "phase": "dyeing"},
            {"label": "Caustic+Rongal\nLinear 20 min",    "start_time": 15,  "end_time": 35,
             "start_temp": 80, "end_temp": 80, "color": "#1565C0", "phase": "dyeing"},
            {"label": "Add Hydrosulfite\n(end of dosing)", "start_time": 35,  "end_time": 50,
             "start_temp": 80, "end_temp": 80, "color": "#9C27B0", "phase": "reduction"},
            {"label": "Exhaust\nDyeing",                   "start_time": 50,  "end_time": 100,
             "start_temp": 80, "end_temp": 60, "color": "#673AB7", "phase": "reduction"},
            {"label": "Oxidation",                         "start_time": 100, "end_time": 130,
             "start_temp": 50, "end_temp": 60, "color": "#FF9800", "phase": "oxidation"},
            {"label": "",                                  "start_time": 130, "end_time": 145,
             "start_temp": 60, "end_temp": 40, "color": "#FF9800", "phase": "oxidation"},
            {"label": "Soaping",                           "start_time": 145, "end_time": 175,
             "start_temp": 40, "end_temp": 95, "color": "#F44336", "phase": "soaping"},
            {"label": "",                                  "start_time": 175, "end_time": 185,
             "start_temp": 95, "end_temp": 95, "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse &\nNeutralise",               "start_time": 185, "end_time": 200,
             "start_temp": 95, "end_temp": 40, "color": "#4CAF50", "phase": "rinse"},
        ],
        "annotations": [
            {"number": 1, "time": 7,   "temp": 86, "chemicals": [
                "Pigmentation at 80°C — 10 min", "...%  IN Special dyes",
            ]},
            {"number": 2, "time": 25,  "temp": 86, "chemicals": [
                "Caustic soda + Rongal® 5242 (BASF AG)",
                "Added linearly over 20 minutes",
                "→ delays reduction, slows bath exhaustion",
            ]},
            {"number": 3, "time": 42,  "temp": 86, "chemicals": [
                "2–4 g/l  Hydrosulfite",
                "Added at END of dosing step only",
            ]},
            {"number": 4, "time": 115, "temp": 55, "chemicals": ["2–4 ml/l  Hydrogen peroxide 50%"]},
            {"number": 5, "time": 160, "temp": 100, "chemicals": ["1–2 g/l  Soaping agent"]},
        ],
        "notes": [
            "IN Special: high affinity — exhaustion 80°C → 60°C",
            "RoDos® method: pigmentation 10 min at 80°C FIRST",
            "Caustic + Rongal® 5242 added linearly (20 min)",
            "Hydrosulfite ONLY at end of dosing step",
            "Strictest conditions — use exclusively for IN Special dyes",
        ]
    }


def _curve_sp(pct: float) -> Dict:
    """SP — Black shades — exhaust 80°C — no electrolyte"""
    return {
        "process_name": "SP Process — Black Shades",
        "total_time": 190, "max_temp": 130,
        "classification": {"group": "SP", "exhaustion_temp": "80°C",
                           "alkalinity": "High", "electrolyte": "No"},
        "steps": [
            {"label": "Pigmentation\n80°C",  "start_time": 0,   "end_time": 20,
             "start_temp": 80, "end_temp": 80, "color": "#2196F3", "phase": "dyeing"},
            {"label": "Vatting",             "start_time": 20,  "end_time": 55,
             "start_temp": 80, "end_temp": 80, "color": "#9C27B0", "phase": "reduction"},
            {"label": "Exhaust\nDyeing",     "start_time": 55,  "end_time": 100,
             "start_temp": 80, "end_temp": 60, "color": "#673AB7", "phase": "reduction"},
            {"label": "Oxidation",           "start_time": 100, "end_time": 130,
             "start_temp": 50, "end_temp": 60, "color": "#FF9800", "phase": "oxidation"},
            {"label": "",                    "start_time": 130, "end_time": 145,
             "start_temp": 60, "end_temp": 40, "color": "#FF9800", "phase": "oxidation"},
            {"label": "Soaping",             "start_time": 145, "end_time": 170,
             "start_temp": 40, "end_temp": 95, "color": "#F44336", "phase": "soaping"},
            {"label": "",                    "start_time": 170, "end_time": 180,
             "start_temp": 95, "end_temp": 95, "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse &\nNeutralise", "start_time": 180, "end_time": 190,
             "start_temp": 95, "end_temp": 40, "color": "#4CAF50", "phase": "rinse"},
        ],
        "annotations": [
            {"number": 1, "time": 10, "temp": 86, "chemicals": [
                "...%  SP / Black dyes", "High alkalinity caustic soda",
                "Hydrosulfite", "Leveling agent",
            ]},
            {"number": 2, "time": 115, "temp": 56, "chemicals": [
                "2–4 ml/l  H\u2082O\u2082 50%", "10 g/l    Sera Con M-LU",
            ]},
            {"number": 3, "time": 157, "temp": 100, "chemicals": ["1–2 g/l  Soaping agent"]},
            {"number": 4, "time": 185, "temp": 45, "chemicals": ["Neutralise to pH 7"]},
        ],
        "notes": [
            "SP group: for black shades only — exhaustion at 80°C",
            "High alkalinity required — no electrolyte",
            "Ensure complete oxidation before soaping",
        ]
    }


def _curve_sp_star(pct: float) -> Dict:
    """SP* — Brilliant Pink R / Red Violet RRN — 80-90°C — sensitive"""
    return {
        "process_name": "SP* Process — Pink R / Red Violet RRN",
        "total_time": 185, "max_temp": 130,
        "classification": {"group": "SP*", "exhaustion_temp": "80–90°C",
                           "alkalinity": "Medium to High", "electrolyte": "No"},
        "steps": [
            {"label": "Pigmentation\n80°C",  "start_time": 0,   "end_time": 20,
             "start_temp": 80, "end_temp": 85, "color": "#E91E63", "phase": "dyeing"},
            {"label": "Vatting",             "start_time": 20,  "end_time": 50,
             "start_temp": 85, "end_temp": 85, "color": "#9C27B0", "phase": "reduction"},
            {"label": "Exhaust\nDyeing",     "start_time": 50,  "end_time": 95,
             "start_temp": 85, "end_temp": 60, "color": "#673AB7", "phase": "reduction"},
            {"label": "Oxidation",           "start_time": 95,  "end_time": 120,
             "start_temp": 50, "end_temp": 55, "color": "#FF9800", "phase": "oxidation"},
            {"label": "",                    "start_time": 120, "end_time": 133,
             "start_temp": 55, "end_temp": 40, "color": "#FF9800", "phase": "oxidation"},
            {"label": "Soaping",             "start_time": 133, "end_time": 160,
             "start_temp": 40, "end_temp": 90, "color": "#F44336", "phase": "soaping"},
            {"label": "",                    "start_time": 160, "end_time": 173,
             "start_temp": 90, "end_temp": 90, "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse &\nNeutralise", "start_time": 173, "end_time": 185,
             "start_temp": 90, "end_temp": 40, "color": "#4CAF50", "phase": "rinse"},
        ],
        "annotations": [
            {"number": 1, "time": 10, "temp": 86, "chemicals": [
                "Indanthren Brilliant Pink R  OR",
                "Indanthren Red Violet RRN",
                "Medium-high caustic soda", "Hydrosulfite (controlled)",
                "\u26a0  Sensitive to some auxiliaries — check compatibility",
            ]},
            {"number": 2, "time": 107, "temp": 56, "chemicals": [
                "2–3 ml/l  H\u2082O\u2082 50%", "8–10 g/l  Sera Con M-LU",
            ]},
            {"number": 3, "time": 146, "temp": 95, "chemicals": ["1 g/l  Soaping agent"]},
        ],
        "notes": [
            "SP* group: Brilliant Pink R + Red Violet RRN ONLY",
            "Exhaustion 80–90°C — medium to high alkalinity",
            "\u26a0  Check auxiliaries compatibility before use",
            "No electrolyte required",
        ]
    }


def _curve_rs(pct: float) -> Dict:
    """RS — controlled reduction — exhaust 50°C"""
    return {
        "process_name": "RS Reduction Process",
        "total_time": 180, "max_temp": 120,
        "classification": {"group": "RS", "exhaustion_temp": "50°C",
                           "alkalinity": "Medium", "electrolyte": "No"},
        "steps": [
            {"label": "Pre-wetting\n& Pigmentation", "start_time": 0,   "end_time": 25,
             "start_temp": 60, "end_temp": 60, "color": "#2196F3", "phase": "dyeing"},
            {"label": "Vatting",                     "start_time": 25,  "end_time": 60,
             "start_temp": 60, "end_temp": 50, "color": "#9C27B0", "phase": "reduction"},
            {"label": "Absorption",                  "start_time": 60,  "end_time": 100,
             "start_temp": 50, "end_temp": 50, "color": "#673AB7", "phase": "reduction"},
            {"label": "Oxidation",                   "start_time": 100, "end_time": 130,
             "start_temp": 50, "end_temp": 55, "color": "#FF9800", "phase": "oxidation"},
            {"label": "",                            "start_time": 130, "end_time": 140,
             "start_temp": 55, "end_temp": 40, "color": "#FF9800", "phase": "oxidation"},
            {"label": "Soaping",                     "start_time": 140, "end_time": 165,
             "start_temp": 40, "end_temp": 90, "color": "#F44336", "phase": "soaping"},
            {"label": "",                            "start_time": 165, "end_time": 175,
             "start_temp": 90, "end_temp": 90, "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse",                       "start_time": 175, "end_time": 180,
             "start_temp": 90, "end_temp": 40, "color": "#4CAF50", "phase": "rinse"},
        ],
        "annotations": [
            {"number": 1, "time": 12, "temp": 66, "chemicals": [
                "...%  RS group dyes", "Caustic soda",
                "Hydrosulfite (RS grade)", "Leveling agent",
                "3 g/l  Glucose (reduction buffer)",
            ]},
            {"number": 2, "time": 115, "temp": 56, "chemicals": [
                "2–3 ml/l  H\u2082O\u2082 50%", "8–10 g/l  Sera Con M-LU",
            ]},
            {"number": 3, "time": 152, "temp": 95, "chemicals": ["1 g/l  Soaping agent"]},
        ],
        "notes": [
            "RS dyes: controlled reduction — DO NOT over-reduce",
            "Vatting temperature max 50°C — do not exceed",
            "Glucose (3 g/l) acts as reduction buffer",
        ]
    }


def _curve_pre_pigment(pct: float) -> Dict:
    """Pre-pigmentation — Yarn dyeing — book section 2.1.1"""
    end_exhaust = 50 if pct > 2 else 60
    return {
        "process_name": "Pre-pigmentation Process (Yarn Dyeing)",
        "total_time": 180, "max_temp": 120,
        "classification": {"group": "IW / IN", "exhaustion_temp": f"{end_exhaust}°C",
                           "alkalinity": "Medium to High", "electrolyte": "Depends on dye group"},
        "steps": [
            {"label": "Pigmentation\n80–90°C",  "start_time": 0,   "end_time": 30,
             "start_temp": 80,          "end_temp": 90,          "color": "#2196F3", "phase": "dyeing"},
            {"label": "Vatting\n80°C",           "start_time": 30,  "end_time": 55,
             "start_temp": 90,          "end_temp": 80,          "color": "#1565C0", "phase": "dyeing"},
            {"label": "Reduction\n→ exhaustion",    "start_time": 55,  "end_time": 90,
             "start_temp": 80,          "end_temp": end_exhaust, "color": "#9C27B0", "phase": "reduction"},
            {"label": "Red. Rinse\n> 1%",         "start_time": 90,  "end_time": 105,
             "start_temp": end_exhaust, "end_temp": end_exhaust, "color": "#7B1FA2", "phase": "reduction"},
            {"label": "Oxidation",               "start_time": 105, "end_time": 125,
             "start_temp": 20,          "end_temp": 50,          "color": "#FF9800", "phase": "oxidation"},
            {"label": "",                        "start_time": 125, "end_time": 135,
             "start_temp": 50,          "end_temp": 20,          "color": "#FF9800", "phase": "oxidation"},
            {"label": "Soaping",                 "start_time": 135, "end_time": 158,
             "start_temp": 20,          "end_temp": 60,          "color": "#F44336", "phase": "soaping"},
            {"label": "",                        "start_time": 158, "end_time": 165,
             "start_temp": 60,          "end_temp": 60,          "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse /\nNeutralise",     "start_time": 165, "end_time": 180,
             "start_temp": 60,          "end_temp": 40,          "color": "#4CAF50", "phase": "neutralize"},
        ],
        "annotations": [
            {"number": 1, "time": 15, "temp": 86, "chemicals": [
                "2 g/l   Sera Sperse C-SN", "1 g/l   Sera Quest C-PX",
                "1 g/l   Sera Sperse M-IS", "3 g/l   Sera Lube M-CF",
                "1 g/l   Sera Gal C-VP", "... g/l Hydrosulfite (Optidye CI)",
                "Caustic soda (Optidye CI) — linear dosing", "3 g/l   Glucose (sensitive dyes only)",
            ]},
            {"number": 2, "time": 42, "temp": 86, "chemicals": [
                "... ml/l  Caustic soda (Optidye CI)", "1–3 g/l   Sera Gal C-VP",
                "3 g/l     Glucose (sensitive dyes)", "... g/l   Hydrosulfite (Optidye CI)",
            ]},
            {"number": 3, "time": 98, "temp": end_exhaust + 5, "chemicals": [
                "For dyeings > 1%:", "2–3 ml/l  Caustic soda 38°Bé",
                "2–3 g/l   Hydrosulfite", "1 g/l     Sera Sperse M-IS",
            ]},
            {"number": 4, "time": 115, "temp": 40, "chemicals": [
                "10 g/l   Sera Con M-LU", "2 ml/l   Hydrogen peroxide 50%",
            ]},
            {"number": 5, "time": 146, "temp": 65, "chemicals": ["1 g/l  Sera Sperse C-SN"]},
            {"number": 6, "time": 172, "temp": 45, "chemicals": ["Neutralise pH 7"]},
        ],
        "notes": [
            "Pre-pigmentation: dyestuff is partly deposited on the fibre in non-substantive pigment form",
            "More uniform deposition at high temperatures (80–90°C) because of better liquor flow through yarn",
            "Dye is vatted at 80°C", 
            "To improve bath exhaustion, reduce the dyeing temperature to 60°C or 50°C near the end",
            "Indanthren dyes are reduced to soluble leuco form with alkali and hydrosulfite, then oxidized back to insoluble dye",
        ]
    }


def _curve_reattivi(pct: float) -> Dict:
    """Reactive dyes exhaust"""
    return {
        "process_name": "Reactive Exhaust Dyeing",
        "total_time": 140, "max_temp": 100,
        "classification": {"group": "Reactive", "exhaustion_temp": "60°C",
                           "alkalinity": "Alkaline (soda ash)", "electrolyte": "Yes — salt required"},
        "steps": [
            {"label": "Salt &\nLeveling",         "start_time": 0,   "end_time": 20,
             "start_temp": 40, "end_temp": 60, "color": "#2196F3", "phase": "dyeing"},
            {"label": "Dye Dosing\n& Absorption",  "start_time": 20,  "end_time": 50,
             "start_temp": 60, "end_temp": 60, "color": "#1565C0", "phase": "dyeing"},
            {"label": "Soda Ash\n(Fixation)",      "start_time": 50,  "end_time": 80,
             "start_temp": 60, "end_temp": 60, "color": "#9C27B0", "phase": "reduction"},
            {"label": "Soaping",                   "start_time": 80,  "end_time": 110,
             "start_temp": 60, "end_temp": 95, "color": "#F44336", "phase": "soaping"},
            {"label": "",                          "start_time": 110, "end_time": 120,
             "start_temp": 95, "end_temp": 95, "color": "#F44336", "phase": "soaping"},
            {"label": "Rinse &\nNeutralise",       "start_time": 120, "end_time": 140,
             "start_temp": 95, "end_temp": 40, "color": "#4CAF50", "phase": "rinse"},
        ],
        "annotations": [
            {"number": 1, "time": 10, "temp": 50, "chemicals": [
                "SOLFATO SODICO  (see recipe formula)", "Wetting / leveling agent",
            ]},
            {"number": 2, "time": 35, "temp": 65, "chemicals": ["...%  Reactive dyes"]},
            {"number": 3, "time": 65, "temp": 65, "chemicals": [
                "SODIO CARBONATO  (see recipe formula)",
                "SODA CAUSTICA    (see recipe formula)",
            ]},
            {"number": 4, "time": 95, "temp": 100, "chemicals": ["Soaping agent  1–2 g/l"]},
            {"number": 5, "time": 130, "temp": 45, "chemicals": ["Acetic acid to pH 6–7"]},
        ],
        "notes": [
            "Salt added first — enhances dye exhaustion",
            "Soda ash added after initial absorption for fixation",
            "After soaping check pH — neutralise with acetic acid",
        ]
    }


def get_phase_legend() -> List[Dict]:
    return [
        {"label": "Dyeing",        "color": "#2196F3"},
        {"label": "Reduction",     "color": "#9C27B0"},
        {"label": "Oxidation",     "color": "#FF9800"},
        {"label": "Soaping",       "color": "#F44336"},
        {"label": "Rinse / Neut.", "color": "#4CAF50"},
    ]
