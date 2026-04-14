# DLL folder

Drop `mcl_pm_NET45.dll` here.

## Where to get it

1. Go to <https://www.minicircuits.com/softwaredownload/pm.html>.
2. Download the **Power Meter API DLL** package (look for the
   `Full API DLL package` or `.NET 4.5` variant — filename usually
   `Power_Meter_API.zip`).
3. Unzip and copy `mcl_pm_NET45.dll` into this directory.

## Alternative locations

The loader also searches:

- `%MCL_PM_DLL_DIR%` (env var override)
- `C:\Program Files\Mini-Circuits\Power_Meter\`
- `C:\Program Files (x86)\Mini-Circuits\Power_Meter\`

So if you installed the full Mini-Circuits Power Meter software, you
can skip this folder entirely.

## Note

The DLL is **not** committed to this repo (see `.gitignore`). It is
Mini-Circuits proprietary software; obtain it under their license.
