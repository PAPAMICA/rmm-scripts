#!/usr/bin/env python3

import subprocess
import sys


def main():
    try:
        result = subprocess.run(
            ["docker", "ps", "-q"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            sys.exit(3)
        container_ids = result.stdout.strip().split("\n")
        num_containers = len([cid for cid in container_ids if cid])
        print(num_containers)
        if num_containers == 0:
            sys.exit(1)  # Alarm if no containers are running
        else:
            sys.exit(0)
    except Exception:
        sys.exit(3)


if __name__ == "__main__":
    main()
