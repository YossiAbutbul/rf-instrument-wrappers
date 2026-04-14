"""Exceptions for the Mini-Circuits power sensor wrapper."""

from __future__ import annotations


class SensorError(Exception):
    """Base class for all power-sensor errors."""


class DLLLoadError(SensorError):
    """Raised when `mcl_pm_NET45.dll` cannot be located or loaded."""


class NotConnectedError(SensorError):
    """Raised when an operation requires an open sensor but none is open."""


class ConnectionFailedError(SensorError):
    """Raised when `Open_Sensor` / `Connect_By_SN` returns a failure code."""


class InvalidParameterError(SensorError, ValueError):
    """Raised when a parameter (e.g. frequency) is outside the allowed range."""
