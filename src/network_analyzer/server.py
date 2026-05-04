"""Live Smith chart web viewer for the Agilent E5061B ENA.

Run:
    uvicorn network_analyzer.server:app --host 0.0.0.0 --port 8766

Open http://localhost:8766 in a browser.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from network_analyzer import NetworkAnalyzer

STATIC_DIR = Path(__file__).parent / "static"

# ---------------------------------------------------------------------------
# shared state
# ---------------------------------------------------------------------------

na = NetworkAnalyzer()
sweep_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    na.connect()
    # fast defaults for live viewer (~0.2 s/sweep)
    na.points = 201
    na.if_bandwidth_hz = 30_000
    yield
    na.disconnect()


app = FastAPI(title="ENA Smith Live Viewer", lifespan=lifespan)


# ---------------------------------------------------------------------------
# config models
# ---------------------------------------------------------------------------

class SweepConfig(BaseModel):
    start_freq_hz: Optional[float] = None
    stop_freq_hz:  Optional[float] = None
    points:        Optional[int]   = None
    if_bandwidth_hz: Optional[float] = None
    source_power_dbm: Optional[float] = None


# ---------------------------------------------------------------------------
# REST: config
# ---------------------------------------------------------------------------

@app.get("/api/config")
def get_config():
    return {
        "idn": na.idn,
        "start_freq_hz": na.start_freq_hz,
        "stop_freq_hz":  na.stop_freq_hz,
        "points":        na.points,
        "if_bandwidth_hz": na.if_bandwidth_hz,
        "source_power_dbm": na.source_power_dbm,
    }


@app.post("/api/config")
async def set_config(cfg: SweepConfig):
    async with sweep_lock:
        if cfg.start_freq_hz   is not None: na.start_freq_hz   = cfg.start_freq_hz
        if cfg.stop_freq_hz    is not None: na.stop_freq_hz    = cfg.stop_freq_hz
        if cfg.points          is not None: na.points          = cfg.points
        if cfg.if_bandwidth_hz is not None: na.if_bandwidth_hz = cfg.if_bandwidth_hz
        if cfg.source_power_dbm is not None: na.source_power_dbm = cfg.source_power_dbm
    return get_config()


# ---------------------------------------------------------------------------
# WebSocket: live sweep stream
# ---------------------------------------------------------------------------

@app.websocket("/ws/sweep")
async def ws_sweep(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            async with sweep_lock:
                # blocking ENA calls in a worker thread so the event loop stays free
                freqs, gamma = await asyncio.to_thread(_sweep_and_read)

            r = (50.0 * (1 + gamma) / (1 - gamma)).real
            x = (50.0 * (1 + gamma) / (1 - gamma)).imag
            payload = {
                "freqs": freqs.tolist(),
                "gamma_real": gamma.real.tolist(),
                "gamma_imag": gamma.imag.tolist(),
                "r": r.tolist(),
                "x": x.tolist(),
            }
            await ws.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        return


def _sweep_and_read():
    na.sweep()
    return na.get_s_parameter_complex("S11")


# ---------------------------------------------------------------------------
# static files
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
