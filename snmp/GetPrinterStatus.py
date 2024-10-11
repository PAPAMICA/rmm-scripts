#!/usr/bin/python3

import sys
from pysnmp.hlapi import *
from pyasn1.type.univ import Integer, OctetString

def get_snmp_data(ip, community, oid):
    """
    Retrieves an SNMP value for a given OID.
    """
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((ip, 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        print(f"SNMP Error: {errorIndication}")
        return None
    elif errorStatus:
        print(f"SNMP Error: {errorStatus.prettyPrint()}")
        return None
    else:
        for varBind in varBinds:
            return varBind[1]
    return None

def check_printer_status(ip, community):
    severity_level = 0  # 0: OK, 1: Critical, 2: Information, 3: Warning

    # OIDs for printer information
    oids = {
        'Manufacturer': ('1.3.6.1.2.1.1.1.0', str),
        'Model': ('1.3.6.1.2.1.25.3.2.1.3.1', str),
        'Serial Number': ('1.3.6.1.2.1.43.5.1.1.17.1', str),
        'Printer Status': ('1.3.6.1.2.1.25.3.5.1.1.1', int),
        'Pages Printed': ('1.3.6.1.2.1.43.10.2.1.4.1.1', int),
        'Printer Name': ('1.3.6.1.2.1.1.5.0', str),
        'Location': ('1.3.6.1.2.1.1.6.0', str),
        'Contact': ('1.3.6.1.2.1.1.4.0', str),
        'MAC Address': ('1.3.6.1.2.1.2.2.1.6.1', str),
    }

    # Possible printer statuses
    printer_statuses = {
        1: 'Other',
        2: 'Unknown',
        3: 'Idle',
        4: 'Printing',
        5: 'Warmup'
    }

    print(f"Printer Status ({ip}):")
    print("---------------------------------")

    # Retrieving and displaying basic information
    for name, (oid, data_type) in oids.items():
        value = get_snmp_data(ip, community, oid)
        if value is None or value == '':
            severity_level = max(severity_level, 1)  # Critical if no data
            print(f"{name}: Data not available")
            continue

        if data_type == int:
            try:
                value = int(value)
            except (ValueError, TypeError):
                print(f"Warning: Unable to convert {name} to integer. Received: {value.prettyPrint()}")
                severity_level = max(severity_level, 1)
                continue
        else:
            value = str(value).strip()

        if name == 'Printer Status':
            status = printer_statuses.get(value, 'Unknown')
            print(f"{name}: {status}")
            if status in ['Other', 'Unknown']:
                severity_level = max(severity_level, 3)  # Warning
            elif status == 'Printing':
                pass  # All good
            elif status == 'Idle':
                pass  # All good
            else:
                severity_level = max(severity_level, 2)  # Information
        elif name == 'MAC Address':
            try:
                mac = ':'.join([f'{ord(x):02x}' for x in value])
                print(f"{name}: {mac}")
            except TypeError:
                print(f"{name}: Invalid format")
                severity_level = max(severity_level, 1)
        else:
            print(f"{name}: {value}")

    # Retrieving supply statuses
    # OIDs for supplies
    supplies_description_oid = '1.3.6.1.2.1.43.11.1.1.6'  # prtMarkerSuppliesDescription
    supplies_level_oid = '1.3.6.1.2.1.43.11.1.1.9'       # prtMarkerSuppliesLevel
    supplies_max_capacity_oid = '1.3.6.1.2.1.43.11.1.1.8' # prtMarkerSuppliesMaxCapacity

    supplies = {}

    # Retrieving supply descriptions
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((ip, 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(supplies_description_oid)),
        lexicographicMode=False
    )

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication or errorStatus:
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                index = oid.prettyPrint().split('.')[-1]
                supplies.setdefault(index, {})['description'] = str(value).strip()

    # Retrieving supply levels
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((ip, 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(supplies_level_oid)),
        lexicographicMode=False
    )

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication or errorStatus:
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                index = oid.prettyPrint().split('.')[-1]
                try:
                    level = int(value)
                except (ValueError, TypeError):
                    level = None
                supplies.setdefault(index, {})['level'] = level

    # Retrieving supply maximum capacities
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((ip, 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(supplies_max_capacity_oid)),
        lexicographicMode=False
    )

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication or errorStatus:
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                index = oid.prettyPrint().split('.')[-1]
                try:
                    max_capacity = int(value)
                except (ValueError, TypeError):
                    max_capacity = None
                supplies.setdefault(index, {})['max_capacity'] = max_capacity

    # Displaying supply statuses
    if supplies:
        print("\nSupply Statuses:")
        for index in supplies:
            data = supplies[index]
            description = data.get('description', 'Unknown')
            level = data.get('level', None)
            max_capacity = data.get('max_capacity', None)

            if level is None or max_capacity is None or max_capacity == 0:
                status = "Unknown"
            elif level == -3:
                status = "Unknown"
            elif level == -2:
                status = "Empty"
                severity_level = max(severity_level, 1)  # Critical
            elif level == -1:
                status = "Low"
                severity_level = max(severity_level, 3)  # Warning
            else:
                percentage = (level / max_capacity) * 100
                status = f"{percentage:.1f}%"
            print(f"{description}: {status}")
    else:
        print("No supplies detected.")

    print("---------------------------------")

    # Return the appropriate exit code
    sys.exit(severity_level)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 script.py <PRINTER_IP> [COMMUNITY_STRING]")
        sys.exit(1)

    printer_ip = sys.argv[1]
    community_string = sys.argv[2] if len(sys.argv) == 3 else 'public'

    check_printer_status(printer_ip, community_string)
