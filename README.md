# Mini-Circuits USB Power Sensor — Python Wrapper

> Python interface for Mini-Circuits USB smart power sensors, built on the official `.NET` DLL via [pythonnet](https://github.com/pythonnet/pythonnet).

**Verified hardware:** PWR-SEN-4GHS &nbsp;|&nbsp; 9 kHz – 4 GHz &nbsp;|&nbsp; −30 to +20 dBm &nbsp;|&nbsp; Windows 10/11

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [DLL Setup](#dll-setup)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Supported Models](#supported-models)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Requirements

| Requirement | Details |
|---|---|
| **OS** | Windows 10 / 11 (64-bit) |
| **Python** | 3.10+ (64-bit) |
| **.NET Framework** | 4.5+ — pre-installed on Windows 10/11 |
| **pythonnet** | ≥ 3.0.3 — installed automatically |
| **Mini-Circuits DLL** | `mcl_pm_NET45.dll` — see [DLL Setup](#dll-setup) |

---

## Installation

```powershell
# 1. Clone the repository
git clone https://github.com/YossiAbutbul/Mini-Circuits-Power-Sensor.git
cd Mini-Circuits-Power-Sensor

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -e .
```

---

## DLL Setup

`mcl_pm_NET45.dll` is Mini-Circuits proprietary software and is **not** bundled with this repo. Two options to obtain it:

### Option A — Download the API package *(recommended)*

1. Go to [minicircuits.com/softwaredownload/pm.html](https://www.minicircuits.com/softwaredownload/pm.html)
2. Click **Download** next to **.NET DLL**
3. Extract the ZIP and copy `mcl_pm_NET45.dll` into the `dll/` folder of this repo

### Option B — Install Mini-Circuits Power Meter software

Install the full GUI application from the same page. The DLL is placed automatically at:

```
C:\Program Files\Mini-Circuits\Power_Meter\mcl_pm_NET45.dll
```

The library finds it there automatically — no manual copy needed.

### DLL search order

The loader checks the following locations in priority order:

| # | Location |
|---|---|
| 1 | `MCL_PM_DLL_DIR` environment variable |
| 2 | `dll/` folder in this repository |
| 3 | `C:\Program Files\Mini-Circuits\Power_Meter\` |
| 4 | `C:\Program Files (x86)\Mini-Circuits\Power_Meter\` |

To use a custom path:

```powershell
$env:MCL_PM_DLL_DIR = "D:\drivers\minicircuits"
```

### Unblocking the DLL

Windows marks downloaded files as potentially unsafe. If you see a `FileLoadException` / error code `0x80131515`, unblock the file:

```powershell
Unblock-File ".\dll\mcl_pm_NET45.dll"
```

Or: right-click `mcl_pm_NET45.dll` → **Properties** → tick **Unblock** → OK.

---

## Quick Start

```python
from mc_power_sensor import PowerSensor

with PowerSensor() as sensor:
    sensor.connect()

    print(f"Model:   {sensor.model_name}")    # PWR-SEN-4GHS
    print(f"Serial:  {sensor.serial_number}") # <serial_number>
    print(f"Power:   {sensor.read_power():.2f} dBm")
```

---

## API Reference

### Connection

```python
# Connect to the first available sensor
sensor.connect()

# Connect to a specific sensor by serial number
sensor.connect(serial="<serial_number>")

# List serial numbers of all connected sensors
serials = PowerSensor.list_available()
# → ['<serial_number>']

# Disconnect manually (or use context manager — preferred)
sensor.disconnect()

# Check connection state
print(sensor.is_connected)  # True / False
```

### Power Measurement

> The sensor measures **total broadband power** across its full operating range (9 kHz – 4 GHz).
> It does **not** filter by frequency — it integrates all power present in band.

```python
# Averaged reading — highest accuracy
power_dbm = sensor.read_power()             # dBm  (default)
power_mw  = sensor.read_power(unit="mW")    # mW

# Immediate reading — faster response, marginally lower accuracy
power_dbm = sensor.read_immediate_power()
power_mw  = sensor.read_immediate_power(unit="mW")
```

### Calibration Frequency

The calibration frequency applies an internal frequency-response correction factor for improved accuracy at a known signal frequency. It does **not** act as a bandpass filter.

```python
sensor.frequency_mhz = 908.7    # set correction for 908.7 MHz
print(sensor.frequency_mhz)     # 908.7
```

Valid range: **0.009 – 4000 MHz**

### Averaging

Hardware averaging reduces measurement noise at the cost of increased reading latency.

```python
sensor.averaging_enabled = True   # enable averaging
sensor.average_count = 16         # samples per reading (default: 0 = off)
sensor.averaging_enabled = False  # disable
```

### Measurement Mode

```python
sensor.measurement_mode = 0   # low-noise mode  (default — slower, more accurate)
sensor.measurement_mode = 1   # fast-sampling mode (higher throughput, more noise)
print(sensor.measurement_mode)  # returns last set value
```

### Device Information

```python
print(sensor.model_name)        # 'PWR-SEN-4GHS'
print(sensor.serial_number)     # '<serial_number>'
print(sensor.firmware_version)  # firmware build number
print(sensor.temperature_c)     # sensor die temperature in °C
```

### Full API Table

| Member | Kind | Description |
|---|---|---|
| `PowerSensor.list_available()` | classmethod | Serial numbers of all connected sensors |
| `connect(serial=None)` | method | Open sensor — first found, or by serial number |
| `disconnect()` | method | Close the sensor connection |
| `is_connected` | property | `True` if sensor is open |
| `model_name` | property | Part number, e.g. `PWR-SEN-4GHS` |
| `serial_number` | property | Sensor serial number |
| `firmware_version` | property | Firmware build number |
| `read_power(unit='dBm')` | method | Averaged power — `'dBm'` or `'mW'` |
| `read_immediate_power(unit='dBm')` | method | Fast power read — `'dBm'` or `'mW'` |
| `frequency_mhz` | r/w property | Calibration frequency in MHz (0.009 – 4000) |
| `averaging_enabled` | r/w property | Enable / disable hardware averaging |
| `average_count` | r/w property | Number of samples per averaged reading |
| `measurement_mode` | r/w property | `0` = low-noise, `1` = fast-sampling |
| `temperature_c` | property | Sensor die temperature in °C |

### Exceptions

| Exception | Raised when |
|---|---|
| `DLLLoadError` | `mcl_pm_NET45.dll` cannot be found or loaded |
| `ConnectionFailedError` | Sensor not found or serial number not available |
| `NotConnectedError` | A method is called before `connect()` |
| `InvalidParameterError` | Out-of-range argument (e.g. frequency, unit) |

All exceptions inherit from `SensorError`.

---

## Examples

### Live power readout

```powershell
python examples/basic_read.py
```

Connects to the first sensor, sets calibration frequency to 908.7 MHz, and prints power every 500 ms.

### Full API validation

```powershell
python examples/validate_api.py
```

Exercises every API method and property, reports PASS / FAIL per item with actual return values, and prints a summary. Useful after a driver or DLL update.

---

## Supported Models

| Model | Range | Dynamic Range | Status |
|---|---|---|---|
| **PWR-SEN-4GHS** | 9 kHz – 4 GHz | −30 to +20 dBm | Verified |
| PWR-SEN-6GHS | 9 kHz – 6 GHz | −30 to +20 dBm | Expected compatible |
| PWR-SEN-8GHS | 9 kHz – 8 GHz | −30 to +20 dBm | Expected compatible |

Any Mini-Circuits USB power sensor that uses `mcl_pm_NET45.dll` should be compatible.

---

## Troubleshooting

**`DLLLoadError: mcl_pm_NET45 not found`**  
The DLL was not found in any of the search locations.  
→ Follow the [DLL Setup](#dll-setup) steps above.

**`FileLoadException` / `0x80131515`**  
Windows blocked the DLL due to Mark-of-the-Web protection.  
→ Run: `Unblock-File ".\dll\mcl_pm_NET45.dll"`

**`ConnectionFailedError: Failed to open sensor`**  
The sensor is not detected on USB.  
→ Check the USB cable and try a different port.  
→ Install the Mini-Circuits Power Meter software once — it registers the HID driver — then uninstall if only the DLL is needed.

**`ConnectionFailedError: Serial number not found`**  
The serial number passed to `connect()` is not detected.  
→ Run `PowerSensor.list_available()` to see currently connected sensors.

**`pythonnet` not found / import error**  
→ Ensure the virtual environment is activated: `.venv\Scripts\activate`  
→ Reinstall: `pip install pythonnet>=3.0.3`

**32-bit / 64-bit mismatch**  
→ Use 64-bit Python. Verify with:
```powershell
python -c "import struct; print(struct.calcsize('P') * 8, 'bit')"
```
`mcl_pm_NET45.dll` is AnyCPU and adapts to Python's bitness automatically.

---

## License

The Python wrapper in this repository is released under the **MIT License**.

`mcl_pm_NET45.dll` is proprietary software owned by Mini-Circuits. Obtain it directly from [Mini-Circuits](https://www.minicircuits.com/softwaredownload/pm.html) under their license terms. The DLL must not be redistributed.
