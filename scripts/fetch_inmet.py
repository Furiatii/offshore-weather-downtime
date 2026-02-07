"""Download INMET historical data and extract coastal RJ stations.

Usage:
    python scripts/fetch_inmet.py [--years 2019 2020 2021 2022 2023]

Downloads yearly ZIP files from INMET's historical data portal and extracts
only the 6 coastal RJ stations used in this analysis.
"""

import argparse
import os
import sys
import zipfile
import tempfile
import urllib.request

# Coastal RJ stations for offshore analysis
STATIONS = ["A602", "A606", "A608", "A620", "A627", "A652"]

INMET_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{year}.zip"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; offshore-downtime-analysis)"}


def download_year(year: int, data_dir: str) -> None:
    """Download and extract station CSVs for a given year."""
    url = INMET_URL.format(year=year)
    print(f"[{year}] Baixando {url} ...")

    req = urllib.request.Request(url, headers=HEADERS)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                tmp.write(resp.read())
            tmp_path = tmp.name
        except Exception as e:
            print(f"[{year}] Erro no download: {e}")
            return

    try:
        zf = zipfile.ZipFile(tmp_path)
    except zipfile.BadZipFile:
        print(f"[{year}] Arquivo ZIP corrompido.")
        os.unlink(tmp_path)
        return

    names = zf.namelist()
    extracted = 0

    for station in STATIONS:
        matches = [n for n in names if f"_{station}_" in n and "RJ" in n.upper()]
        if not matches:
            print(f"[{year}] {station}: não encontrada")
            continue

        fname = matches[0]
        out_path = os.path.join(data_dir, f"{station}_{year}.csv")
        with zf.open(fname) as src, open(out_path, "wb") as dst:
            dst.write(src.read())
        size_kb = os.path.getsize(out_path) / 1024
        print(f"[{year}] {station}: {size_kb:.0f} KB")
        extracted += 1

    zf.close()
    os.unlink(tmp_path)
    print(f"[{year}] {extracted}/{len(STATIONS)} estações extraídas.\n")


def main():
    parser = argparse.ArgumentParser(description="Download INMET data for coastal RJ stations")
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2019, 2020, 2021, 2022, 2023],
        help="Years to download (default: 2019-2023)",
    )
    parser.add_argument(
        "--data-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "data"),
        help="Output directory for CSV files",
    )
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    os.makedirs(data_dir, exist_ok=True)
    print(f"Diretório de saída: {data_dir}\n")

    for year in sorted(args.years):
        download_year(year, data_dir)

    # Count final files
    csvs = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    print(f"Total: {len(csvs)} arquivos CSV em {data_dir}")


if __name__ == "__main__":
    main()
