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
    """High-level interface to a Mini-Circuits USB power sensor.

    Usage::

        with PowerSensor() as sensor:
            sensor.connect()
            print(sensor.model_name, sensor.serial_number)
            print(f"{sensor.read_power():.2f} dBm")

    Connect to a specific unit by serial number::

        sensor.connect(serial="11501120012")
    """

    def __init__(self) -> None:
        self._usb_pm_cls = load_usb_pm()
        self._dev = self._usb_pm_cls()
        self._connected = False
        self._measurement_mode = 0  # DLL has no getter; track locally

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
    @classmethod
    def list_available(cls) -> list[str]:
        """Return serial numbers of all connected sensors.

        Example::

            sns = PowerSensor.list_available()
            # ['11501120012', '11501130034']
        """
        usb_pm_cls = load_usb_pm()
        dev = usb_pm_cls()
        raw = dev.Get_Available_SN_List("")
        sn_str = str(_out_value(raw) if isinstance(raw, tuple) else raw).strip()
        if not sn_str:
            return []
        return [s.strip("[]") for s in sn_str.split() if s.strip("[]")]

    def connect(self, serial: Optional[str] = None) -> None:
        """Open the sensor. If ``serial`` is given, match that specific unit."""
        if self._connected:
            return

        if serial:
            result = self._dev.Connect_By_SN(serial)
        else:
            result = self._dev.Open_Sensor("")

        status = int(_unwrap(result))
        if status == 0:
            raise ConnectionFailedError(
                f"Failed to open sensor (serial={serial!r}). "
                "Check USB connection and driver installation."
            )
        if status == 3:
            raise ConnectionFailedError(
                f"Serial number {serial!r} not found. "
                f"Call PowerSensor.list_available() to see connected sensors."
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
        """Firmware version number."""
        self._require_connected()
        raw = _unwrap(self._dev.GetFirmwareVer(0))
        return str(int(raw))

    # ------------------------------------------------------------------
    # measurement
    # ------------------------------------------------------------------
    def read_power(self, unit: PowerUnit = "dBm") -> float:
        """Read power (averaged, higher accuracy).

        Args:
            unit: ``'dBm'`` (default) or ``'mW'``.

        Returns:
            Power reading in the requested unit.
        """
        self._require_connected()
        if unit not in ("dBm", "mW"):
            raise InvalidParameterError(f"unit must be 'dBm' or 'mW', got {unit!r}")
        self._dev.Format_mw = (unit == "mW")
        return float(_unwrap(self._dev.ReadPower()))

    def read_immediate_power(self, unit: PowerUnit = "dBm") -> float:
        """Read power with faster response but reduced accuracy.

        Useful for fast sweeps or monitoring where ±0.5 dB is acceptable.
        """
        self._require_connected()
        if unit not in ("dBm", "mW"):
            raise InvalidParameterError(f"unit must be 'dBm' or 'mW', got {unit!r}")
        self._dev.Format_mw = (unit == "mW")
        return float(_unwrap(self._dev.ReadImmediatePower()))

    @property
    def frequency_mhz(self) -> float:
        """Calibration frequency in MHz.

        Tells the sensor which correction factor to apply from its internal
        cal table. Does NOT filter — the sensor always measures total broadband
        power across its full operating range (9 kHz – 4 GHz).
        """
        self._require_connected()
        return float(self._dev.Freq)

    @frequency_mhz.setter
    def frequency_mhz(self, value: float) -> None:
        self._require_connected()
        if not (_FREQ_MIN_MHZ <= value <= _FREQ_MAX_MHZ):
            raise InvalidParameterError(
                f"frequency_mhz must be in [{_FREQ_MIN_MHZ}, {_FREQ_MAX_MHZ}] "
                f"MHz, got {value}"
            )
        self._dev.Freq = float(value)

    # ------------------------------------------------------------------
    # averaging
    # ------------------------------------------------------------------
    @property
    def averaging_enabled(self) -> bool:
        """Toggle hardware averaging (reduces noise, increases latency)."""
        self._require_connected()
        return bool(self._dev.AVG)

    @averaging_enabled.setter
    def averaging_enabled(self, value: bool) -> None:
        self._require_connected()
        self._dev.AVG = bool(value)

    @property
    def average_count(self) -> int:
        """Number of samples per averaged reading."""
        self._require_connected()
        return int(self._dev.AvgCount)

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
        return float(_unwrap(self._dev.GetDeviceTemperature("C")))

    @property
    def measurement_mode(self) -> int:
        """0 = low-noise mode, 1 = fast-sampling mode.

        DLL has no getter — returns last value set (defaults to 0).
        """
        return self._measurement_mode

    @measurement_mode.setter
    def measurement_mode(self, value: int) -> None:
        self._require_connected()
        self._dev.SetFasterMode(int(value))
        self._measurement_mode = int(value)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _require_connected(self) -> None:
        if not self._connected:
            raise NotConnectedError("Call connect() before using the sensor.")
