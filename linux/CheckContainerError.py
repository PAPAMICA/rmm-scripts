#!/usr/bin/env python3

import subprocess
import sys


def main():
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "-f", "status=exited", "-q"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            sys.exit(3)
        container_ids = result.stdout.strip().split("\n")
        num_failed = len([cid for cid in container_ids if cid])
        print(num_failed)
        if num_failed > 0:
            sys.exit(1)  # Alarm if any containers have failed
        else:
            sys.exit(0)
    except Exception:
        sys.exit(3)


if __name__ == "__main__":
    main()
