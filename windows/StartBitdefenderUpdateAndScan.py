#!/usr/bin/env python3

import subprocess
import sys
import time

def run_bitdefender_command(command):
    """Executes a Bitdefender command in the installation directory."""
    bitdefender_path = r"C:\Program Files\Bitdefender\Endpoint Security"
    full_command = f'"{bitdefender_path}\\product.console.exe" /c {command}'
    
    result = subprocess.run(full_command, capture_output=True, text=True, shell=True)

    if result.returncode != 0:
        print(f"Error executing command '{command}': {result.stderr}")
        sys.exit(1)

    print(f"Command '{command}' executed successfully.")
    return result.stdout

def update_bitdefender():
    """Starts a Bitdefender update and waits for its completion."""
    print("Starting Bitdefender update...")
    output = run_bitdefender_command("StartUpdate")
    
    while "error 0" not in output:
        print("Update in progress...")
        time.sleep(30)  # Wait 30 seconds before checking again
        output = run_bitdefender_command("GetUpdateStatus")
    
    print("Update completed successfully.")

def scan_bitdefender():
    """Starts a full system scan with Bitdefender and displays the results."""
    print("Starting full Bitdefender scan...")
    scan_command = 'FileScan.OnDemand.RunScanTask custom ' \
                   'infectedAction1=disinfect infectedAction2=quarantine ' \
                   'suspiciousAction1=quarantine suspiciousAction2=delete ' \
                   'scanBootSectors=true scanRegistry=true scanMemory=true ' \
                   'smartScan=false scanRootKits=true scanKeyloggers=true ' \
                   'scanPUA=true scanArchives=true extensionType=all ' \
                   'lowPriority=false'
    run_bitdefender_command(scan_command)
    print("Full scan completed. Displaying results...")
    get_last_scan_info()

def get_last_scan_info():
    """Retrieves and displays information from the last scan."""
    import xml.etree.ElementTree as ET
    from pathlib import Path
    from datetime import datetime
    import locale

    log_dir = Path(r"C:\Program Files\Bitdefender\Endpoint Security\Logs\system")

    if not log_dir.exists():
        print("Bitdefender log folder does not exist.")
        sys.exit(1)

    try:
        xml_files = list(log_dir.rglob('*.xml'))
        if not xml_files:
            print("No scan file found.")
            sys.exit(1)

        latest_xml = max(xml_files, key=lambda x: x.stat().st_mtime)
    except Exception as e:
        print(f"Error while searching for scan files: {e}")
        sys.exit(1)

    try:
        tree = ET.parse(latest_xml)
        root = tree.getroot()

        creation_date = root.attrib.get('creationDate', 'Not available')
        scan_summary = root.find('ScanSummary')
        if scan_summary is not None:
            scanned = scan_summary.find('.//TypeSummary[@type="0"]').attrib.get('scanned', '0')
            infected = scan_summary.find('.//TypeSummary[@type="0"]').attrib.get('infected', '0')
            suspicious = scan_summary.find('.//TypeSummary[@type="0"]').attrib.get('suspicious', '0')

            print(f"Last scan: {creation_date}")
            print(f"Scanned: {scanned}")
            print(f"Infected: {infected}")
            print(f"Suspicious: {suspicious}")
        else:
            print("No scan summary information found.")

    except ET.ParseError:
        print("Error while parsing the XML file.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Start Bitdefender update and wait for its completion
    update_bitdefender()

    # Start a scan after the update is finished
    scan_bitdefender()
