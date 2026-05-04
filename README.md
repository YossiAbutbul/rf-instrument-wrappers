# RF Instruments — Python Wrappers

> Pythonic wrappers for RF lab instruments used at Arad Technologies. Each device lives in its own package under `src/` with isolated dependencies, examples, and (optionally) a FastAPI server for n8n / remote automation.

---

## Supported Devices

| Device | Package | Connection | Status |
|---|---|---|---|
| **Mini-Circuits USB Power Sensor** (PWR-SEN-4GHS family) | [`power_sensor`](src/power_sensor) | USB HID via `mcl_pm_NET45.dll` (pythonnet) | Verified |
| **Agilent E5061B ENA Network Analyzer** | [`network_analyzer`](src/network_analyzer) | USBTMC via pyvisa | Verified |

---

## Repository Layout

```
src/
├── power_sensor/         # Mini-Circuits USB power sensor wrapper
│   ├── sensor.py            wrapper class
│   ├── server.py            FastAPI HTTP server (for n8n)
│   ├── requirements.txt
│   └── requirements_server.txt
└── network_analyzer/     # Agilent E5061B ENA wrapper
    ├── analyzer.py          wrapper class
    ├── requirements.txt
    └── requirements_plot.txt
examples/
├── power_sensor/         basic_read.py, validate_api.py
└── network_analyzer/     basic_test.py, smith_test.py
n8n/
└── power_measurement.json  importable n8n workflow
pyproject.toml
README.md
```

---

## Quick Start

### 1. Clone and create a venv

```powershell
git clone https://github.com/YossiAbutbul/RF-Instruments.git
cd RF-Instruments
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install only what you need

```powershell
# Mini-Circuits power sensor
pip install -r src/power_sensor/requirements.txt

# E5061B network analyzer
pip install -r src/network_analyzer/requirements.txt

# Plotting (Smith chart)
pip install -r src/network_analyzer/requirements_plot.txt

# FastAPI server for n8n integration
pip install -r src/power_sensor/requirements_server.txt

# Editable install of the packages
pip install -e .
```

Or via `pyproject.toml` extras:

```powershell
pip install -e ".[power_sensor]"
pip install -e ".[network_analyzer,plot]"
pip install -e ".[power_sensor,server]"
```

---

## Mini-Circuits Power Sensor

### Quick example

```python
from power_sensor import PowerSensor

with PowerSensor() as sensor:
    sensor.connect()
    print(f"Model:  {sensor.model_name}")     # PWR-SEN-4GHS
    print(f"Serial: {sensor.serial_number}")
    print(f"Power:  {sensor.read_power():.2f} dBm")
```

### Examples

| Script | Purpose |
|---|---|
| [`examples/power_sensor/basic_read.py`](examples/power_sensor/basic_read.py) | Live power readout @ 908.7 MHz, 500 ms loop |
| [`examples/power_sensor/validate_api.py`](examples/power_sensor/validate_api.py) | Exercise every API method, report PASS/FAIL |

### DLL setup

`mcl_pm_NET45.dll` is proprietary. Download from [minicircuits.com](https://www.minicircuits.com/softwaredownload/pm.html) and place in `dll/` (or install the Power Meter software for auto-discovery).

DLL search order:

| # | Location |
|---|---|
| 1 | `MCL_PM_DLL_DIR` env var |
| 2 | `dll/` folder in this repo |
| 3 | `C:\Program Files\Mini-Circuits\Power_Meter\` |
| 4 | `C:\Program Files (x86)\Mini-Circuits\Power_Meter\` |

If you see `0x80131515`, unblock the DLL: `Unblock-File ".\dll\mcl_pm_NET45.dll"`.

### Key API

| Member | Kind | Description |
|---|---|---|
| `PowerSensor.list_available()` | classmethod | Serial numbers of connected sensors |
| `connect(serial=None)` | method | Open sensor (first found, or by serial) |
| `read_power(unit='dBm')` | method | Averaged power, `'dBm'` or `'mW'` |
| `read_immediate_power(unit='dBm')` | method | Fast (lower-accuracy) read |
| `frequency_mhz` | r/w property | Calibration frequency 0.009 – 4000 MHz |
| `averaging_enabled` / `average_count` | r/w property | Hardware averaging |
| `measurement_mode` | r/w property | `0` low-noise, `1` fast-sampling |
| `model_name`, `serial_number`, `firmware_version`, `temperature_c` | property | Identity / status |

---

## Agilent E5061B Network Analyzer

### Quick example

```python
from network_analyzer import NetworkAnalyzer

