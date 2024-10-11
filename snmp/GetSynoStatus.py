#!/usr/bin/python3

import sys
from pysnmp.hlapi import *

def get_human_readable_status(value):
    statuses = {1: "Normal", 2: "Failed"}
    return statuses.get(int(value), "Unknown")

def get_human_readable_temperature(value):
    return f"{value} °C"

def get_human_readable_power_status(value):
    statuses = {1: "Normal", 2: "Failed"}
    return statuses.get(int(value), "Unknown")

def get_human_readable_fan_status(value):
    statuses = {1: "Normal", 2: "Failed"}
    return statuses.get(int(value), "Unknown")

def get_human_readable_disk_status(value):
    statuses = {
        1: "Normal",
        2: "Initialized",
        3: "Not Initialized",
        4: "System Partition Failed",
        5: "Crashed"
    }
    return statuses.get(int(value), "Unknown")

def get_human_readable_raid_status(value):
    statuses = {
        1: "Normal",
        2: "Repairing",
        3: "Migrating",
        4: "Expanding",
        5: "Deleting",
        6: "Creating",
        7: "Raid Syncing",
        8: "Raid Parity Checking",
        9: "Raid Assembling",
        10: "Canceling",
        11: "Degrade",
        12: "Crashed",
        13: "Data Scrubbing",
        14: "Raid Deploying",
        15: "Raid UnDeploying",
        16: "Raid Mount Cache",
        17: "Raid Unmount Cache",
        18: "Raid Expanding Unfinished SHR",
        19: "Raid Convert SHR To Pool",
        20: "Raid Migrate SHR1 To SHR2",
        21: "Raid Unknown Status"
    }
    return statuses.get(int(value), "Unknown")

def get_human_readable_memory(value):
    try:
        return f"{float(value) / (1024):.2f} MB"
    except (ValueError, TypeError):
        return "Invalid value"

