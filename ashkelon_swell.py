from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import subprocess
import xarray as xr
import pandas as pd
import json
import os

TZ = ZoneInfo("Asia/Jerusalem")
UTC = ZoneInfo("UTC")

LAT = 31.6875
LON = 34.5000

now = datetime.now(TZ)
tomorrow = (now + timedelta(days=1)).date()

local_start = datetime.combine(tomorrow, datetime.min.time(), TZ)
local_end = local_start + timedelta(hours=23)

utc_start = local_start.astimezone(UTC)
utc_end = local_end.astimezone(UTC)

folder = os.path.expanduser("~/copernicus-data")
os.makedirs(folder, exist_ok=True)

file = os.path.join(folder, "ashkelon_swell.nc")

cmd = [
    "copernicusmarine", "subset",
    "-i", "cmems_mod_med_wav_anfc_4.2km_PT1H-i",
    "-v", "VHM0_SW1",
    "-v", "VTM01_SW1",
    "-v", "VMDR_SW1",
    "-x", str(LON),
    "-X", str(LON),
    "-y", str(LAT),
    "-Y", str(LAT),
    "-t", utc_start.strftime("%Y-%m-%d %H:%M:%S"),
    "-T", utc_end.strftime("%Y-%m-%d %H:%M:%S"),
    "-o", folder,
    "-f", "ashkelon_swell.nc",
    "--overwrite"
]

subprocess.run(cmd, check=True)

ds = xr.open_dataset(file)

df = (
    ds[["VHM0_SW1", "VTM01_SW1", "VMDR_SW1"]]
    .to_dataframe()
    .dropna()
    .reset_index()
)

rows = []

for _, r in df.iterrows():
    t = (
        pd.Timestamp(r["time"])
        .to_pydatetime()
        .replace(tzinfo=UTC)
        .astimezone(TZ)
    )

    rows.append({
        "time": t.strftime("%Y-%m-%d %H:%M"),
        "hour": t.strftime("%H:%M"),
        "swell_cm": round(float(r["VHM0_SW1"]) * 100),
        "period_sec": round(float(r["VTM01_SW1"]), 2),
        "swell_direction_deg": round(float(r["VMDR_SW1"]))
    })

output = {
    "location": "אשקלון",
    "date": str(tomorrow),
    "forecast": rows
}

with open("ashkelon.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(json.dumps(output, ensure_ascii=False, indent=2))