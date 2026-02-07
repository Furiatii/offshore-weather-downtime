"""Process raw INMET CSV data into a clean DataFrame."""

import pandas as pd
import numpy as np
import os
import glob


STATION_META = {
    "A602": {"name": "Marambaia", "lat": -23.05, "lon": -43.59},
    "A606": {"name": "Arraial do Cabo", "lat": -22.97, "lon": -42.02},
    "A608": {"name": "Macaé", "lat": -22.39, "lon": -41.78},
    "A620": {"name": "São Tomé (Campos)", "lat": -21.75, "lon": -41.05},
    "A627": {"name": "Niterói", "lat": -22.90, "lon": -43.10},
    "A652": {"name": "Forte de Copacabana", "lat": -22.99, "lon": -43.19},
}


def parse_inmet_csv(filepath: str) -> pd.DataFrame:
    """Parse a single INMET automatic station CSV file."""
    # INMET CSVs have a metadata header line, then column headers + data
    # Separator is ;  and decimals use , (Brazilian format)
    with open(filepath, "r", encoding="latin-1") as f:
        lines = f.readlines()

    # Find the actual header (starts with "Data;")
    header_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("Data;"):
            header_idx = i
            break

    # Read from header onwards
    from io import StringIO
    csv_text = "".join(lines[header_idx:])
    df = pd.read_csv(StringIO(csv_text), sep=";", decimal=",", na_values=["-9999", ""])

    # Standardize column names
    col_map = {}
    for col in df.columns:
        lower = col.lower()
        if col.startswith("Data"):
            col_map[col] = "data"
        elif col.startswith("Hora"):
            col_map[col] = "hora"
        elif "precipita" in lower:
            col_map[col] = "precipitacao_mm"
        elif "vento, velocidade" in lower:
            col_map[col] = "vento_vel_ms"
        elif "vento, rajada" in lower:
            col_map[col] = "vento_rajada_ms"
        elif "vento, dire" in lower:
            col_map[col] = "vento_dir_graus"
        elif "temperatura do ar" in lower and "bulbo seco" in lower:
            col_map[col] = "temperatura_c"
        elif "umidade relativa do ar, horaria" in lower:
            col_map[col] = "umidade_pct"

    df = df.rename(columns=col_map)

    # Keep only relevant columns
    keep = ["data", "hora", "precipitacao_mm", "vento_vel_ms", "vento_rajada_ms",
            "vento_dir_graus", "temperatura_c", "umidade_pct"]
    df = df[[c for c in keep if c in df.columns]]

    # Parse datetime
    if "data" in df.columns and "hora" in df.columns:
        df["hora"] = df["hora"].astype(str).str.replace(" UTC", "").str.zfill(4)
        df["datetime"] = pd.to_datetime(
            df["data"] + " " + df["hora"],
            format="%Y/%m/%d %H%M",
            errors="coerce",
        )
        df = df.drop(columns=["data", "hora"])

    # Convert numeric columns
    for col in ["precipitacao_mm", "vento_vel_ms", "vento_rajada_ms",
                "vento_dir_graus", "temperatura_c", "umidade_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows without datetime
    df = df.dropna(subset=["datetime"])

    return df


def load_all_stations(data_dir: str) -> pd.DataFrame:
    """Load and combine all station CSV files into one DataFrame."""
    all_dfs = []
    pattern = os.path.join(data_dir, "A*.csv")

    for filepath in sorted(glob.glob(pattern)):
        filename = os.path.basename(filepath)
        # Extract station code (e.g., A627 from A627_2023.csv)
        station_code = filename.split("_")[0]

        if station_code not in STATION_META:
            continue

        try:
            df = parse_inmet_csv(filepath)
            df["estacao"] = station_code
            df["local"] = STATION_META[station_code]["name"]
            all_dfs.append(df)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    if not all_dfs:
        return pd.DataFrame()

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values(["estacao", "datetime"]).reset_index(drop=True)
    return combined


def ms_to_knots(ms: float) -> float:
    """Convert m/s to knots."""
    return ms * 1.94384
