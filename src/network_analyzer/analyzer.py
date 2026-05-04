"""Pythonic wrapper around the Agilent E5061B ENA Network Analyzer.

Communicates via USBTMC using pyvisa (NI-VISA backend).

Usage::

    with NetworkAnalyzer() as na:
        na.connect()
        print(na.idn)
        na.start_freq_hz = 1e6
        na.stop_freq_hz  = 3e9
        na.points        = 401
        na.if_bandwidth_hz = 1000
        na.sweep()
        freqs, s21 = na.get_s21_db()
"""

from __future__ import annotations

import time
from typing import Optional

import numpy as np
import pyvisa

DEFAULT_RESOURCE = "USB0::0x0957::0x1309::MY49102148::INSTR"
DEFAULT_TIMEOUT_MS = 10_000


class NetworkAnalyzerError(Exception):
    pass


class NotConnectedError(NetworkAnalyzerError):
    pass


class NetworkAnalyzer:
    """High-level interface to an Agilent E5061B via USBTMC/VISA."""

    def __init__(
        self,
        resource: str = DEFAULT_RESOURCE,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
    ) -> None:
        self._resource_str = resource
        self._timeout_ms = timeout_ms
        self._rm: Optional[pyvisa.ResourceManager] = None
        self._dev: Optional[pyvisa.resources.Resource] = None

    # ------------------------------------------------------------------
    # context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "NetworkAnalyzer":
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
        self._dev.write_termination = "\n"
        self._dev.read_termination = "\n"
        self._dev.send_end = True
        self._write("SYST:BEEP:WARN:STAT OFF")
        self._write("SYST:BEEP:COMP:STAT OFF")
        self._write("*CLS")  # clear error queue

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
    # sweep parameters
    # ------------------------------------------------------------------

    @property
    def start_freq_hz(self) -> float:
        return float(self._query("SENS:FREQ:STAR?"))

    @start_freq_hz.setter
    def start_freq_hz(self, value: float) -> None:
        self._write(f"SENS:FREQ:STAR {value:.0f}")

    @property
    def stop_freq_hz(self) -> float:
        return float(self._query("SENS:FREQ:STOP?"))

    @stop_freq_hz.setter
    def stop_freq_hz(self, value: float) -> None:
        self._write(f"SENS:FREQ:STOP {value:.0f}")

    @property
    def center_freq_hz(self) -> float:
        return float(self._query("SENS:FREQ:CENT?"))

    @center_freq_hz.setter
    def center_freq_hz(self, value: float) -> None:
        self._write(f"SENS:FREQ:CENT {value:.0f}")

    @property
    def span_hz(self) -> float:
        return float(self._query("SENS:FREQ:SPAN?"))

    @span_hz.setter
    def span_hz(self, value: float) -> None:
        self._write(f"SENS:FREQ:SPAN {value:.0f}")

    @property
    def points(self) -> int:
        return int(self._query("SENS:SWE:POIN?"))

    @points.setter
    def points(self, value: int) -> None:
        self._write(f"SENS:SWE:POIN {value}")

    @property
    def if_bandwidth_hz(self) -> float:
        return float(self._query("SENS:BWID?"))

    @if_bandwidth_hz.setter
    def if_bandwidth_hz(self, value: float) -> None:
        self._write(f"SENS:BWID {value:.0f}")

    @property
    def source_power_dbm(self) -> float:
        return float(self._query("SOUR:POW?"))

    @source_power_dbm.setter
    def source_power_dbm(self, value: float) -> None:
        self._write(f"SOUR:POW {value}")

    # ------------------------------------------------------------------
    # sweep & data
    # ------------------------------------------------------------------

    def sweep(self, wait: bool = True) -> None:
        """Trigger a single sweep and optionally wait for completion."""
        self._write("TRIG:SOUR BUS")
        self._write("TRIG:SING")
        if wait:
            self._query("*OPC?")

    def get_frequency_array(self) -> np.ndarray:
        """Return frequency points as Hz array (computed from start/stop/points)."""
        return np.linspace(self.start_freq_hz, self.stop_freq_hz, self.points)

    def get_s_parameter_db(self, param: str = "S21") -> tuple[np.ndarray, np.ndarray]:
        """Return (frequencies_hz, magnitude_db) for the given S-parameter.

        Args:
            param: S-parameter string, e.g. ``'S11'``, ``'S21'``.

        Returns:
            Tuple of (freq_hz array, magnitude_dB array).
        """
        self._require_connected()
        # E5061B ENA: define trace 1 of channel 1 as the requested param
        self._write(f"CALC1:PAR1:DEF {param}")
        self._write("CALC1:PAR1:SEL")
        self._write("CALC1:FORM MLOG")
        # FDATA returns 2 values per point: value + 0 (for log mag the 2nd is unused)
        raw = self._query_ascii_data("CALC1:DATA:FDAT?")
        # take every other value (real part), skip the unused 2nd
        mag_db = np.array(raw[0::2])
        return self.get_frequency_array(), mag_db

    def get_s_parameter_complex(self, param: str = "S21") -> tuple[np.ndarray, np.ndarray]:
        """Return (frequencies_hz, complex_data) for the given S-parameter."""
        self._require_connected()
        self._write(f"CALC1:PAR1:DEF {param}")
        self._write("CALC1:PAR1:SEL")
        vals = self._query_ascii_data("CALC1:DATA:SDAT?")
        freqs = self.get_frequency_array()
        real = np.array(vals[0::2])
        imag = np.array(vals[1::2])
        return freqs, real + 1j * imag

    def _query_ascii_data(self, cmd: str) -> list[float]:
        """Query large ASCII float arrays with extended timeout."""
        self._require_connected()
        old_timeout = self._dev.timeout
        self._dev.timeout = 30_000
        try:
            return self._dev.query_ascii_values(cmd, separator=",")
        finally:
            self._dev.timeout = old_timeout

    # convenience aliases
    def get_s11_db(self) -> tuple[np.ndarray, np.ndarray]:
        return self.get_s_parameter_db("S11")

    def get_s21_db(self) -> tuple[np.ndarray, np.ndarray]:
        return self.get_s_parameter_db("S21")

    def get_impedance(
        self, param: str = "S11", z0: float = 50.0
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (frequencies_hz, R, X) from reflection coefficient.

        Smith chart impedance: Z = Z0 * (1 + Γ) / (1 - Γ)

        Args:
            param: reflection S-param (``'S11'`` or ``'S22'``).
            z0:    reference impedance, default 50 ohms.

        Returns:
            Tuple of (freq_hz, R_ohm, X_ohm) arrays.
            R = real part, X = imaginary part (positive = inductive, negative = capacitive).
        """
        freqs, gamma = self.get_s_parameter_complex(param)
        z = z0 * (1 + gamma) / (1 - gamma)
        return freqs, z.real, z.imag

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _require_connected(self) -> None:
        if not self.is_connected:
            raise NotConnectedError("Call connect() before using the analyzer.")

    def _write(self, cmd: str) -> None:
        self._require_connected()
        self._dev.write(cmd)

    def _query(self, cmd: str) -> str:
        self._require_connected()
        return self._dev.query(cmd).strip()
