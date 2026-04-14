"""Pythonic wrapper around the Mini-Circuits `usb_pm` .NET class.

Target device family: Mini-Circuits USB smart power sensors
(e.g. PWR-SEN-4GHS, PWR-6GHS). Communicates through `mcl_pm_NET45.dll`
loaded via pythonnet.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from ._clr_loader import load_usb_pm
from .exceptions import (
    ConnectionFailedError,
    InvalidParameterError,
    NotConnectedError,
)

_FREQ_MIN_MHZ = 0.009      # 9 kHz
_FREQ_MAX_MHZ = 4000.0     # 4 GHz (PWR-SEN-4GHS upper limit)

PowerUnit = Literal["dBm", "mW"]


def _unwrap(result: Any) -> Any:
    """pythonnet turns .NET `ref`/`out` parameters into extra tuple items.

    Return the first element when that happens; otherwise the value itself.
    """
    if isinstance(result, tuple) and result:
        return result[0]
    return result


def _out_value(result: Any) -> Any:
    """Return the first `out` value (tuple[1]) if present, else the result."""
    if isinstance(result, tuple) and len(result) >= 2:
        return result[1]
    return result


class PowerSensor:
    """High-level interface to a Mini-Circuits USB power sensor."""

    def __init__(self) -> None:
        self._usb_pm_cls = load_usb_pm()
        self._dev = self._usb_pm_cls()
        self._connected = False

    # ------------------------------------------------------------------
    # context manager
    # ------------------------------------------------------------------
    def __enter__(self) -> "PowerSensor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._connected:
            self.disconnect()

    # ------------------------------------------------------------------
    # connection
    # ------------------------------------------------------------------
    def connect(self, serial: Optional[str] = None) -> None:
        """Open the sensor. If ``serial`` is given, match that specific unit."""
        if self._connected:
            return

        if serial:
            result = self._dev.Connect_By_SN(serial)
        else:
            result = self._dev.Open_Sensor()

        status = _unwrap(result)
        if not int(status):
            raise ConnectionFailedError(
                f"Failed to open sensor (serial={serial!r}). "
                "Check USB connection and driver installation."
            )
        self._connected = True

    def disconnect(self) -> None:
        if not self._connected:
            return
        self._dev.Close_Sensor()
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # identity
    # ------------------------------------------------------------------
    @property
    def model_name(self) -> str:
        self._require_connected()
        return str(_unwrap(self._dev.GetSensorModelName()))

    @property
    def serial_number(self) -> str:
        self._require_connected()
        return str(_unwrap(self._dev.GetSensorSN()))

    @property
    def firmware_version(self) -> str:
        """Firmware version as 'major.minor' (decoded from Int64)."""
        self._require_connected()
        raw = _unwrap(self._dev.GetFirmwareVer(0))
        return str(int(raw))

    @property
    def calibration_date(self) -> str:
        """Best-effort calibration date; returns 'N/A' if DLL lacks the call."""
        self._require_connected()
        for name in ("GetCalDate", "GetDeviceCalDate", "CalDate", "Get_Cal_Date"):
            fn = getattr(self._dev, name, None)
            if fn is None:
                continue
            for args in ((), ("",), (0,)):
                try:
                    raw = fn(*args)
                except TypeError:
                    continue
                val = _out_value(raw) if isinstance(raw, tuple) and len(raw) >= 2 else _unwrap(raw)
                return str(val)
        return "N/A"

    # ------------------------------------------------------------------
    # measurement
    # ------------------------------------------------------------------
    def read_power(self, unit: PowerUnit = "dBm") -> float:
        """Read instantaneous power in dBm (default) or mW."""
        self._require_connected()
        if unit not in ("dBm", "mW"):
            raise InvalidParameterError(f"unit must be 'dBm' or 'mW', got {unit!r}")
        # Format_mw is a settable property on usb_pm: True -> mW, False -> dBm
        self._dev.Format_mw = (unit == "mW")
        return float(_unwrap(self._dev.ReadPower()))

    @property
    def frequency_mhz(self) -> float:
        """Calibration frequency in MHz."""
        self._require_connected()
        return float(_unwrap(self._dev.Freq))

    @frequency_mhz.setter
    def frequency_mhz(self, value: float) -> None:
        self._require_connected()
        if not (_FREQ_MIN_MHZ <= value <= _FREQ_MAX_MHZ):
            raise InvalidParameterError(
                f"frequency_mhz must be in [{_FREQ_MIN_MHZ}, {_FREQ_MAX_MHZ}] "
                f"MHz, got {value}"
            )
        # DLL may expose setter as property `Freq` or method `SetFreq`/`SetFrequency`
        for name in ("SetFreq", "SetFrequency", "Set_Freq"):
            fn = getattr(self._dev, name, None)
            if fn is not None:
                fn(float(value))
                return
        self._dev.Freq = float(value)

    # ------------------------------------------------------------------
    # averaging
    # ------------------------------------------------------------------
    @property
    def averaging_enabled(self) -> bool:
        self._require_connected()
        return bool(_unwrap(self._dev.AVG))

    @averaging_enabled.setter
    def averaging_enabled(self, value: bool) -> None:
        self._require_connected()
        self._dev.AVG = bool(value)

    @property
    def average_count(self) -> int:
        self._require_connected()
        return int(_unwrap(self._dev.AvgCount))

    @average_count.setter
    def average_count(self, value: int) -> None:
        self._require_connected()
        if value < 1:
            raise InvalidParameterError("average_count must be >= 1")
        self._dev.AvgCount = int(value)

    # ------------------------------------------------------------------
    # misc
    # ------------------------------------------------------------------
    @property
    def temperature_c(self) -> float:
        """Sensor die temperature in degrees Celsius."""
        self._require_connected()
        return float(_unwrap(self._dev.GetSensorTemperature()))

    @property
    def measurement_mode(self) -> int:
        """Measurement mode (see Mini-Circuits programming manual)."""
        self._require_connected()
        return int(_unwrap(self._dev.GetMeasurementMode()))

    @measurement_mode.setter
    def measurement_mode(self, value: int) -> None:
        self._require_connected()
        self._dev.SetMeasurementMode(int(value))

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _require_connected(self) -> None:
        if not self._connected:
            raise NotConnectedError("Call connect() before using the sensor.")
