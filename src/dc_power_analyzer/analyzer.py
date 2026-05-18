"""Pythonic wrapper around the Agilent N6705B DC Power Analyzer.

Communicates via USBTMC using pyvisa (NI-VISA backend).

Usage::

    with DCPowerAnalyzer() as psu:
        psu.connect()
        print(psu.idn)

        psu.set_voltage(5.0, channel=1)
        psu.set_current_limit(1.0, channel=1)
        psu.enable_output(channel=1)

        v = psu.measure_voltage(channel=1)
        i = psu.measure_current(channel=1)
        p = psu.measure_power(channel=1)
"""

from __future__ import annotations

from typing import Optional

import pyvisa

DEFAULT_RESOURCE = "USB0::0x0957::0x0F07::MY00000000::INSTR"  # update with your serial number
DEFAULT_TIMEOUT_MS = 10_000
MAX_CHANNELS = 4


class DCPowerAnalyzerError(Exception):
    pass


class NotConnectedError(DCPowerAnalyzerError):
    pass


class InvalidChannelError(DCPowerAnalyzerError):
    pass


class DCPowerAnalyzer:
    """High-level interface to an Agilent N6705B via USBTMC/VISA.

    The N6705B has up to 4 output channels. Channel numbers are 1-based.

    Args:
        voltage_cal: per-channel calibration scale dict, e.g. ``{3: 0.5}``.
            Applied as: ``actual_setpoint = requested_voltage * scale``.
            Use when a module has a bad calibration (e.g. sets 7.2 V when
            asked for 3.6 V → scale = 0.5).  Measurement readbacks are
            divided by the same scale so ``measure_voltage`` always returns
            the true terminal voltage.
    """

    def __init__(
        self,
        resource: str = DEFAULT_RESOURCE,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        num_channels: int = MAX_CHANNELS,
        voltage_cal: dict[int, float] | None = None,
    ) -> None:
        self._resource_str = resource
        self._timeout_ms = timeout_ms
        self._num_channels = num_channels
        self._voltage_cal: dict[int, float] = voltage_cal or {}
        self._rm: Optional[pyvisa.ResourceManager] = None
        self._dev: Optional[pyvisa.resources.Resource] = None

    def _vcal(self, channel: int) -> float:
        """Return voltage calibration scale for channel (default 1.0)."""
        return self._voltage_cal.get(channel, 1.0)

    # ------------------------------------------------------------------
    # context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "DCPowerAnalyzer":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    # ------------------------------------------------------------------
    # connection
    # ------------------------------------------------------------------

    @staticmethod
    def list_available() -> list[str]:
        """Return VISA resource strings for all connected instruments."""
        rm = pyvisa.ResourceManager()
        return list(rm.list_resources())

    def connect(self) -> None:
        if self._dev is not None:
            return
        self._rm = pyvisa.ResourceManager()
        self._dev = self._rm.open_resource(self._resource_str)
        self._dev.timeout = self._timeout_ms
        self._write("*CLS")

    def disconnect(self) -> None:
        if self._dev is not None:
            self._dev.close()
            self._dev = None
        if self._rm is not None:
            self._rm.close()
            self._rm = None

    @property
    def is_connected(self) -> bool:
        return self._dev is not None

    # ------------------------------------------------------------------
    # identity
    # ------------------------------------------------------------------

    @property
    def idn(self) -> str:
        return self._query("*IDN?")

    # ------------------------------------------------------------------
    # output enable/disable
    # ------------------------------------------------------------------

    def enable_output(self, channel: int = 1) -> None:
        """Turn on the output for the given channel."""
        self._check_channel(channel)
        self._write(f"OUTP ON,(@{channel})")

    def disable_output(self, channel: int = 1) -> None:
        """Turn off the output for the given channel."""
        self._check_channel(channel)
        self._write(f"OUTP OFF,(@{channel})")

    def disable_all_outputs(self, active_channels: list[int] | None = None) -> None:
        """Turn off channel outputs.

        Args:
            active_channels: list of channels that have modules installed.
                             If None, tries all 1–num_channels and silently
                             skips empty slots (instrument returns error 222).
        """
        channels = active_channels or range(1, self._num_channels + 1)
        for ch in channels:
            try:
                self._write(f"OUTP OFF,(@{ch})")
            except Exception:
                pass

    def is_output_enabled(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return bool(int(self._query(f"OUTP:STAT? (@{channel})")))

    # ------------------------------------------------------------------
    # voltage setpoint
    # ------------------------------------------------------------------

    def set_voltage(self, volts: float, channel: int = 1) -> None:
        """Set output voltage. Applies per-channel calibration scale if configured."""
        self._check_channel(channel)
        raw = volts * self._vcal(channel)
        self._write(f"VOLT {raw:.6g},(@{channel})")

    def get_voltage_setpoint(self, channel: int = 1) -> float:
        """Return voltage setpoint in user units (cal scale removed)."""
        self._check_channel(channel)
        raw = float(self._query(f"VOLT? (@{channel})"))
        return raw / self._vcal(channel)

    # ------------------------------------------------------------------
    # current limit  (voltage-priority mode: CURR:LIM, not CURR)
    # ------------------------------------------------------------------

    def set_current_limit(self, amps: float, channel: int = 1) -> None:
        """Set current limit for voltage-priority mode.

        Note: N6781A-type modules generate a harmless settings-conflict
        warning (315) if the channel is in voltage-priority mode — the
        value is still written correctly.
        """
        self._check_channel(channel)
        self._write(f"CURR:LIM {amps:.6g},(@{channel})")

    def get_current_limit(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return float(self._query(f"CURR:LIM? (@{channel})"))

    # ------------------------------------------------------------------
    # measurements
    # ------------------------------------------------------------------

    def measure_voltage(self, channel: int = 1) -> float:
        """Measure actual terminal voltage in volts.

        No calibration correction applied — ADC reads the real voltage.
        Only the DAC setpoint (set_voltage) is affected by voltage_cal.
        """
        self._check_channel(channel)
        return float(self._query(f"MEAS:VOLT? (@{channel})"))

    def set_current_measurement_range(self, amps: float, channel: int = 1) -> None:
        """Set the current measurement range via CURR:RANG.

        Generates a harmless 315 warning in voltage-priority mode but
        correctly shifts the measurement range on N6781A modules.
        Pick a range just above your expected current for best accuracy.
        Common N6781A ranges: 0.006, 0.06, 0.6, 3.0 (A).

        Args:
            amps: range in amps, e.g. 0.06 for 60 mA range.
        """
        self._check_channel(channel)
        self._write(f"CURR:RANG {amps:.6g},(@{channel})")

    def measure_current(self, channel: int = 1) -> float:
        """Measure actual output current in amps (absolute value).

        N6781A MEAS:CURR? uses a sign convention opposite to the front
        panel display. abs() is applied so the result matches the display.
        """
        self._check_channel(channel)
        return abs(float(self._query(f"MEAS:CURR? (@{channel})")))

    def measure_power(self, channel: int = 1) -> float:
        """Measure actual output power in watts."""
        self._check_channel(channel)
        return float(self._query(f"MEAS:POW? (@{channel})"))

    def measure_all(self, channel: int = 1) -> dict[str, float]:
        """Return dict with voltage_v, current_a, power_w for channel."""
        return {
            "voltage_v": self.measure_voltage(channel),
            "current_a": self.measure_current(channel),
            "power_w": self.measure_power(channel),
        }

    # ------------------------------------------------------------------
    # voltage software limit (VOLT:LIM — N6781A-style modules)
    # Note: standard modules use VOLT:PROT; N6781A uses VOLT:LIM.
    # ------------------------------------------------------------------

    def set_voltage_limit(self, volts: float, channel: int = 1) -> None:
        """Set software voltage limit (VOLT:LIM). Used by N6781A modules."""
        self._check_channel(channel)
        self._write(f"VOLT:LIM {volts:.6g},(@{channel})")

    def get_voltage_limit(self, channel: int = 1) -> float:
        self._check_channel(channel)
        return float(self._query(f"VOLT:LIM? (@{channel})"))

    # ------------------------------------------------------------------
    # OCP status (level not supported on N6781A)
    # ------------------------------------------------------------------

    def enable_ocp(self, channel: int = 1) -> None:
        self._check_channel(channel)
        self._write(f"CURR:PROT:STAT ON,(@{channel})")

    def disable_ocp(self, channel: int = 1) -> None:
        self._check_channel(channel)
        self._write(f"CURR:PROT:STAT OFF,(@{channel})")

    def is_ocp_enabled(self, channel: int = 1) -> bool:
        self._check_channel(channel)
        return bool(int(self._query(f"CURR:PROT:STAT? (@{channel})")))

    # ------------------------------------------------------------------
    # software polling (replaces hardware datalog for N6781A firmware)
    # ------------------------------------------------------------------

    def poll_measurements(
        self,
        channel: int = 1,
        duration_s: float = 1.0,
        interval_s: float = 0.1,
    ) -> dict[str, list]:
        """Poll V/I at fixed intervals and return time-series arrays.

        Uses two MEAS queries per sample (V then I). Each USB round-trip
        takes ~30–80 ms, so effective minimum interval is ~80 ms. Power
        is computed as V×I.

        Args:
            channel:    channel to measure.
            duration_s: total polling duration in seconds.
            interval_s: target time between sample starts (default 0.1 s).

        Returns:
            Dict with keys ``time_s``, ``voltage_v``, ``current_a``,
            ``power_w`` — each a list of floats.
        """
        import time as _time

        self._check_channel(channel)
        times, volts, amps, watts = [], [], [], []
        t0 = _time.monotonic()
        while True:
            t_sample = _time.monotonic()
            v = float(self._query(f"MEAS:VOLT? (@{channel})"))
            i = float(self._query(f"MEAS:CURR? (@{channel})"))
            times.append(round(t_sample - t0, 6))
            volts.append(v)
            amps.append(i)
            watts.append(round(v * i, 9))
            elapsed = _time.monotonic() - t0
            if elapsed >= duration_s:
                break
            query_time = _time.monotonic() - t_sample
            sleep_for = interval_s - query_time
            if sleep_for > 0:
                _time.sleep(sleep_for)
        return {
            "time_s":    times,
            "voltage_v": volts,
            "current_a": amps,
            "power_w":   watts,
        }

    # ------------------------------------------------------------------
    # errors
    # ------------------------------------------------------------------

    def read_error(self) -> str:
        """Read one entry from the instrument error queue."""
        return self._query("SYST:ERR?")

    def clear_errors(self) -> None:
        self._write("*CLS")

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _check_channel(self, channel: int) -> None:
        if not (1 <= channel <= self._num_channels):
            raise InvalidChannelError(
                f"Channel {channel} out of range (1–{self._num_channels})"
            )

    def _require_connected(self) -> None:
        if not self.is_connected:
            raise NotConnectedError("Call connect() before using the analyzer.")

    def _write(self, cmd: str) -> None:
        self._require_connected()
        self._dev.write(cmd)

    def _query(self, cmd: str) -> str:
        self._require_connected()
        return self._dev.query(cmd).strip()
