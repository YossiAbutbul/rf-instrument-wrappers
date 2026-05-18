"""Set 3.6 V / 1 A limit on CH3, wait 2 s, measure V and I, turn off.

CH3 module has bad calibration (outputs 2× the requested voltage).
voltage_cal={3: 0.5} compensates: wrapper sends 1.8 V to get 3.6 V on terminals.
"""

import time
from dc_power_analyzer import DCPowerAnalyzer

RESOURCE = "USB0::0x0957::0x0F07::MY50000200::INSTR"
CHANNEL  = 3

with DCPowerAnalyzer(RESOURCE, voltage_cal={CHANNEL: 0.5}) as psu:
    psu.connect()

    psu.set_voltage(3.6, channel=CHANNEL)
    psu.set_current_limit(1.0, channel=CHANNEL)
    psu.enable_output(channel=CHANNEL)
    print(f"CH{CHANNEL} output ON — 3.6 V, 1.0 A limit")

    v = psu.measure_voltage(channel=CHANNEL)
    i = psu.measure_current(channel=CHANNEL)
    print(f"Voltage : {v:.4f} V")
    print(f"Current : {i*1000:.3f} mA")

    psu.disable_output(channel=CHANNEL)
    print(f"CH{CHANNEL} output OFF")
