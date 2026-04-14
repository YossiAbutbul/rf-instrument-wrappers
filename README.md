# Mini-Circuits USB Power Sensor — Python Wrapper

Python library for Mini-Circuits USB smart power sensors (tested target:
**PWR-SEN-4GHS**, 9 kHz – 4 GHz, -30 to +20 dBm). Wraps the official
`mcl_pm_NET45.dll` via [pythonnet](https://github.com/pythonnet/pythonnet).

- Windows only (uses .NET Framework 4.5+).
- 64-bit Python 3.10+.
- Clean pythonic API with context-manager support.

## Install

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Get the DLL

1. Visit <https://www.minicircuits.com/softwaredownload/pm.html>.
2. Download the **Power Meter API DLL** package (ZIP).
3. Extract and copy `mcl_pm_NET45.dll` into the `dll/` folder of this repo.

Alternatively, install Mini-Circuits' full Power Meter software — the DLL
will land in `C:\Program Files\Mini-Circuits\Power_Meter\`. The loader
searches that path automatically.

Override the search path by setting `MCL_PM_DLL_DIR`:

```powershell
$env:MCL_PM_DLL_DIR = "D:\drivers\minicircuits"
```

## Quick start

```python
from mc_power_sensor import PowerSensor

with PowerSensor() as sensor:
    sensor.connect()                    # first sensor on bus
    print(sensor.model_name)            # "PWR-SEN-4GHS"
    print(sensor.serial_number)

    sensor.frequency_mhz = 1000         # calibration frequency
    sensor.averaging_enabled = True
    sensor.average_count = 16

    print(f"{sensor.read_power():.2f} dBm")
    print(f"Sensor temp: {sensor.temperature_c:.1f} C")
```

Connect to a specific unit by serial number:

```python
sensor.connect(serial="11512345678")
```

## API

| Member | Type | Meaning |
|---|---|---|
| `connect(serial=None)` | method | open sensor (by SN or first found) |
| `disconnect()` | method | close sensor |
| `model_name` | property | e.g. `PWR-SEN-4GHS` |
| `serial_number` | property | sensor SN |
| `firmware_version` | property | firmware string |
| `calibration_date` | property | last cal date |
| `frequency_mhz` | r/w property | calibration frequency (0.009–4000) |
| `averaging_enabled` | r/w property | toggle averaging |
| `average_count` | r/w property | number of samples per read |
| `measurement_mode` | r/w property | 0 = low-noise, 1 = low-freq (check DLL docs) |
| `temperature_c` | property | sensor die temperature |
| `read_power(unit="dBm")` | method | `"dBm"` or `"mW"` |

## Troubleshooting

- **`DLLLoadError: mcl_pm_NET45 not found`** — DLL not in `dll/`, not in
  Program Files, and `MCL_PM_DLL_DIR` unset. See [Get the DLL](#get-the-dll).
- **`SensorError: Open_Sensor returned 0`** — sensor not plugged in, wrong
  serial, or driver not installed. Install Mini-Circuits Power Meter
  software once so Windows registers the HID driver.
- **32-bit vs 64-bit mismatch** — pythonnet bitness must match Python;
  `mcl_pm_NET45.dll` is AnyCPU so it works with both.

## License

MIT for the Python wrapper. The Mini-Circuits DLL is **not** redistributed
here; obtain it directly from Mini-Circuits under their license.
