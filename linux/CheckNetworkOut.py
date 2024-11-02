#!/usr/bin/env python3

import sys
import time


def main():
    try:
        import psutil
    except ImportError:
        sys.exit(3)
    try:
        net1 = psutil.net_io_counters()
        time.sleep(1)
        net2 = psutil.net_io_counters()
        bytes_sent = net2.bytes_sent - net1.bytes_sent
        print(bytes_sent)
        if bytes_sent > 100000000:  # Alarm if outgoing > 100MB/s
            sys.exit(1)
        elif bytes_sent > 50000000:  # Warning if outgoing > 50MB/s
            sys.exit(2)
        else:
            sys.exit(0)
    except Exception:
        sys.exit(3)


if __name__ == "__main__":
    main()
