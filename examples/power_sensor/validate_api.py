"""API validation script for Mini-Circuits USB power sensor.

Tests every wrapper method/property and reports PASS / FAIL / SKIP.
Run with the sensor plugged in.

    python examples/power_sensor/validate_api.py
"""

from __future__ import annotations

import traceback
from typing import Any

from power_sensor import PowerSensor


# ──────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────

PASS  = "PASS "
FAIL  = "FAIL "
SKIP  = "SKIP "

results: list[tuple[str, str, str]] = []   # (status, name, detail)


def check(name: str, fn, *, skip: bool = False) -> Any:
    """Run ``fn()``, print result, record outcome. Return value or None."""
    if skip:
        print(f"  {SKIP} {name}")
        results.append((SKIP, name, "skipped"))
        return None
    try:
        value = fn()
        detail = repr(value) if value is not None else ""
        print(f"  {PASS} {name:<35} {detail}")
        results.append((PASS, name, detail))
        return value
    except Exception as exc:
        short = str(exc).splitlines()[0][:120]
        print(f"  {FAIL} {name:<35} {short}")
        results.append((FAIL, name, traceback.format_exc()))
        return None


def section(title: str) -> None:
    print(f"\n{'─' * 55}")
    print(f"  {title}")
    print(f"{'─' * 55}")


# ──────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 55)
    print("  Mini-Circuits Power Sensor — API Validation")
    print("=" * 55)

    # ── class-level ───────────────────────────────────────────────────
    section("Class methods (no sensor needed)")

    available = check("list_available()", PowerSensor.list_available)
    print(f"         → detected sensors: {available}")

    # ── connect ───────────────────────────────────────────────────────
    section("Connection")

    sensor = PowerSensor()
    check("connect()", sensor.connect)
    check("is_connected", lambda: sensor.is_connected)

    if not sensor.is_connected:
        print("\nSensor not connected — cannot continue.")
        return

    with sensor:
        # ── identity ──────────────────────────────────────────────────
        section("Device identity")

        check("model_name",       lambda: sensor.model_name)
        check("serial_number",    lambda: sensor.serial_number)
        check("firmware_version", lambda: sensor.firmware_version)

        # ── basic power ───────────────────────────────────────────────
        section("Power reading")

        check("read_power() dBm",          lambda: sensor.read_power())
        check("read_power() mW",           lambda: sensor.read_power(unit="mW"))
        check("read_immediate_power() dBm", lambda: sensor.read_immediate_power())
        check("read_immediate_power() mW",  lambda: sensor.read_immediate_power(unit="mW"))

        # ── frequency ─────────────────────────────────────────────────
        section("Calibration frequency")

        check("frequency_mhz getter",       lambda: sensor.frequency_mhz)
        check("frequency_mhz = 908.7",      lambda: setattr(sensor, "frequency_mhz", 908.7))
        check("frequency_mhz readback",     lambda: sensor.frequency_mhz)
        check("frequency_mhz = 1000.0",     lambda: setattr(sensor, "frequency_mhz", 1000.0))
        check("read_power() after freq set", lambda: sensor.read_power())

        # ── averaging ─────────────────────────────────────────────────
        section("Averaging")

        check("averaging_enabled getter",   lambda: sensor.averaging_enabled)
        check("averaging_enabled = True",   lambda: setattr(sensor, "averaging_enabled", True))
        check("average_count getter",       lambda: sensor.average_count)
        check("average_count = 16",         lambda: setattr(sensor, "average_count", 16))
        check("read_power() with averaging", lambda: sensor.read_power())
        check("averaging_enabled = False",  lambda: setattr(sensor, "averaging_enabled", False))

        # ── measurement mode ──────────────────────────────────────────
        section("Measurement mode")

        check("measurement_mode getter",    lambda: sensor.measurement_mode)
        check("measurement_mode = 1 (fast)", lambda: setattr(sensor, "measurement_mode", 1))
        check("read_power() fast mode",     lambda: sensor.read_power())
        check("measurement_mode = 0 (low noise)", lambda: setattr(sensor, "measurement_mode", 0))

        # ── temperature ───────────────────────────────────────────────
        section("Temperature")

        check("temperature_c",              lambda: sensor.temperature_c)

        # ── disconnect ────────────────────────────────────────────────
        section("Disconnect")
        check("disconnect()", sensor.disconnect)
        check("is_connected after disconnect", lambda: sensor.is_connected)

    # ── summary ───────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  Summary")
    print("=" * 55)

    passed  = [r for r in results if r[0] == PASS]
    failed  = [r for r in results if r[0] == FAIL]
    skipped = [r for r in results if r[0] == SKIP]

    print(f"  PASS:  {len(passed)}")
    print(f"  FAIL:  {len(failed)}")
    print(f"  SKIP:  {len(skipped)}")

    if failed:
        print("\n  Failed tests:")
        for _, name, detail in failed:
            first_line = detail.splitlines()[-1][:100] if detail else ""
            print(f"    - {name}: {first_line}")

    print()


if __name__ == "__main__":
    main()
