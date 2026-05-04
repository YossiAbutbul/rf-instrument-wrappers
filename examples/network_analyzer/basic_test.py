"""Basic connectivity and sweep test for the Agilent E5061B."""

from network_analyzer import NetworkAnalyzer

def main():
    print("=== E5061B Basic Test ===\n")

    print(f"Resource: USB0::0x0957::0x1309::MY49102148::INSTR\n")

    with NetworkAnalyzer() as na:
        na.connect()
        print(f"IDN       : {na.idn}")
        print(f"Connected : {na.is_connected}\n")

        # -- configure sweep --
        na.start_freq_hz   = 1e6       # 1 MHz
        na.stop_freq_hz    = 3e9       # 3 GHz
        na.points          = 201
        na.if_bandwidth_hz = 1000      # 1 kHz IFBW
        na.source_power_dbm = -10

        print(f"Start freq : {na.start_freq_hz / 1e6:.3f} MHz")
        print(f"Stop freq  : {na.stop_freq_hz  / 1e9:.3f} GHz")
        print(f"Points     : {na.points}")
        print(f"IFBW       : {na.if_bandwidth_hz:.0f} Hz")
        print(f"Source pwr : {na.source_power_dbm} dBm\n")

        # -- trigger sweep and read S21 --
        print("Triggering sweep...")
        na.sweep()
        print("Sweep complete.\n")

        freqs, s21_db = na.get_s21_db()

        print(f"S21 results ({len(freqs)} points):")
        print(f"  Min : {s21_db.min():.2f} dB  @ {freqs[s21_db.argmin()] / 1e6:.1f} MHz")
        print(f"  Max : {s21_db.max():.2f} dB  @ {freqs[s21_db.argmax()] / 1e6:.1f} MHz")
        print(f"  @ 1 GHz : {s21_db[len(freqs)//2]:.2f} dB")

    print("\nDisconnected. Test passed.")

if __name__ == "__main__":
    main()
