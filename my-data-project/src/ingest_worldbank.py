
import os, pathlib, time
import pandas as pd
import requests

print("CWD:", os.getcwd())

RAW_DIR = pathlib.Path("data/raw/worldbank")
RAW_DIR.mkdir(parents=True, exist_ok=True)
print("RAW_DIR:", RAW_DIR.resolve())

COUNTRY = "VNM"
INDICATORS = ["SP.POP.TOTL","FP.CPI.TOTL.ZG"]  # Dân số & CPI %
PER_PAGE = 20000

def fetch(ind):
    url = f"https://api.worldbank.org/v2/country/{COUNTRY}/indicator/{ind}?format=json&per_page={PER_PAGE}"
    print("GET:", url)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    meta, data = r.json()
    if not data:
        raise RuntimeError(f"No data returned for {ind}")
    df = pd.json_normalize(data)[["date","value","indicator.value","country.value"]]
    df.columns = ["date","value","indicator_name","country_name"]
    df["indicator_code"] = ind
    return df

frames = []
for ind in INDICATORS:
    df = fetch(ind)
    frames.append(df)
    time.sleep(0.8)

out = pd.concat(frames, ignore_index=True)
out.to_csv(RAW_DIR / "worldbank_vnm.csv", index=False)
print("WROTE:", (RAW_DIR / "worldbank_vnm.csv").resolve())
