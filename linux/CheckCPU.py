#!/usr/bin/env python3

import sys


def main():
    try:
        import psutil
    except ImportError:
        sys.exit(3)
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        print(int(cpu_percent))
        if cpu_percent > 90:
            sys.exit(1)  # Alarm
        elif cpu_percent > 75:
            sys.exit(2)  # Warning
        else:
            sys.exit(0)  # OK
    except Exception:
        sys.exit(3)


if __name__ == "__main__":
    main()
