#!/usr/bin/env python3

import subprocess
import sys
import os
import re
from datetime import datetime, timedelta


def find_acrocmd_path():
    """Finds the path to acrocmd.exe in BackupClient or Acronis directories."""
    possible_paths = [
        r"C:\Program Files\BackupClient\CommandLineTool\acrocmd.exe",
        r"C:\Program Files\Acronis\CommandLineTool\acrocmd.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def run_acronis_command(command):
    """Executes an Acronis command by specifying the full path to acrocmd."""
    acrocmd_path = find_acrocmd_path()

    if acrocmd_path is None:
        print("Error: acrocmd.exe not found in BackupClient or Acronis directories.")
        return None

    full_command = f'"{acrocmd_path}" {command}'

    try:
        result = subprocess.run(
            full_command, capture_output=True, text=True, check=True, shell=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing Acronis command: {e}")
        print(f"Error output: {e.stderr}")
        return None


def check_running_backup():
    """Checks if a backup is currently running and returns (duration in minutes, progress percentage)."""
    command = "list activities --filter_state=running --output=raw"
    output = run_acronis_command(command)

    if output is None:
        return None

    if not output.strip():
        return None

    # Parse the output to find the start date/time and progress percentage
    # The output format is tab-separated, and the start date is typically in a specific column
    lines = output.splitlines()
    
    # Look for date/time pattern in the format "DD.MM.YYYY HH:MM:SS" or "DD/MM/YYYY HH:MM:SS"
    date_formats = ["%d.%m.%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
    
    # Try to find a date and progress percentage in each line
    for line in lines:
        if not line.strip():
            continue
        
        # Look for progress percentage (e.g., "running 10%" or "10%")
        progress_match = re.search(r'(\d+)%', line)
        progress = None
        if progress_match:
            progress = int(progress_match.group(1))
            
        # Split by tab and try to parse each part as a date
        parts = line.split("\t")
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(part, date_format)
                    # Verify it's a reasonable date (not too old, not in the future)
                    now = datetime.now()
                    if start_date <= now and (now - start_date).days < 30:
                        # Calculate minutes since start
                        elapsed = now - start_date
                        minutes = int(elapsed.total_seconds() / 60)
                        return (minutes, progress)
                except ValueError:
                    continue
    
    return None


def format_duration(minutes):
    """Formats duration in minutes to human-readable format (e.g., 70 min -> 1h 10 min)."""
    if minutes < 60:
        return f"{minutes} min"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {remaining_minutes} min"


def format_time_ago(date_string):
    """Formats the time elapsed since a date to human-readable format (e.g., 2 days, 3h 30 min)."""
    date_formats = ["%d.%m.%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
    parsed_date = None

    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_string, date_format)
            break
        except ValueError:
            continue

    if parsed_date is None:
        return None

    now = datetime.now()
    elapsed = now - parsed_date
    
    total_minutes = int(elapsed.total_seconds() / 60)
    
    if total_minutes < 60:
        return f"{total_minutes} min"
    
    days = elapsed.days
    hours = (elapsed.seconds // 3600)
    minutes = (elapsed.seconds % 3600) // 60
    
    if days > 0:
        if hours == 0 and minutes == 0:
            return f"{days} day{'s' if days > 1 else ''}"
        elif minutes == 0:
            return f"{days} day{'s' if days > 1 else ''}, {hours}h"
        else:
            return f"{days} day{'s' if days > 1 else ''}, {hours}h {minutes} min"
    else:
        if minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {minutes} min"


def extract_backup_info(output):
    """Extracts the plan name, status, and date of the last backup from the raw format."""
    if not output.strip():
        print("No backup plan found.")
        sys.exit(3)

    parts = output.split("\t")

    if len(parts) < 4:
        print("Unable to extract backup information.")
        sys.exit(1)

    plan_name = parts[0]
    last_status = parts[2]
    last_date = parts[3]

    return plan_name, last_status, last_date


def get_last_completed_backup():
    """Gets the last completed backup activity and returns (date, status).
    Filters by activity name 'Sauvegarder' or 'Backup' and uses Start Time and Result columns."""
    command = "list activities --filter_state=completed --output=raw"
    output = run_acronis_command(command)

    if output is None:
        return None, None

    if not output.strip():
        return None, None

    # Parse the output
    # Column structure: Name, Machine, State, Progress, Start Time, Elapsed Time, Estimated Time, GUID, Resource, Result
    lines = output.splitlines()
    
    date_formats = ["%d.%m.%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S"]
    
    # Store all backup activities with their dates to find the most recent one
    backup_activities = []
    
    for line in lines:
        if not line.strip():
            continue
        
        parts = line.split("\t")
        
        # Column 0: Name - filter for "Sauvegarder" or "Backup"
        if len(parts) < 10:
            continue
            
        activity_name = parts[0].strip()
        if activity_name.lower() not in ["sauvegarder", "backup"]:
            continue
        
        # Column 4: Start Time (date)
        if len(parts) > 4:
            start_time_str = parts[4].strip()
            start_date = None
            
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(start_time_str, date_format)
                    # Verify it's a reasonable date (not too old, not in the future)
                    now = datetime.now()
                    if start_date <= now and (now - start_date).days < 365:
                        break
                except ValueError:
                    continue
            
            # Column 9: Result (status)
            result_status = None
            if len(parts) > 9:
                result_status = parts[9].strip()
            
            if start_date:
                backup_activities.append((start_time_str, result_status, start_date))
    
    # Return the most recent backup (latest date)
    if backup_activities:
        # Sort by date (most recent first)
        backup_activities.sort(key=lambda x: x[2], reverse=True)
        return backup_activities[0][0], backup_activities[0][1]
    
    return None, None


def get_last_backup_status():
    """Checks the status of the last Acronis backup plan."""
    
    # Get backup plan information first
    command = "list plans --output raw"
    output = run_acronis_command(command)

    if output is None:
        return 1

    if not output.strip():
        print("No backup plan found.")
        return 1

    raw_output = output.splitlines()[0]

    plan_name, plan_status, _ = extract_backup_info(raw_output)
    
    # Get the last completed backup date and status from activities
    last_date, activity_status = get_last_completed_backup()
    
    # Use activity status if available, otherwise fall back to plan status
    last_status = activity_status if activity_status else plan_status
    
    # Check if a backup is currently running
    running_info = check_running_backup()
    if running_info is not None:
        minutes, progress = running_info
        duration_str = format_duration(minutes)
        if progress is not None:
            print(f"Backup in progress since {duration_str} ({progress}%)")
        else:
            print(f"Backup in progress since {duration_str}")
        print(f"Plan: [{plan_status}] {plan_name}")
        if last_date:
            print(f"Last backup: {last_date}")
        else:
            print("Last backup: No backup yet")
        # Return 1 if backup has been running for more than 24 hours, otherwise return 2
        if minutes > 1440:  # 24 hours = 1440 minutes
            return 1
        return 2

    if last_date:
        time_ago = format_time_ago(last_date)
        if time_ago:
            print(f"Backup {last_status} in {time_ago} ({last_date})")
        else:
            print(f"Backup {last_status} ({last_date})")
    else:
        print(f"Backup {last_status}")
    print(f"Plan: [{plan_status}] {plan_name}")

    if last_status and last_status.lower() in ["error", "failed"]:
        if last_date:
            print(f"The last backup is in error ({last_date})")
        else:
            print("The last backup is in error")
        return 1

    if last_date is None:
        print("No backup yet.")
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
        print("No backup yet.")
        return 1

    if datetime.now() - parsed_date > timedelta(days=7):
        print("The last backup is more than 7 days old.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(get_last_backup_status())
