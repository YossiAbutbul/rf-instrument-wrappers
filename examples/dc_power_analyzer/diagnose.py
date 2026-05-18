"""Diagnose VISA setup for the N6705B."""

import sys
from pathlib import Path

print(f"Python: {sys.version}\n")

# 1. pyvisa installed?
try:
    import pyvisa
    print(f"pyvisa        : {pyvisa.__version__}")
except ImportError:
    print("pyvisa        : NOT INSTALLED  →  pip install pyvisa")
    sys.exit(1)

# 2. which backend loads by default?
rm = None
try:
    rm = pyvisa.ResourceManager()
    print(f"VISA backend  : {rm.visalib}")
    resources = list(rm.list_resources())
    print(f"  resources    : {resources if resources else '(empty)'}")
except Exception as e:
    print(f"VISA backend  : FAILED — {e}")

# 3. try Keysight VISA DLL explicitly
KEYSIGHT_PATHS = [
    r"C:\Program Files\Keysight\IO Libraries Suite\bin\visa32.dll",
    r"C:\Program Files\Keysight\IO Libraries Suite\bin\visa64.dll",
    r"C:\Program Files (x86)\Keysight\IO Libraries Suite\bin\visa32.dll",
    r"C:\Program Files\Agilent\IO Libraries Suite\bin\visa32.dll",
    r"C:\Program Files (x86)\Agilent\IO Libraries Suite\bin\visa32.dll",
]
print("\nKeysight VISA DLL search:")
for p in KEYSIGHT_PATHS:
    if Path(p).exists():
        print(f"  FOUND: {p}")
        try:
            rm_ks = pyvisa.ResourceManager(p)
            res_ks = list(rm_ks.list_resources())
            print(f"    resources: {res_ks if res_ks else '(empty)'}")
        except Exception as e:
            print(f"    open failed: {e}")
    else:
        print(f"  not found: {p}")

# 4. try pyvisa-py
print("\npyvisa-py:")
try:
    import pyvisa_py
    print(f"  version      : {pyvisa_py.__version__}")
    rm_py = pyvisa.ResourceManager("@py")
    resources_py = list(rm_py.list_resources())
    print(f"  resources    : {resources_py if resources_py else '(empty)'}")
except ImportError:
    print("  NOT INSTALLED  →  pip install pyvisa-py")
except Exception as e:
    print(f"  error — {e}")

# 5. pyusb / libusb
print("\npyusb:")
try:
    import usb.core
    devs = list(usb.core.find(find_all=True))
    print(f"  OK — {len(devs)} USB device(s) visible via libusb")
    agilent = [d for d in devs if d.idVendor == 0x0957]
    if agilent:
        for d in agilent:
            print(f"  Agilent/Keysight: VID=0x{d.idVendor:04X} PID=0x{d.idProduct:04X}")
    else:
        print("  No Agilent/Keysight (VID 0x0957) device found")
except ImportError:
    print("  NOT INSTALLED  →  pip install pyusb")
except Exception as e:
    print(f"  error — {e}")

# 6. check libusb DLL directly
print("\nlibusb DLL search:")
LIBUSB_PATHS = [
    r"C:\Windows\System32\libusb-1.0.dll",
    r"C:\Windows\SysWOW64\libusb-1.0.dll",
    r"C:\Program Files\Keysight\IO Libraries Suite\bin\libusb-1.0.dll",
]
for p in LIBUSB_PATHS:
    print(f"  {'FOUND' if Path(p).exists() else 'not found'}: {p}")

print("\nDone.")
