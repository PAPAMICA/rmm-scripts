#!/usr/bin/env python3

import subprocess
import sys
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from datetime import datetime
import locale

def check_bitdefender_installed():
    # Check via PowerShell if Bitdefender is installed and activated
    cmd = (
        'powershell -Command "Get-WmiObject -Namespace root\\SecurityCenter2 -Class AntiVirusProduct '
        '| Where-Object { $_.displayName -like \'*Bitdefender*\' } | Select-Object displayName,productState | ConvertTo-Json"'
    )
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, encoding='utf-8')

    if result.returncode != 0:
        print("Error while checking Bitdefender.")
        sys.exit(1)

    try:
        antivirus_info = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Unable to decode JSON response.")
        sys.exit(1)

    # Check if Bitdefender is installed (name containing "Bitdefender")
    if not antivirus_info or "Bitdefender" not in antivirus_info.get("displayName", ""):
        print(f"Antivirus found: {antivirus_info.get('displayName', 'Unknown')}")
        print("Bitdefender is not installed.")
        sys.exit(1)

    # Check Bitdefender status
    product_state = int(antivirus_info.get('productState', 0))
    if product_state & 0x1000:  # Bitdefender is activated
        return True
    else:
        print("Bitdefender is installed but disabled.")
        sys.exit(1)


def get_last_scan_info():
    # Path to Bitdefender logs
    log_dir = Path(r"C:\Program Files\Bitdefender\Endpoint Security\Logs\system")

    # Check if the log folder exists
    if not log_dir.exists():
        print("Bitdefender log folder does not exist.")
        sys.exit(1)

    # Recursive search for the most recent XML scan file
    try:
        xml_files = list(log_dir.rglob('*.xml'))
        if not xml_files:
            print("No scan file found.")
            sys.exit(1)

        # Sort files by modification date
        latest_xml = max(xml_files, key=lambda x: x.stat().st_mtime)
    except Exception as e:
        print(f"Error while searching for scan files: {e}")
        sys.exit(1)

    # Read and parse the XML file
    try:
        tree = ET.parse(latest_xml)
        root = tree.getroot()

        # Extract scan information
        creation_date = root.attrib.get('creationDate', 'Not available')
        scan_summary = root.find('ScanSummary')
        if scan_summary is not None:
            scanned = scan_summary.find('.//TypeSummary[@type="0"]').attrib.get('scanned', '0')
            infected = scan_summary.find('.//TypeSummary[@type="0"]').attrib.get('infected', '0')
            suspicious = scan_summary.find('.//TypeSummary[@type="0"]').attrib.get('suspicious', '0')

            try:
                last_scan_date = datetime.strptime(creation_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    last_scan_date = datetime.strptime(creation_date, "%A %d %B %Y %H:%M:%S")
                except ValueError:
                    try:
                        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
                        last_scan_date = datetime.strptime(creation_date, "%A %d %B %Y %H:%M:%S")
                    except ValueError:
                        print(f"Error: Unable to parse the date '{creation_date}'")
                        sys.exit(1)
                    finally:
                        locale.setlocale(locale.LC_TIME, '')
            current_date = datetime.now()
            time_difference = current_date - last_scan_date

            if time_difference.days > 7:
                sys.exit(2)
            else:
                print(f"Last scan: {creation_date}")
                print(f"Scanned: {scanned}")
                print(f"Infected: {infected}")
                print(f"Suspicious: {suspicious}")
            if time_difference.days > 7:
                sys.exit(2)
        else:
            print("No scan summary information found.")
            sys.exit(1)

    except ET.ParseError:
        print("Error while parsing the XML file.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":

    # Check if Bitdefender is installed and activated
    if check_bitdefender_installed():
        get_last_scan_info()
