#!/usr/bin/env python3

import sys
from pysnmp.hlapi import *

def get_snmp_data(ip, community, oid):
    """
    Retrieves an SNMP value for a given OID.
    """
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),  # SNMP v1
        UdpTransportTarget((ip, 161), timeout=2, retries=2),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        # print(f"SNMP Error: {errorIndication}")
        return None
    elif errorStatus:
        # print(f"SNMP Error: {errorStatus.prettyPrint()}")
        return None
    else:
        for varBind in varBinds:
            return varBind[1]
    return None

def get_snmp_table(ip, community, oid):
    """
    Retrieves an SNMP table for a given OID.
    """
    result = {}
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((ip, 161), timeout=2, retries=2),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False
    ):
        if errorIndication:
            # print(f"SNMP Error: {errorIndication}")
            break
        elif errorStatus:
            # print(f"SNMP Error: {errorStatus.prettyPrint()}")
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                oid_str = oid.prettyPrint()
                oid_index = oid_str.split('.')[-1]
                result[oid_index] = value
    return result

def check_wifi_ap_status(ip, community):
    severity_level = 0  # 0: OK, 1: Warning, 2: Critical

    # OIDs for device information
    oids = {
        'Device Name': ('1.3.6.1.2.1.1.5.0', str),        # sysName
        'Description': ('1.3.6.1.2.1.1.1.0', str),        # sysDescr
        'Uptime': ('1.3.6.1.2.1.1.3.0', int),             # sysUpTime
        'Contact': ('1.3.6.1.2.1.1.4.0', str),            # sysContact
        'Location': ('1.3.6.1.2.1.1.6.0', str),           # sysLocation
    }

    print(f"Wi-Fi Access Point Status ({ip}):")
    print("---------------------------------")

    # Retrieve and display basic information
    for name, (oid, data_type) in oids.items():
        value = get_snmp_data(ip, community, oid)
        if value is None:
            severity_level = max(severity_level, 1)
            print(f"{name}: Data not available")
            continue

        if data_type == int:
            try:
                value = int(value)
                if name == 'Uptime':
                    days = value // (100 * 60 * 60 * 24)
                    hours = (value // (100 * 60 * 60)) % 24
                    minutes = (value // (100 * 60)) % 60
                    seconds = (value // 100) % 60
                    value = f"{days}d {hours}h {minutes}m {seconds}s"
            except (ValueError, TypeError):
                print(f"Warning: Unable to convert {name} to integer. Received: {value.prettyPrint()}")
                severity_level = max(severity_level, 1)
                continue
        else:
            value = str(value).strip()

        print(f"{name}: {value}")

    # Retrieve interface information
    print("\nNetwork Interfaces:")
    interfaces = {}

    # OIDs for interfaces
    if_index_oid = '1.3.6.1.2.1.2.2.1.1'        # ifIndex
    if_descr_oid = '1.3.6.1.2.1.2.2.1.2'        # ifDescr
    if_type_oid = '1.3.6.1.2.1.2.2.1.3'         # ifType
    if_mtu_oid = '1.3.6.1.2.1.2.2.1.4'          # ifMtu
    if_speed_oid = '1.3.6.1.2.1.2.2.1.5'        # ifSpeed
    if_phys_addr_oid = '1.3.6.1.2.1.2.2.1.6'    # ifPhysAddress
    if_admin_status_oid = '1.3.6.1.2.1.2.2.1.7' # ifAdminStatus
    if_oper_status_oid = '1.3.6.1.2.1.2.2.1.8'  # ifOperStatus

    # Retrieve the interface table
    descr_table = get_snmp_table(ip, community, if_descr_oid)
    admin_status_table = get_snmp_table(ip, community, if_admin_status_oid)
    oper_status_table = get_snmp_table(ip, community, if_oper_status_oid)

    # Build the interface dictionary
    for idx in descr_table:
        index = int(idx)
        descr = str(descr_table[idx])
        admin_status = int(admin_status_table.get(idx, 2))  # 2 = Down if not available
        oper_status = int(oper_status_table.get(idx, 2))    # 2 = Down if not available

        interfaces[index] = {
            'description': descr,
            'admin_status': admin_status,
            'oper_status': oper_status,
        }

    # Display active interfaces
    if interfaces:
        for idx in sorted(interfaces):
            data = interfaces[idx]
            descr = data['description']
            admin_status = 'Up' if data['admin_status'] == 1 else 'Down'
            oper_status = 'Up' if data['oper_status'] == 1 else 'Down'

            # Display only operational interfaces
            if data['oper_status'] == 1:
                print(f"Interface {idx} - {descr}: Admin = {admin_status}, Operational = {oper_status}")
    else:
        print("No interfaces detected.")
        severity_level = max(severity_level, 1)

    # Retrieve the number of connected clients (if available)
    print("\nConnected Clients:")
    # Specific OID for the number of clients (must be adjusted according to the manufacturer)
    num_clients_oid = '1.3.6.1.4.1.11863.10.1.2.1.0'  # Example OID for the number of clients

    num_clients = get_snmp_data(ip, community, num_clients_oid)
    if num_clients is not None:
        print(f"Number of connected clients: {num_clients}")
    else:
        print("Number of connected clients: Data not available")
        severity_level = max(severity_level, 1)

    print("---------------------------------")
    sys.exit(severity_level)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 wifi_ap_script.py <DEVICE_IP_ADDRESS> [COMMUNITY_STRING]")
        sys.exit(1)

    device_ip = sys.argv[1]
    community_string = sys.argv[2] if len(sys.argv) == 3 else 'public'

    check_wifi_ap_status(device_ip, community_string)
