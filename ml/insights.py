# ml/insights.py

"""
Domain-based parameter classification for groundwater quality.

This is ONLY for UI insights (progress bars / gauges), not for ML.
"""

def _get_thresholds():
    """
    Returns: parameter_name -> (low_limit, high_limit)
    Based on realistic groundwater / drinking water guidelines.
    """
    return {
        "pH": (6.5, 8.5),
        "Electrical_Conductivity": (250, 750),
        "Total_Dissolved_Solids": (300, 900),
        "Carbonate": (0, 30),
        "Bicarbonate": (50, 200),
        "Chloride": (0, 250),
        "Fluoride": (0, 1.0),
        "Nitrate": (0, 45),
        "Sulfate": (0, 200),
        "Sodium": (0, 60),
        "Calcium": (0, 75),
        "Magnesium": (0, 50),
        "Total_Hardness": (0, 300),
        "Sodium_Adsorption_Ratio": (0, 10),
        "Residual_Sodium_Carbonate": (0, 2.5),
    }


def classify_param(name: str, value: float) -> dict:
    """
    Classify parameter into Low / Normal / High using domain thresholds.

    Returns dict:
    {
        "status": "Low" | "Normal" | "High",
        "color": "warning" | "success" | "danger",
        "percent": 0–100 (for the gauge)
    }
    """

    thresholds = _get_thresholds()
    low_limit, high_limit = thresholds.get(name, (0.0, 1.0))

    # -----------------------------
    # 1. Determine Status
    # -----------------------------
    if value < low_limit:
        status = "Low"
        color = "warning"
    elif low_limit <= value <= high_limit:
        status = "Normal"
        color = "success"
    else:
        status = "High"
        color = "danger"

    # -----------------------------
    # 2. Calculate % for Gauge
    # -----------------------------
    if high_limit == low_limit:
        percent = 50  # avoid division by zero
    else:
        if value <= low_limit:
            # Below normal range: map to 20–50%
            if low_limit == 0:
                percent = 30
            else:
                ratio = max(value, 0) / low_limit
                percent = 20 + ratio * 30  # 20–50%
        elif value >= high_limit:
            # Above range => max danger
            percent = 100
        else:
            # Inside range: 50–95%
            span = high_limit - low_limit
            offset = value - low_limit
            ratio = offset / span
            percent = 50 + ratio * 45

    # Clean final percentage
    percent = max(0, min(int(round(percent)), 100))

    return {
        "status": status,
        "color": color,
        "percent": percent,
    }
