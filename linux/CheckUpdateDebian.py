#!/usr/bin/env python3

import re
import subprocess
import sys


def main():
    try:
        result = subprocess.run(
            ["apt-get", "-s", "upgrade"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            sys.exit(3)
        # Parse output
        # Looking for line like:
        # N upgraded, M newly installed, O to remove and P not upgraded.
        match = re.search(r"(\d+)\supgraded", result.stdout)
        if match:
            num_upgrades = int(match.group(1))
            print(num_upgrades)
            if num_upgrades > 10:
                sys.exit(1)  # Alarm if more than 10 updates pending
            elif num_upgrades > 0:
                sys.exit(2)  # Warning if updates are pending
            else:
                sys.exit(0)  # OK
        else:
            print(0)
            sys.exit(0)
    except Exception:
        sys.exit(3)


if __name__ == "__main__":
    main()
