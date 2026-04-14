# Mini-Circuits USB Power Sensor — Python Wrapper

Python library for Mini-Circuits USB smart power sensors.  
Verified on **PWR-SEN-4GHS** (9 kHz – 4 GHz, −30 to +20 dBm).

Wraps the official `mcl_pm_NET45.dll` via [pythonnet](https://github.com/pythonnet/pythonnet) — the same DLL used by LabVIEW, C#, and MATLAB integrations.

---

## Requirements

| Requirement | Version |
|---|---|
| Windows | 10 / 11 (64-bit) |
| Python | 3.10+ (64-bit) |
| .NET Framework | 4.5+ (pre-installed on Win 10/11) |
| pythonnet | ≥ 3.0.3 (installed automatically) |

---

## Installation

### 1. Clone the repo

```powershell
git clone https://github.com/YossiAbutbul/Mini-Circuits-Power-Sensor.git
cd Mini-Circuits-Power-Sensor
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
pip install -e .
```

### 4. Get the Mini-Circuits DLL

The `mcl_pm_NET45.dll` is Mini-Circuits proprietary software and is **not** included in this repo. Obtain it from Mini-Circuits:

**Option A — Download the API package (recommended)**

1. Go to: https://www.minicircuits.com/softwaredownload/pm.html
2. Click **Download** next to **.NET DLL**
3. Extract the ZIP
4. Copy `mcl_pm_NET45.dll` into the `dll/` folder of this repo

**Option B — Install Mini-Circuits Power Meter software**

Install the full GUI application (also from the link above).  
The DLL is automatically placed in:
```
C:\Program Files\Mini-Circuits\Power_Meter\
```
The loader finds it there automatically — no need to copy anything.

> **OneDrive / downloaded file note:** Windows may block DLLs downloaded from the internet.  
> If you see a `FileLoadException` / `0x80131515` error, right-click `mcl_pm_NET45.dll` → **Properties** → check **Unblock** → OK.  
> Or run in PowerShell:
> ```powershell
> Unblock-File ".\dll\mcl_pm_NET45.dll"
> ```

### 5. Connect the sensor

Plug in the PWR-SEN-4GHS via USB. Windows installs the HID driver automatically — no separate driver download needed.

---

## Quick Start

```python
from mc_power_sensor import PowerSensor

with PowerSensor() as sensor:
    sensor.connect()
    print(f"Model:  {sensor.model_name}")   # PWR-SEN-4GHS
    print(f"Serial: {sensor.serial_number}")
    print(f"Power:  {sensor.read_power():.2f} dBm")
```

Run the included example for a live readout:

```powershell
python examples/basic_read.py
```

---

## API Reference

### Connecting

```python
# First sensor found
sensor.connect()

# Specific sensor by serial number
sensor.connect(serial="11501120012")

# List all connected sensors
serials = PowerSensor.list_available()
print(serials)  # ['11501120012', '11501130034']
```

### Reading Power

The sensor measures **total broadband power** across its full operating range (9 kHz – 4 GHz). It does **not** filter by frequency — it sees everything in range.

```python
# Averaged reading — highest accuracy (default)
power_dbm = sensor.read_power()            # dBm
power_mw  = sensor.read_power(unit='mW')   # mW

# Immediate reading — faster response, slightly lower accuracy
power_dbm = sensor.read_immediate_power()
```

### Calibration Frequency

```python
# Optional: set expected signal frequency for best accuracy.
# This applies the sensor's internal frequency-response correction.
# Does NOT filter — sensor still reads all power in range.
sensor.frequency_mhz = 908.7
```

### Averaging

```python
sensor.averaging_enabled = True   # enable hardware averaging
sensor.average_count = 16         # number of samples per reading
```

### Device Info

```python
print(sensor.model_name)        # 'PWR-SEN-4GHS'
print(sensor.serial_number)     # '11501120012'
print(sensor.firmware_version)  # firmware build number
```

### Measurement Mode

```python
sensor.measurement_mode = 0   # low-noise mode (default, slower)
sensor.measurement_mode = 1   # fast-sampling mode (higher noise)
```

### Full API Table

| Member | Type | Description |
|---|---|---|
| `connect(serial=None)` | method | Open sensor (first found, or by SN) |
| `disconnect()` | method | Close sensor |
| `list_available()` | classmethod | List SNs of all connected sensors |
| `is_connected` | property | `True` if sensor is open |
| `model_name` | property | Part number string |
| `serial_number` | property | Sensor serial number |
| `firmware_version` | property | Firmware build number |
| `read_power(unit='dBm')` | method | Averaged power in dBm or mW |
| `read_immediate_power(unit='dBm')` | method | Fast power read (lower accuracy) |
| `frequency_mhz` | r/w property | Cal correction frequency (0.009–4000 MHz) |
| `averaging_enabled` | r/w property | Enable/disable hardware averaging |
| `average_count` | r/w property | Samples per averaged reading |
| `measurement_mode` | r/w property | 0 = low-noise, 1 = fast-sampling |
| `temperature_c` | property | Sensor die temperature (°C) |

---

## Supported Models

Tested: **PWR-SEN-4GHS**  
Should work with any Mini-Circuits USB power sensor that uses `mcl_pm_NET45.dll` (PWR-6GHS, PWR-8GHS, etc.).

---

## Troubleshooting

**`DLLLoadError: mcl_pm_NET45 not found`**  
DLL not found in any search location.  
→ See [Step 4](#4-get-the-mini-circuits-dll) above.

**`FileLoadException` / `0x80131515`**  
Windows blocked the downloaded DLL (Mark-of-the-Web protection).  
→ Run: `Unblock-File ".\dll\mcl_pm_NET45.dll"`

**`ConnectionFailedError: Failed to open sensor`**  
Sensor not detected.  
→ Check USB cable. Try unplugging and replugging.  
→ Install Mini-Circuits Power Meter software once to register the USB driver, then uninstall if you only need the DLL.

**`ConnectionFailedError: Serial number not found`**  
Wrong serial passed to `connect()`.  
→ Run `PowerSensor.list_available()` to see detected sensors.

**`pythonnet` import error**  
→ Make sure you activated the virtual environment: `.venv\Scripts\activate`  
→ Reinstall: `pip install pythonnet>=3.0.3`

**32-bit / 64-bit mismatch**  
→ Use 64-bit Python. Check with: `python -c "import struct; print(struct.calcsize('P')*8)"`  
→ `mcl_pm_NET45.dll` is AnyCPU so it adapts to Python's bitness.

---

## DLL Search Order

The loader checks these locations in order:

| Priority | Location |
|---|---|
| 1 | `MCL_PM_DLL_DIR` environment variable |
| 2 | `dll/` folder in this repo |
| 3 | `C:\Program Files\Mini-Circuits\Power_Meter\` |
| 4 | `C:\Program Files (x86)\Mini-Circuits\Power_Meter\` |

Custom path override:
```powershell
$env:MCL_PM_DLL_DIR = "D:\drivers\minicircuits"
python examples/basic_read.py
```

---

## License

MIT for the Python wrapper code.  
`mcl_pm_NET45.dll` is Mini-Circuits proprietary software — obtain it directly from [Mini-Circuits](https://www.minicircuits.com/softwaredownload/pm.html) under their license. Do not redistribute the DLL.
