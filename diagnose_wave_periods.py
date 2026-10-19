"""Read-only Copernicus wave-period diagnostic; never alters forecast JSON."""
import os
import subprocess
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
import xarray as xr

DATE = os.getenv("DIAGNOSTIC_DATE", "2026-10-19")
LAT, LON = 31.6875, 34.5000
DATASET = "cmems_mod_med_wav_anfc_4.2km_PT1H-i"
FIELDS = ("VTM01_SW1", "VTPK", "VTM10", "VTM02", "VHM0_SW1")
TZ = ZoneInfo("Asia/Jerusalem")
def utc_str(hour):
    return datetime.fromisoformat(f"{DATE}T{hour}:00").replace(tzinfo=TZ).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%d %H:%M:%S")

values = {}
with tempfile.TemporaryDirectory() as folder:
    for field in FIELDS:
        args = ["copernicusmarine", "subset", "-i", DATASET, "-v", field, "-x", str(LON), "-X", str(LON), "-y", str(LAT), "-Y", str(LAT), "-t", utc_str("05:00"), "-T", utc_str("10:00"), "-o", folder, "-f", f"{field}.nc", "--overwrite"]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode:
            print(f"{field}: unavailable: {result.stderr[-800:]}", flush=True)
            continue
        with xr.open_dataset(os.path.join(folder, f"{field}.nc")) as ds:
            frame = ds[[field]].to_dataframe().dropna().reset_index()
            for _, row in frame.iterrows():
                local = row["time"].to_pydatetime().replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
                values.setdefault(local.strftime("%H:%M"), {})[field] = round(float(row[field]), 3)

print(f"Copernicus {DATASET} | date={DATE} | lat={LAT}, lon={LON}")
print("Hour | " + " | ".join(FIELDS))
for hour in ("06:00", "07:00", "08:00", "09:00"):
    print(hour + " | " + " | ".join(str(values.get(hour, {}).get(field, "N/A")) for field in FIELDS))
if not values:
    raise SystemExit("No data retrieved; inspect Copernicus errors above.")
