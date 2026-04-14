"""Minimal end-to-end example for the PWR-SEN-4GHS sensor.

Run:
    python examples/basic_read.py
"""

from __future__ import annotations

import time

from mc_power_sensor import PowerSensor


def main() -> None:
    with PowerSensor() as sensor:
        sensor.connect()

        print(f"Model:       {sensor.model_name}")
        print(f"Serial:      {sensor.serial_number}")
        print(f"Firmware:    {sensor.firmware_version}")
        print(f"Cal date:    {sensor.calibration_date}")
        print(f"Temperature: {sensor.temperature_c:.1f} C")

        sensor.frequency_mhz = 1000.0
        sensor.averaging_enabled = True
        sensor.average_count = 16

        print("\nReading power @ 1 GHz (Ctrl+C to stop):")
        try:
            while True:
                print(f"  {sensor.read_power():+7.2f} dBm")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
