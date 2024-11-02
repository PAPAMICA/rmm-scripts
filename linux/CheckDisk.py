#!/usr/bin/env python3

import sys


def main():
    try:
        import psutil
    except ImportError:
        sys.exit(3)
    try:
        disk_path = "/"
        if len(sys.argv) > 1:
            disk_path = sys.argv[1]
        disk = psutil.disk_usage(disk_path)
        disk_percent = disk.percent
        print(int(disk_percent))
        if disk_percent > 90:
            sys.exit(1)  # Alarm
        elif disk_percent > 75:
            sys.exit(2)  # Warning
        else:
            sys.exit(0)  # OK
    except Exception:
        sys.exit(3)


if __name__ == "__main__":
    main()