def get_storage_indexes(nas_ip, community_string):
    storage_indexes = []
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community_string, mpModel=0),
        UdpTransportTarget((nas_ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1.2.1.25.2.3.1.3')),  # hrStorageDescr
        lexicographicMode=False
    )

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication:
            print(f"SNMP Error: {errorIndication}")
            break
        elif errorStatus:
            print(f"SNMP Error: {errorStatus}")
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                oid_str = str(oid)
                # Extract the index at the end of the OID
                index = oid_str.split('.')[-1]
                descr = str(value)
                storage_indexes.append((index, descr))
    return storage_indexes

def get_volume_info(nas_ip, community_string, storage_index, volume_name):
    # OIDs for the volume
    base_oid = f'1.3.6.1.2.1.25.2.3.1'
    descr_oid = f'{base_oid}.3.{storage_index}'
    allocation_units_oid = f'{base_oid}.4.{storage_index}'
    size_oid = f'{base_oid}.5.{storage_index}'
    used_oid = f'{base_oid}.6.{storage_index}'

    # Get volume description
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(), CommunityData(community_string, mpModel=0),
               UdpTransportTarget((nas_ip, 161)), ContextData(),
               ObjectType(ObjectIdentity(descr_oid)))
    )

    if errorIndication or errorStatus:
        print(f"Error retrieving hrStorageDescr: {errorIndication or errorStatus}")
        return

    hrStorageDescr = str(varBinds[0][1])

    # Get allocation unit
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(), CommunityData(community_string, mpModel=0),
               UdpTransportTarget((nas_ip, 161)), ContextData(),
               ObjectType(ObjectIdentity(allocation_units_oid)))
    )

    if errorIndication or errorStatus:
        print(f"Error retrieving hrStorageAllocationUnits: {errorIndication or errorStatus}")
        return

    hrStorageAllocationUnits = int(varBinds[0][1])

    # Get total size
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(), CommunityData(community_string, mpModel=0),
               UdpTransportTarget((nas_ip, 161)), ContextData(),
               ObjectType(ObjectIdentity(size_oid)))
    )

    if errorIndication or errorStatus:
        print(f"Error retrieving hrStorageSize: {errorIndication or errorStatus}")
        return

    hrStorageSize = int(varBinds[0][1])

    # Get used space
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(), CommunityData(community_string, mpModel=0),
               UdpTransportTarget((nas_ip, 161)), ContextData(),
               ObjectType(ObjectIdentity(used_oid)))
    )

    if errorIndication or errorStatus:
        print(f"Error retrieving hrStorageUsed: {errorIndication or errorStatus}")
        return

    hrStorageUsed = int(varBinds[0][1])

    # Calculate actual sizes
    total_bytes = hrStorageSize * hrStorageAllocationUnits
    used_bytes = hrStorageUsed * hrStorageAllocationUnits
    free_bytes = total_bytes - used_bytes
    used_percentage = (used_bytes / total_bytes) * 100 if total_bytes > 0 else 0

    # Convert sizes to readable units
    total_gb = total_bytes / (1024 ** 3)
    used_gb = used_bytes / (1024 ** 3)
    free_gb = free_bytes / (1024 ** 3)

    print(f"\nInformation for volume '{volume_name}' (Index {storage_index}):")
    print(f"-----------------------------------------------")
    print(f"Volume description : {hrStorageDescr}")
    print(f"Total size         : {total_gb:.2f} GB")
    print(f"Used space         : {used_gb:.2f} GB")
    print(f"Free space         : {free_gb:.2f} GB")
    print(f"Used percentage    : {used_percentage:.2f}%")

    return used_percentage  # Return the used percentage for severity assessment

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 script.py <NAS_IP> [COMMUNITY_STRING]")
        sys.exit(1)

    nas_ip = sys.argv[1]
    community_string = sys.argv[2] if len(sys.argv) == 3 else 'public'

    # Initialize severity level
    severity_level = 0  # 0: OK, 1: Urgent, 2: Information, 3: Warning

    oids = {
        'Model': ('1.3.6.1.4.1.6574.1.5.3.0', str),
        'Serial Number': ('1.3.6.1.4.1.6574.1.5.2.0', str),
        'DSM Version': ('1.3.6.1.4.1.6574.1.5.1.0', str),
        'System Status': ('1.3.6.1.4.1.6574.1.1.0', get_human_readable_status),
        'System Temperature': ('1.3.6.1.4.1.6574.1.2.0', get_human_readable_temperature),
        'Power Status': ('1.3.6.1.4.1.6574.1.3.0', get_human_readable_power_status),
        'System Fan Status': ('1.3.6.1.4.1.6574.1.4.1.0', get_human_readable_fan_status),
        'CPU Fan Status': ('1.3.6.1.4.1.6574.1.4.2.0', get_human_readable_fan_status),
        'Disk 1 Status': ('1.3.6.1.4.1.6574.2.1.1.5.0', get_human_readable_disk_status),
        'Disk 2 Status': ('1.3.6.1.4.1.6574.2.1.1.5.1', get_human_readable_disk_status),
        'Disk 1 Temperature': ('1.3.6.1.4.1.6574.2.1.1.6.0', get_human_readable_temperature),
        'Disk 2 Temperature': ('1.3.6.1.4.1.6574.2.1.1.6.1', get_human_readable_temperature),
        'CPU Usage': ('1.3.6.1.4.1.2021.11.9.0', lambda x: f"{x}%"),
        'Total Memory': ('1.3.6.1.4.1.2021.4.5.0', get_human_readable_memory),
        'Available Memory': ('1.3.6.1.4.1.2021.4.6.0', get_human_readable_memory),
        'Update Available': ('1.3.6.1.4.1.6574.1.5.4.0', lambda x: "Yes" if int(x) == 1 else "No"),
        'RAID Index': ('1.3.6.1.4.1.6574.3.1.1.1.0', lambda x: f"RAID {x}"),
        'RAID Name': ('1.3.6.1.4.1.6574.3.1.1.2.0', str),
        'RAID Status': ('1.3.6.1.4.1.6574.3.1.1.3.0', get_human_readable_raid_status),
        'RAID Hotspare Count': ('1.3.6.1.4.1.6574.3.1.1.6.0', lambda x: f"{x} disks" if int(x) >= 0 else "Error"),
    }

    print(f"Synology NAS Status ({nas_ip}):")
    print("---------------------------------")

    for name, (oid, formatter) in oids.items():
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community_string, mpModel=0),
            UdpTransportTarget((nas_ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

        if errorIndication:
            print(f"{name}: Error - {errorIndication}")
            severity_level = max(severity_level, 1)  # Set to urgent
        elif errorStatus:
            print(f"{name}: Error - {errorStatus}")
            severity_level = max(severity_level, 1)  # Set to urgent
        else:
            for varBind in varBinds:
                value = varBind[1]
                try:
                    formatted_value = formatter(value) if callable(formatter) else value
                    print(f"{name}: {formatted_value}")

                    # Assess severity based on specific conditions
                    if name == 'System Status' and formatted_value != 'Normal':
                        severity_level = max(severity_level, 1)  # Urgent
                    elif 'Disk' in name and 'Status' in name:
                        if formatted_value == 'Crashed':
                            severity_level = max(severity_level, 1)  # Urgent
                        elif formatted_value != 'Normal':
                            severity_level = max(severity_level, 3)  # Warning
                    elif name == 'RAID Status':
                        if formatted_value == 'Crashed':
                            severity_level = max(severity_level, 1)  # Urgent
                        elif formatted_value != 'Normal':
                            severity_level = max(severity_level, 3)  # Warning
                    elif name == 'Update Available' and formatted_value == 'Yes':
                        severity_level = max(severity_level, 2)  # Information
                    elif 'Volume' in name and 'Usage' in name:
                        usage = float(formatted_value.strip('%'))
                        if usage > 90:
                            severity_level = max(severity_level, 1)  # Urgent
                        elif usage > 80:
                            severity_level = max(severity_level, 3)  # Warning

                except Exception as e:
                    print(f"{name}: Error during formatting - {str(e)}")
                    severity_level = max(severity_level, 1)  # Set to urgent

    # Discover available volumes
    print("\nDiscovering available volumes:")
    storage_indexes = get_storage_indexes(nas_ip, community_string)

    # Filter relevant volumes (e.g., those with description containing '/volume')
    volume_indexes = [(index, descr) for index, descr in storage_indexes if '/volume' in descr]

    if volume_indexes:
        for index, descr in volume_indexes:
            used_percentage = get_volume_info(nas_ip, community_string, index, descr)
            if used_percentage is not None and used_percentage >= 90:
                severity_level = max(severity_level, 3)  # Warning if disk usage >= 90%
    else:
        print("No relevant volumes found.")

    print("---------------------------------")

    # Exit with appropriate code
    sys.exit(severity_level)
