# RF Instruments — Python Wrappers

> Pythonic wrappers for RF lab instruments used at Arad Technologies. Each device lives in its own package under `src/` with isolated dependencies, examples, and (optionally) a FastAPI server for n8n / remote automation.

---

## Supported Devices

| Device | Package | Connection | Status |
|---|---|---|---|
| **Mini-Circuits USB Power Sensor** (PWR-SEN-4GHS family) | [`power_sensor`](src/power_sensor) | USB HID via `mcl_pm_NET45.dll` (pythonnet) | Verified |
| **Agilent E5061B ENA Network Analyzer** | [`network_analyzer`](src/network_analyzer) | USBTMC via pyvisa | Verified |
| **Agilent N6705B DC Power Analyzer** (N6781A module) | [`dc_power_analyzer`](src/dc_power_analyzer) | USBTMC via pyvisa | Verified |

---

## Repository Layout

```
src/
├── power_sensor/         # Mini-Circuits USB power sensor wrapper
│   ├── sensor.py            wrapper class
│   ├── server.py            FastAPI HTTP server (for n8n)
│   ├── requirements.txt
│   └── requirements_server.txt
├── network_analyzer/     # Agilent E5061B ENA wrapper
│   ├── analyzer.py          wrapper class
│   ├── server.py            FastAPI HTTP server + live Smith chart
│   ├── requirements.txt
│   └── requirements_plot.txt
└── dc_power_analyzer/    # Agilent N6705B DC Power Analyzer wrapper
    ├── analyzer.py          wrapper class
    └── requirements.txt
examples/
├── power_sensor/         basic_read.py, validate_api.py
├── network_analyzer/     basic_test.py, smith_test.py
└── dc_power_analyzer/    basic_test.py, features_test.py, charge_measure.py
n8n/
├── power_measurement.json      importable n8n workflow (power sensor)
└── Smith_ENA_workflow.json     importable n8n workflow (ENA Smith chart)
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

# N6705B DC power analyzer
pip install -r src/dc_power_analyzer/requirements.txt

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
pip install -e ".[dc_power_analyzer]"
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

### Live Smith Chart Web Viewer

A FastAPI + Plotly web app that streams S11 sweeps over WebSocket and renders a live Smith chart in the browser.

```powershell
pip install -r src/network_analyzer/requirements_server.txt
uvicorn network_analyzer.server:app --host 0.0.0.0 --port 8766
```

Open <http://localhost:8766>.

**Features:**
- Real-time S11 trace on a Plotly Smith chart (~5 Hz refresh at default settings)
- Hover any point → tooltip with `f`, `R`, `X`, `|Γ|`
- Configurable trail history (0–10 past sweeps shown faded)
- Sweep config form (start/stop/points/IFBW/power) with live Apply
- Pause / Resume / Clear, sweep counter and rate
- Dark theme, responsive layout

**API endpoints (also driveable from n8n / scripts):**

| Method | Path | Notes |
|---|---|---|
| GET  | `/api/config` | current sweep settings + IDN |
| POST | `/api/config` | partial update of any sweep field |
| POST | `/api/measure` | measure at specific frequencies → `[{freq_hz, r_ohm, x_ohm, l_nh, s11_db, …}]` |
| POST | `/api/append-results` | append rows to Excel file (creates if missing) |
| POST | `/api/open-file` | open a file with its default Windows application |
| WS   | `/ws/sweep` | streams `{freqs, gamma_real, gamma_imag, r, x}` per sweep |

---

## Agilent N6705B DC Power Analyzer

### Quick example

```python
from dc_power_analyzer import DCPowerAnalyzer

with DCPowerAnalyzer("USB0::0x0957::0x0F07::MY50000200::INSTR") as psu:
    psu.connect()

    psu.set_voltage(3.6, channel=3)
    psu.set_current_limit(1.0, channel=3)
    psu.enable_output(channel=3)

    v = psu.measure_voltage(channel=3)
    i = psu.measure_current(channel=3)
    print(f"Voltage: {v:.4f} V   Current: {i*1000:.3f} mA")

    psu.disable_output(channel=3)