with NetworkAnalyzer() as na:
    na.connect()
    na.start_freq_hz   = 100e6
    na.stop_freq_hz    = 3e9
    na.points          = 1601
    na.if_bandwidth_hz = 1000

    na.sweep()

    freqs, mag_db   = na.get_s21_db()
    freqs, r, x     = na.get_impedance(param="S11", z0=50.0)  # Smith R + jX
```

### Examples

| Script | Purpose |
|---|---|
| [`examples/network_analyzer/basic_test.py`](examples/network_analyzer/basic_test.py) | Connect, sweep, print S21 stats |
| [`examples/network_analyzer/smith_test.py`](examples/network_analyzer/smith_test.py) | Full sweep → CSV + interactive Smith chart with R+jX hover tooltips |

### Connection

USB Type-B → Type-A cable. The instrument enumerates as USBTMC. Default resource string in [`analyzer.py`](src/network_analyzer/analyzer.py) — change if your serial differs:

```python
DEFAULT_RESOURCE = "USB0::0x0957::0x1309::MY49102148::INSTR"
```

List available resources:

```python
from network_analyzer import NetworkAnalyzer
print(NetworkAnalyzer.list_available())
```

Requires NI-VISA or Keysight IO Libraries Suite (recommended), or pure-Python via `pyvisa-py + pyusb` (needs Zadig to swap the USB driver).

### Key API

| Member | Kind | Description |
|---|---|---|
| `connect()` / `disconnect()` | method | Open / close VISA session |
| `start_freq_hz` / `stop_freq_hz` / `center_freq_hz` / `span_hz` | r/w property | Sweep range (Hz) |
| `points` | r/w property | Sweep points (max 1601) |
| `if_bandwidth_hz` | r/w property | IF BW (lower = cleaner, slower) |
| `source_power_dbm` | r/w property | Stimulus power |
| `sweep(wait=True)` | method | Trigger single sweep, wait for completion |
| `get_s21_db()` / `get_s11_db()` | method | `(freqs, mag_dB)` |
| `get_s_parameter_complex(param)` | method | `(freqs, complex Γ)` |
| `get_impedance(param='S11', z0=50)` | method | `(freqs, R, X)` — Smith chart data |
| `idn` | property | Instrument ID string |

---

## n8n Integration (Power Sensor)

The power sensor wrapper ships with a FastAPI server so n8n (or any HTTP client) can drive it.

### Start the server

```powershell
uvicorn power_sensor.server:app --host 0.0.0.0 --port 8765
```

Swagger UI at <http://localhost:8765/docs>.

### Endpoints

| Method | Path | Body / Notes |
|---|---|---|
| GET  | `/sensors` | List connected sensor SNs |
| POST | `/connect` | `{"serial": "..."} ` (optional) |
| POST | `/disconnect` | — |
| GET  | `/status` | model, serial, firmware, temp, freq, mode |
| POST | `/config` | any subset of `{frequency_mhz, averaging_enabled, average_count, measurement_mode}` |
| GET  | `/power` | averaged read → `{value_dbm, value_mw}` |
| GET  | `/power/immediate` | fast read → `{value_dbm, value_mw}` |

### n8n workflow

Import [`n8n/power_measurement.json`](n8n/power_measurement.json):

```
Manual Trigger → POST /connect → GET /power → Format Result
```

If n8n runs in Docker, replace `localhost` with `host.docker.internal` in the HTTP Request nodes.

---

## Troubleshooting

**Power sensor — `DLLLoadError`** → install/copy `mcl_pm_NET45.dll` (see DLL setup above).
**Power sensor — `0x80131515`** → `Unblock-File ".\dll\mcl_pm_NET45.dll"`.
**ENA — empty `list_resources()`** → install NI-VISA or Keysight IO Libraries Suite.
**ENA — `Query Unterminated` on screen** → instrument got a malformed SCPI command; check error queue with `*CLS` then retry.
**n8n — connection refused** → use `host.docker.internal` in URLs (Docker can't see host's `localhost`).

---

## License

Python wrappers in this repo: **MIT License**.

`mcl_pm_NET45.dll` is proprietary to Mini-Circuits — obtain directly from them, do not redistribute.
