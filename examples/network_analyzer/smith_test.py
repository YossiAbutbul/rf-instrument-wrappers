"""Smith chart impedance measurement (R + jX) from S11.

Saves full sweep to CSV and optionally plots a Smith chart.
"""

import os
import csv

import numpy as np
from network_analyzer import NetworkAnalyzer

CSV_PATH = os.path.join(os.path.dirname(__file__), "smith_data.csv")
PLOT_PATH = os.path.join(os.path.dirname(__file__), "smith_chart.png")


def main():
    print("=== E5061B Smith Chart Test ===\n")

    with NetworkAnalyzer() as na:
        na.connect()
        print(f"IDN : {na.idn}\n")

        # -- configure sweep --
        na.start_freq_hz    = 100e6     # 100 MHz
        na.stop_freq_hz     = 1e9       # 1 GHz
        na.points           = 1601      # E5061B max
        na.if_bandwidth_hz  = 1000
        na.source_power_dbm = -10

        print(f"Sweep: {na.start_freq_hz/1e6:.0f}-{na.stop_freq_hz/1e6:.0f} MHz, "
              f"{na.points} pts")

        print("Triggering sweep...")
        na.sweep()
        print("Sweep complete.\n")

        # -- get full impedance data + raw S11 (for Smith plot) --
        freqs, gamma = na.get_s_parameter_complex("S11")
        z = 50.0 * (1 + gamma) / (1 - gamma)
        r, x = z.real, z.imag

    # -- save CSV --
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["freq_hz", "R_ohm", "X_ohm", "S11_real", "S11_imag"])
        for fr, rr, xx, gr, gi in zip(freqs, r, x, gamma.real, gamma.imag):
            w.writerow([fr, rr, xx, gr, gi])
    print(f"Saved {len(freqs)} points -> {CSV_PATH}")

    # -- plot Smith chart if matplotlib available --
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 7))
        # unit circle (Smith chart boundary)
        theta = np.linspace(0, 2 * np.pi, 360)
        ax.plot(np.cos(theta), np.sin(theta), "k-", lw=1)
        ax.axhline(0, color="gray", lw=0.5)
        # constant resistance circles (R = 0, 25, 50, 100, 200)
        for rn in [0, 0.5, 1, 2, 5]:
            cx, cy = rn / (1 + rn), 0
            rad = 1 / (1 + rn)
            ax.plot(cx + rad * np.cos(theta), cy + rad * np.sin(theta),
                    "gray", lw=0.4)
        # plot trace as scatter so each point is hoverable
        trace = ax.scatter(gamma.real, gamma.imag, c=freqs, cmap="viridis",
                           s=8, picker=True)
        ax.plot(gamma.real, gamma.imag, "b-", lw=0.8, alpha=0.5)
        ax.plot(gamma.real[0], gamma.imag[0], "go", ms=10,
                label=f"start {freqs[0]/1e6:.0f} MHz")
        ax.plot(gamma.real[-1], gamma.imag[-1], "ro", ms=10,
                label=f"stop {freqs[-1]/1e6:.0f} MHz")
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)
        ax.set_aspect("equal")
        ax.set_title("S11 Smith Chart (hover for R+jX)")
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(False)
        plt.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
        print(f"Saved plot -> {PLOT_PATH}")

        # hover tooltips
        try:
            import mplcursors
            cursor = mplcursors.cursor(trace, hover=True)

            @cursor.connect("add")
            def _on_hover(sel):
                idx = sel.index
                sign = "+j" if x[idx] >= 0 else "-j"
                sel.annotation.set_text(
                    f"f = {freqs[idx]/1e6:.2f} MHz\n"
                    f"Z = {r[idx]:.2f} {sign}{abs(x[idx]):.2f} Ω\n"
                    f"|Γ| = {abs(gamma[idx]):.3f}"
                )
                sel.annotation.get_bbox_patch().set(fc="lightyellow", alpha=0.9)
        except ImportError:
            print("mplcursors not installed - no hover tooltips. pip install mplcursors")

        plt.show()
    except ImportError:
        print("matplotlib not installed - skipping plot. pip install matplotlib")


if __name__ == "__main__":
    main()
