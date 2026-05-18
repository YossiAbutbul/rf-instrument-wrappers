"""Feature walkthrough for the Agilent N6705B DC Power Analyzer (N6781A module).

Demonstrates:
  - Set voltage / current limit
  - Enable output and measure V, I, P
  - Polled waveform acquisition
  - Safe teardown

Edit CHANNEL, TARGET_VOLTAGE, and CURRENT_LIMIT before running.
"""

import time

from dc_power_analyzer import DCPowerAnalyzer

RESOURCE       = "USB0::0x0957::0x0F07::MY50000200::INSTR"
CHANNEL        = 3  # N6781A module installed in slot 3
TARGET_VOLTAGE = 5.0    # V
CURRENT_LIMIT  = 0.5    # A


def main():
    print("=== N6705B Features Test ===\n")

    with DCPowerAnalyzer(RESOURCE) as psu:
        psu.connect()
        print(f"IDN: {psu.idn}\n")

        # ------------------------------------------------------------------
        # 1. Configure voltage + current limit
        # ------------------------------------------------------------------
        print(f"[1] Setting CH{CHANNEL}: {TARGET_VOLTAGE} V, {CURRENT_LIMIT} A limit")
        psu.set_voltage(TARGET_VOLTAGE, channel=CHANNEL)
        psu.set_current_limit(CURRENT_LIMIT, channel=CHANNEL)
        print(f"    V setpoint : {psu.get_voltage_setpoint(CHANNEL):.3f} V")
        print(f"    I limit    : {psu.get_current_limit(CHANNEL):.3f} A\n")

        # ------------------------------------------------------------------
        # 2. Enable output and measure
        # ------------------------------------------------------------------
        print(f"[2] Enabling CH{CHANNEL} output...")
        psu.enable_output(channel=CHANNEL)
        time.sleep(0.1)  # let output settle

        readings = psu.measure_all(channel=CHANNEL)
        print(f"    Voltage : {readings['voltage_v']:.4f} V")
        print(f"    Current : {readings['current_a']:.4f} A")
        print(f"    Power   : {readings['power_w']:.4f} W\n")

        # ------------------------------------------------------------------
        # 3. Polled waveform (hardware datalog not supported on N6781A D.02.08)
        # ------------------------------------------------------------------
        POLL_DURATION_S = 1.0
        POLL_INTERVAL_S = 0.1
        print(f"[4] Polling {POLL_DURATION_S} s @ {POLL_INTERVAL_S*1000:.0f} ms/sample on CH{CHANNEL}")
        data = psu.poll_measurements(
            channel=CHANNEL,
            duration_s=POLL_DURATION_S,
            interval_s=POLL_INTERVAL_S,
        )
        voltages = data["voltage_v"]
        currents = data["current_a"]
        v_min, v_max = min(voltages), max(voltages)
        i_min, i_max = min(currents), max(currents)
        print(f"    Samples : {len(voltages)}")
        print(f"    V range : {v_min:.4f} – {v_max:.4f} V")
        print(f"    I range : {i_min:.6f} – {i_max:.6f} A\n")

        # ------------------------------------------------------------------
        # 4. Safe teardown
        # ------------------------------------------------------------------
        print("[5] Disabling all outputs...")
        psu.disable_all_outputs(active_channels=[CHANNEL])
        print(f"    CH{CHANNEL} output: {'ON' if psu.is_output_enabled(CHANNEL) else 'OFF'}")

        err = psu.read_error()
        print(f"\nError queue: {err}")

    print("\nDisconnected. Feature test complete.")


if __name__ == "__main__":
    main()
