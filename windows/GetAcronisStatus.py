#!/usr/bin/env python3

import subprocess
import sys
import re
from datetime import datetime, timedelta

def run_acronis_command(command):
    """Executes an Acronis command by specifying the full path to acrocmd."""
    full_command = f'"C:\\Program Files\\BackupClient\\CommandLineTool\\acrocmd.exe" {command}'
    
    try:
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing Acronis command: {e}")
        print(f"Error output: {e.stderr}")
        return None

def extract_backup_info(output):
    """Extracts the plan name, status, and date of the last backup from the raw format."""
    parts = output.split('\t')
    
    if len(parts) < 4:
        print("Unable to extract backup information.")
        sys.exit(1)

    plan_name = parts[0]
    last_status = parts[2]
    last_date = parts[3]

    return plan_name, last_status, last_date

def get_last_backup_status():
    """Checks the status of the last Acronis backup plan."""

    command = "list plans --output raw"
    output = run_acronis_command(command)

    if output is None:
        return 1

    if not output.strip():
        print("No backup plan found.")
        return 1

    raw_output = output.splitlines()[0]

    plan_name, last_status, last_date = extract_backup_info(raw_output)

    print(f"Plan name: {plan_name}")
    print(f"Last backup status: {last_status}")
    print(f"Last backup date: {last_date}")

    if last_status.lower() == "error":
        print("The last backup is in error.")
        return 1

    date_formats = ["%d.%m.%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
    parsed_date = None

    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(last_date, date_format)
            break
        except ValueError:
            continue

    if parsed_date is None:
        print("Unable to parse the date of the last backup.")
        return 1

    if datetime.now() - parsed_date > timedelta(days=7):
        print("The last backup is more than 7 days old.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(get_last_backup_status())