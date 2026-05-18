"""Probe current measurement range and mode commands for N6781A."""

import pyvisa
import time

RESOURCE   = "USB0::0x0957::0x0F07::MY50000200::INSTR"
TIMEOUT_MS = 5_000
CH = 3

rm = pyvisa.ResourceManager()
dev = rm.open_resource(RESOURCE)
dev.timeout = TIMEOUT_MS


def q(cmd):
    try:
        resp = dev.query(cmd).strip()
        print(f"  OK  {cmd:<60} → {resp}")
        return resp
    except pyvisa.errors.VisaIOError:
        try: dev.clear(); time.sleep(0.2)
        except Exception: pass
        print(f"  TMO {cmd:<60} → timeout")
        return None


def w(cmd):
    dev.write(cmd)
    time.sleep(0.1)
    err = dev.query("SYST:ERR?").strip()
    status = "" if err.startswith("+0") else f"  ← {err}"
    print(f"  WR  {cmd}{status}")


# enable output at 3.6 V so current is flowing
dev.write("VOLT 1.8,(@3)")   # 1.8 raw = 3.6 actual (2x cal)
dev.write("CURR:LIM 1.0,(@3)")
dev.write("OUTP ON,(@3)")
time.sleep(0.5)

print(f"IDN: {dev.query('*IDN?').strip()}\n")

print("=== Current measurement — baseline ===")
q(f"MEAS:CURR? (@{CH})")

print("\n=== Current range read/write ===")
q(f"CURR:RANG? (@{CH})")
q(f"SENS:CURR:RANG? (@{CH})")
w(f"CURR:RANG 0.006,(@{CH})")      # 6 mA range
q(f"MEAS:CURR? (@{CH})")
w(f"CURR:RANG 0.06,(@{CH})")       # 60 mA range
q(f"MEAS:CURR? (@{CH})")
w(f"CURR:RANG 1.0,(@{CH})")        # 1 A range
q(f"MEAS:CURR? (@{CH})")

print("\n=== DC measurement mode ===")
q(f"SENS:CURR:DC:RANG? (@{CH})")
w(f"SENS:CURR:DC:RANG MIN,(@{CH})")
q(f"MEAS:CURR? (@{CH})")
w(f"SENS:CURR:DC:RANG MAX,(@{CH})")
q(f"MEAS:CURR? (@{CH})")

print("\n=== Autorange ===")
q(f"CURR:RANG:AUTO? (@{CH})")
w(f"CURR:RANG:AUTO ON,(@{CH})")
q(f"MEAS:CURR? (@{CH})")
q(f"CURR:RANG? (@{CH})")

print("\n=== Alternative current commands ===")
q(f"MEAS:SCAL:CURR:DC? (@{CH})")
q(f"MEAS:CURR:DC? (@{CH})")

dev.write("OUTP OFF,(@3)")
dev.close()
rm.close()
