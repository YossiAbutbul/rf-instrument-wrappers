# Network Analyzer Examples

Scripts and the browser-based `measure.html` app for the Agilent E5061B ENA.

## Install on a new computer

### 1. System prerequisites

- **Python 3.10+** (Windows: install from [python.org](https://www.python.org/downloads/), check "Add to PATH").
- **Keysight IO Libraries Suite** — provides NI-VISA driver for USBTMC. Download from [keysight.com](https://www.keysight.com/find/iosuite). After install, verify the ENA shows up in *Keysight Connection Expert*.
- **USB Type-B → Type-A** cable to the ENA.

### 2. Clone repo + venv

```powershell
git clone https://github.com/YossiAbutbul/rf-instrument-wrappers.git
cd rf-instrument-wrappers
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Python deps

```powershell
pip install -r src/network_analyzer/requirements.txt
pip install -r src/network_analyzer/requirements_plot.txt
pip install -r src/network_analyzer/requirements_server.txt
pip install -e .
```

Or via extras:

```powershell
pip install -e ".[network_analyzer,plot,server]"
```

### 4. Verify VISA sees the ENA

```powershell
python -c "from network_analyzer import NetworkAnalyzer; print(NetworkAnalyzer.list_available())"
```

Should print a list containing something like `USB0::0x0957::0x1309::MY49102148::INSTR`. If empty: re-check Keysight Connection Expert, USB cable, and that the ENA is powered on.

If your serial differs from the default in [`src/network_analyzer/analyzer.py`](../../src/network_analyzer/analyzer.py), update `DEFAULT_RESOURCE` or pass the resource string to `NetworkAnalyzer(resource=...)`.

## Run the scripts

```powershell
python examples/network_analyzer/basic_test.py
python examples/network_analyzer/smith_test.py
```

## Run the browser measure app

```powershell
uvicorn network_analyzer.server:app --host 0.0.0.0 --port 8766
```

Open in browser:

- **Measure table app** → <http://localhost:8766/static/measure.html>
- Live Smith chart viewer → <http://localhost:8766/>

The measure page lets you type a frequency, click **Measure** to append R + jX (Smith-chart impedance from S11) to a table, then **Export Excel** to download an `.xlsx`. The ENA must already be sweeping over your target frequency — the server interpolates from the current sweep.
