#!/usr/bin/python3
import re
import subprocess
import sys
from datetime import datetime, timedelta


def get_installed_software(days=1):
    # Command to list installed software
    cmd = "wmic product get Name, InstallDate"
    result = subprocess.run(cmd, capture_output=True, text=True)

    # If the command fails
    if result.returncode != 0:
        print("Error executing the command.")
        sys.exit(1)

    # Clean up results by removing empty lines
    software_list = [
        line.strip() for line in result.stdout.splitlines() if line.strip()
    ]

    # Remove the first line which is the header
    software_list = software_list[1:]

    installed_software = []
    # Calculate the limit date
    limit_date = datetime.now() - timedelta(days=days)

    # Iterate through installed software
    for software in software_list:
        # Search for name and installation date
        match = re.match(r"(\d{8})\s+(.+)", software)
        if match:
            install_date = match.group(1).strip()
            name = match.group(2).strip()
            try:
                install_date_obj = datetime.strptime(install_date, "%Y%m%d")
            except ValueError:
                continue  # Ignore if the date is not valid

            # Check if the installation date is within the time frame
            if install_date_obj >= limit_date:
                installed_software.append(name)

    return installed_software


if __name__ == "__main__":
    # Initialize parameters
    days = 1
    check_mode = False

    # Parse arguments
    for arg in sys.argv[1:]:
        if arg == "--check":
            check_mode = True
        else:
            try:
                days = int(arg)
            except ValueError:
                print(f"Invalid argument: {arg}")
                sys.exit(1)

    installed_software = get_installed_software(days)

    if check_mode:
        # Check mode: return code 0 if nothing to report, 1 if software installed
        if installed_software:
            print(f"Software installed in the last {days} days:")
            for software in installed_software:
                print(f"- {software}")
            sys.exit(1)
        else:
            print("Nothing to report")
            sys.exit(0)
    else:
        # Normal mode: display software
        if installed_software:
            print(f"Software installed in the last {days} days:")
            for software in installed_software:
                print(f"- {software}")
        else:
            print("Nothing to report")
