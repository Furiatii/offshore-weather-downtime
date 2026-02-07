"""Operational thresholds for offshore activities."""

import pandas as pd
import numpy as np


# Thresholds based on typical offshore operational limits
# Sources: NORMAM-01, industry standards, Noble Denton guidelines
OPERATIONS = {
    "Içamento com guindaste": {
        "desc": "Crane lifts on deck or between vessel and platform",
        "vento_max_ms": 12.9,     # ~25 knots sustained
        "rajada_max_ms": 15.4,    # ~30 knots gust
        "chuva_max_mm": 10.0,     # heavy rain = low visibility
    },
    "Transferência de pessoal": {
        "desc": "Personnel transfer by basket or gangway",
        "vento_max_ms": 10.3,     # ~20 knots sustained
        "rajada_max_ms": 12.9,    # ~25 knots gust
        "chuva_max_mm": 10.0,
    },
    "Mergulho (saturação)": {
        "desc": "Saturation diving operations",
        "vento_max_ms": 10.3,     # ~20 knots
        "rajada_max_ms": 12.9,    # ~25 knots
        "chuva_max_mm": 5.0,
    },
    "Operações gerais no convés": {
        "desc": "General deck operations, maintenance",
        "vento_max_ms": 15.4,     # ~30 knots sustained
        "rajada_max_ms": 20.6,    # ~40 knots gust
        "chuva_max_mm": 20.0,
    },
}


def classify_hour(row: pd.Series, operation: str) -> bool:
    """Check if a single hourly reading exceeds operational limits.

    Returns True if conditions are ABOVE limits (= downtime).
    """
    limits = OPERATIONS[operation]

    wind_exceeded = (
        pd.notna(row.get("vento_vel_ms"))
        and row["vento_vel_ms"] > limits["vento_max_ms"]
    )
    gust_exceeded = (
        pd.notna(row.get("vento_rajada_ms"))
        and row["vento_rajada_ms"] > limits["rajada_max_ms"]
    )
    rain_exceeded = (
        pd.notna(row.get("precipitacao_mm"))
        and row["precipitacao_mm"] > limits["chuva_max_mm"]
    )

    return wind_exceeded or gust_exceeded or rain_exceeded


def calculate_downtime(df: pd.DataFrame) -> pd.DataFrame:
    """Add downtime columns for each operation type.

    Each column is True when conditions exceed limits for that operation.
    """
    result = df.copy()
    for op_name in OPERATIONS:
        col_name = f"downtime_{op_name}"
        result[col_name] = result.apply(lambda row: classify_hour(row, op_name), axis=1)
    return result


def daily_downtime_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly downtime to daily counts.

    Returns a DataFrame with date, station, and hours of downtime per operation.
    """
    if "datetime" not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df["date"] = df["datetime"].dt.date

    downtime_cols = [c for c in df.columns if c.startswith("downtime_")]

    agg = {"vento_vel_ms": "max", "vento_rajada_ms": "max", "precipitacao_mm": "sum"}
    for col in downtime_cols:
        agg[col] = "sum"  # count hours of downtime

    daily = df.groupby(["estacao", "local", "date"]).agg(agg).reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    daily["month"] = daily["date"].dt.month
    daily["year"] = daily["date"].dt.year

    # A day counts as "downtime day" if >= 4 hours exceeded limits
    for col in downtime_cols:
        daily[f"{col}_day"] = daily[col] >= 4

    return daily
