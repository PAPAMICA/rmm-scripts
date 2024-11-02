#!/usr/bin/env python3

import sys


def main():
    try:
        import psutil
    except ImportError:
        sys.exit(3)
    try:
        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        print(int(ram_percent))
        if ram_percent > 90:
            sys.exit(1)  # Alarm
        elif ram_percent > 75:
            sys.exit(2)  # Warning
        else:
            sys.exit(0)  # OK
    except Exception:
        sys.exit(3)


if __name__ == "__main__":
    main()