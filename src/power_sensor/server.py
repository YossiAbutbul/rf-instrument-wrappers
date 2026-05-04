"""FastAPI HTTP server for Mini-Circuits USB power sensor.

Start with:
    uvicorn power_sensor.server:app --host 0.0.0.0 --port 8765

n8n workflows call:
    GET  /power            -> {"value_dbm": -12.34, "value_mw": 0.0583}
    GET  /power/immediate  -> same shape, faster/noisier
    GET  /status           -> model, serial, firmware, temp, freq, mode
    GET  /sensors          -> list connected sensor serial numbers
    POST /connect          -> body: {"serial": "..."} or {}
    POST /disconnect
    POST /config           -> body: any subset of ConfigRequest fields
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from power_sensor import (
    ConnectionFailedError,
    InvalidParameterError,
    NotConnectedError,
    PowerSensor,
)

# ---------------------------------------------------------------------------
# shared sensor state
# ---------------------------------------------------------------------------

sensor = PowerSensor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    if sensor.is_connected:
        sensor.disconnect()


app = FastAPI(title="MC Power Sensor API", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _require_connected() -> None:
    if not sensor.is_connected:
        raise HTTPException(status_code=503, detail="Sensor not connected. POST /connect first.")


def _sensor_error(exc: Exception) -> HTTPException:
    if isinstance(exc, NotConnectedError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, ConnectionFailedError):
        return HTTPException(status_code=502, detail=str(exc))
    if isinstance(exc, InvalidParameterError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# request / response models
# ---------------------------------------------------------------------------

class ConnectRequest(BaseModel):
    serial: Optional[str] = None


class ConfigRequest(BaseModel):
    frequency_mhz: Optional[float] = Field(None, ge=0.009, le=4000.0)
    averaging_enabled: Optional[bool] = None
    average_count: Optional[int] = Field(None, ge=1)
    measurement_mode: Optional[int] = Field(None, ge=0, le=1)


# ---------------------------------------------------------------------------
# routes
# ---------------------------------------------------------------------------

@app.get("/sensors")
def list_sensors():
    """Return serial numbers of all connected USB power sensors."""
    return {"sensors": PowerSensor.list_available()}


@app.post("/connect")
def connect(body: ConnectRequest = ConnectRequest()):
    try:
        sensor.connect(serial=body.serial)
    except (ConnectionFailedError, NotConnectedError) as exc:
        raise _sensor_error(exc)
    return {"connected": True, "model": sensor.model_name, "serial": sensor.serial_number}


@app.post("/disconnect")
def disconnect():
    sensor.disconnect()
    return {"connected": False}


@app.get("/status")
def status():
    _require_connected()
    try:
        return {
            "connected": sensor.is_connected,
            "model": sensor.model_name,
            "serial": sensor.serial_number,
            "firmware": sensor.firmware_version,
            "temperature_c": sensor.temperature_c,
            "frequency_mhz": sensor.frequency_mhz,
            "averaging_enabled": sensor.averaging_enabled,
            "average_count": sensor.average_count,
            "measurement_mode": sensor.measurement_mode,
        }
    except Exception as exc:
        raise _sensor_error(exc)


@app.post("/config")
def configure(body: ConfigRequest):
    _require_connected()
    try:
        if body.frequency_mhz is not None:
            sensor.frequency_mhz = body.frequency_mhz
        if body.averaging_enabled is not None:
            sensor.averaging_enabled = body.averaging_enabled
        if body.average_count is not None:
            sensor.average_count = body.average_count
        if body.measurement_mode is not None:
            sensor.measurement_mode = body.measurement_mode
    except Exception as exc:
        raise _sensor_error(exc)
    return {
        "frequency_mhz": sensor.frequency_mhz,
        "averaging_enabled": sensor.averaging_enabled,
        "average_count": sensor.average_count,
        "measurement_mode": sensor.measurement_mode,
    }


@app.get("/power")
def read_power():
    """Averaged power reading (higher accuracy)."""
    _require_connected()
    try:
        dbm = sensor.read_power(unit="dBm")
        mw = sensor.read_power(unit="mW")
    except Exception as exc:
        raise _sensor_error(exc)
    return {"value_dbm": round(dbm, 3), "value_mw": round(mw, 6)}


@app.get("/power/immediate")
def read_power_immediate():
    """Immediate power reading (faster, ±0.5 dB accuracy)."""
    _require_connected()
    try:
        dbm = sensor.read_immediate_power(unit="dBm")
        mw = sensor.read_immediate_power(unit="mW")
    except Exception as exc:
        raise _sensor_error(exc)
    return {"value_dbm": round(dbm, 3), "value_mw": round(mw, 6)}


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("power_sensor.server:app", host="0.0.0.0", port=8765, reload=False)