```

### Examples

| Script | Purpose |
|---|---|
| [`examples/dc_power_analyzer/basic_test.py`](examples/dc_power_analyzer/basic_test.py) | Scan VISA resources, connect, read channel state |
| [`examples/dc_power_analyzer/features_test.py`](examples/dc_power_analyzer/features_test.py) | Set V/I, enable output, measure, polled waveform, teardown |
| [`examples/dc_power_analyzer/charge_measure.py`](examples/dc_power_analyzer/charge_measure.py) | Set 3.6 V / 1 A, measure V and I immediately, turn off |

### Connection

USB Type-B → Type-A cable. Requires **Keysight IO Libraries Suite** installed — the N6705B enumerates as USBTMC only after the Keysight USB driver is registered.

Find your resource string:

```python
from dc_power_analyzer import DCPowerAnalyzer
print(DCPowerAnalyzer.list_available())
# e.g. ['USB0::0x0957::0x0F07::MY50000200::INSTR']
```

### N6781A module — known quirks (firmware D.02.08)

| Issue | Detail |
|---|---|
| **Current limit command** | Use `CURR:LIM` (not `CURR`) in voltage-priority mode. Generates harmless warning 315 but value is written correctly. |
| **OVP** | `VOLT:PROT` not supported. Use `get_voltage_limit()` / `set_voltage_limit()` (`VOLT:LIM`) for the hardware voltage ceiling. |
| **OCP level** | `CURR:PROT` level not supported. Only `CURR:PROT:STAT` (enable/disable) works. |
| **Hardware datalog** | `SENS:DLOG` / `FETC:DLOG` commands not reliably accessible. Use `poll_measurements()` instead. |
| **Current measurement** | Measure immediately after `enable_output()` — delays cause the reading to drift toward zero. Best accuracy ~±1 mA. |
| **Current sign** | `MEAS:CURR?` returns negative for sourced current on N6781A. `measure_current()` applies `abs()` to match front-panel display. |
| **Bad calibration** | If the module DAC outputs 2× the set voltage, pass `voltage_cal={ch: 0.5}` to the constructor — all set/get voltage calls are transparently corrected. |

### Voltage calibration correction

Some N6781A modules have a bad factory calibration where requesting 3.6 V produces 7.2 V on the terminals. Compensate via the `voltage_cal` parameter:

```python
# voltage_cal={channel: scale} — multiplied into every VOLT write,
# divided out of every VOLT? read. ADC (MEAS:VOLT?) is unaffected.
psu = DCPowerAnalyzer(RESOURCE, voltage_cal={3: 0.5})
psu.set_voltage(3.6, channel=3)   # sends VOLT 1.8 to instrument → 3.6 V on terminals
psu.get_voltage_setpoint(channel=3)  # returns 3.6 (not 1.8)
```

### Key API

| Member | Kind | Description |
|---|---|---|
| `DCPowerAnalyzer.list_available()` | classmethod | VISA resource strings for all connected instruments |
| `connect()` / `disconnect()` | method | Open / close VISA session |
| `set_voltage(volts, channel)` | method | Set output voltage (voltage-priority mode) |
| `get_voltage_setpoint(channel)` | method | Read back voltage setpoint |
| `set_current_limit(amps, channel)` | method | Set current limit (`CURR:LIM`) |
| `get_current_limit(channel)` | method | Read back current limit |
| `enable_output(channel)` / `disable_output(channel)` | method | Turn output on/off |
| `disable_all_outputs(active_channels=None)` | method | Turn off all (or specified) channels; skips empty slots silently |
| `is_output_enabled(channel)` | method | `True` if output is on |
| `measure_voltage(channel)` | method | Actual terminal voltage (V) |
| `measure_current(channel)` | method | Actual output current (A, absolute value) |
| `measure_power(channel)` | method | Actual output power (W) |
| `measure_all(channel)` | method | `{voltage_v, current_a, power_w}` dict |
| `poll_measurements(channel, duration_s, interval_s)` | method | Time-series V/I/P via repeated queries |
| `get_voltage_limit(channel)` / `set_voltage_limit(volts, channel)` | method | Hardware voltage ceiling (`VOLT:LIM`) |
| `enable_ocp(channel)` / `disable_ocp(channel)` / `is_ocp_enabled(channel)` | method | OCP enable/disable/query |
| `read_error()` / `clear_errors()` | method | SCPI error queue |
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
**ENA / N6705B — empty `list_resources()`** → install Keysight IO Libraries Suite. Open Keysight Connection Expert and verify the instrument appears there first.
**ENA — `Query Unterminated` on screen** → instrument got a malformed SCPI command; check error queue with `*CLS` then retry.
**N6705B — `VI_ERROR_TMO` on channel query** → the addressed channel has no module installed. Only query channels with modules present.
**N6705B — current reads ~0 after a delay** → measure immediately after `enable_output()`. Delayed reads on N6781A drift toward zero.
**N6705B — voltage 2× expected** → bad module calibration. Pass `voltage_cal={ch: 0.5}` to the constructor.
**n8n — connection refused** → use `host.docker.internal` in URLs (Docker can't see host's `localhost`).

---

## License

Python wrappers in this repo: **MIT License**.

`mcl_pm_NET45.dll` is proprietary to Mini-Circuits — obtain directly from them, do not redistribute.
