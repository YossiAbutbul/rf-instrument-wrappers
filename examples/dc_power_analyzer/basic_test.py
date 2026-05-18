"""Basic connectivity test for the Agilent N6705B DC Power Analyzer."""

from dc_power_analyzer import DCPowerAnalyzer

RESOURCE = "USB0::0x0957::0x0F07::MY50000200::INSTR"


def main():
    print("=== N6705B Basic Connection Test ===\n")

    print("Scanning for VISA resources...")
    available = DCPowerAnalyzer.list_available()
    if available:
        for r in available:
            print(f"  {r}")
    else:
        print("  (none found)")
    print()

    print(f"Connecting to: {RESOURCE}")
    with DCPowerAnalyzer(RESOURCE) as psu:
        psu.connect()
        print(f"Connected : {psu.is_connected}")
        print(f"IDN       : {psu.idn}\n")

        for ch in [3]:  # only slot 3 has a module installed
            v_set = psu.get_voltage_setpoint(ch)
            i_lim = psu.get_current_limit(ch)
            enabled = psu.is_output_enabled(ch)
            print(f"  CH{ch}  V_set={v_set:.3f} V  I_lim={i_lim:.3f} A  output={'ON' if enabled else 'OFF'}")

        print()
        err = psu.read_error()
        print(f"Error queue: {err}")

    print("\nDisconnected. Test passed.")


if __name__ == "__main__":
    main()
