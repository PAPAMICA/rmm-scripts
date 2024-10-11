#!/usr/bin/env python3

import sys
from pysnmp.hlapi import *
from pyasn1.type.univ import Integer, OctetString

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

def check_device_status(ip, community):
    severity_level = 0  # 0: OK, 1: Warning, 2: Critical

    # OIDs for device information
    oids = {
        'Device Name': ('1.3.6.1.2.1.1.5.0', str),        # sysName
        'Description': ('1.3.6.1.2.1.1.1.0', str),        # sysDescr
        'Uptime': ('1.3.6.1.2.1.1.3.0', int),             # sysUpTime
        'Contact': ('1.3.6.1.2.1.1.4.0', str),            # sysContact
        'Location': ('1.3.6.1.2.1.1.6.0', str),           # sysLocation
        'Services': ('1.3.6.1.2.1.1.7.0', int),           # sysServices
        'MAC Address': ('1.3.6.1.4.1.11863.6.1.1.7.0', str),  # tpSysInfoMacAddr
        'Serial Number': ('1.3.6.1.4.1.11863.6.1.1.8.0', str),  # tpSysInfoSerialNum
        'Hardware Version': ('1.3.6.1.4.1.11863.6.1.1.5.0', str),  # tpSysInfoHardwareVersion
        'Firmware Version': ('1.3.6.1.4.1.11863.6.1.1.6.0', str),  # tpSysInfoFirmwareVersion
    }
    print(f"Device Status ({ip}):")
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

    # Retrieve interface statuses
    interfaces = {}

    # OIDs for interfaces
    if_index_oid = '1.3.6.1.2.1.2.2.1.1'        # ifIndex
    if_descr_oid = '1.3.6.1.2.1.2.2.1.2'        # ifDescr
    if_admin_status_oid = '1.3.6.1.2.1.2.2.1.7' # ifAdminStatus
    if_oper_status_oid = '1.3.6.1.2.1.2.2.1.8'  # ifOperStatus

    # Retrieve the list of interface indices
    indices = []
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),
        UdpTransportTarget((ip, 161), timeout=2, retries=2),
        ContextData(),
        ObjectType(ObjectIdentity(if_index_oid)),
        lexicographicMode=False
    )

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication or errorStatus:
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                index = int(value)
                indices.append(index)

    # For each interface, retrieve information
    for index in indices:
        descr = get_snmp_data(ip, community, f"{if_descr_oid}.{index}")
        admin_status = get_snmp_data(ip, community, f"{if_admin_status_oid}.{index}")
        oper_status = get_snmp_data(ip, community, f"{if_oper_status_oid}.{index}")
        
        # Add OIDs for traffic and IP addresses
        if_in_octets_oid = '1.3.6.1.2.1.2.2.1.10'  # ifInOctets
        if_out_octets_oid = '1.3.6.1.2.1.2.2.1.16'  # ifOutOctets
        if_ip_addr_oid = '1.3.6.1.2.1.4.20.1.1'  # ipAdEntAddr

        in_octets = get_snmp_data(ip, community, f"{if_in_octets_oid}.{index}")
        out_octets = get_snmp_data(ip, community, f"{if_out_octets_oid}.{index}")
        ip_addr = get_snmp_data(ip, community, f"{if_ip_addr_oid}.{index}")

        if descr is None or admin_status is None or oper_status is None:
            continue

        descr = str(descr)
        admin_status = int(admin_status)
        oper_status = int(oper_status)
        in_octets = int(in_octets) if in_octets is not None else 0
        out_octets = int(out_octets) if out_octets is not None else 0

        # Keep only ports that are Up
        if oper_status == 1:
            interfaces[index] = {
                'description': descr,
                'admin_status': admin_status,
                'oper_status': oper_status,
                'in_octets': in_octets,
                'out_octets': out_octets,
            }

    # ASCII representation of ports (front view)
    print("\nASCII representation of ports (X = Up):")
    
    # Determine the total number of switch ports
    max_port = max([int(port['description'].split('/')[-1]) for port in interfaces.values() if 'gigabitEthernet' in port['description']], default=0)
    ports_per_row = max_port // 2  # Number of ports per line

    # Function to generate a separator line
    def generate_separator(width):
        return '+---' * width + '+'

    # Generate ASCII representation
    for row in range((max_port + ports_per_row - 1) // ports_per_row):
        # Display port numbers
        print(generate_separator(ports_per_row))
        port_labels = '|'
        for i in range(ports_per_row):
            port_num = row * ports_per_row + i + 1
            if port_num <= max_port:
                port_labels += f"{port_num:3d}|"
            else:
                port_labels += '   |'
        print(port_labels)

        # Display port status
        print(generate_separator(ports_per_row))
        port_status = '|'
        for i in range(ports_per_row):
            port_num = row * ports_per_row + i + 1
            if any(f"gigabitEthernet 1/0/{port_num}" in port['description'] for port in interfaces.values()):
                port_status += ' X |'
            elif port_num <= max_port:
                port_status += '   |'
            else:
                port_status += '   |'
        print(port_status)

    print(generate_separator(ports_per_row))


    # Display Up interfaces with their information
    if interfaces:
        print("\nUp interfaces with their traffic information:")
        for idx in sorted(interfaces):
            data = interfaces[idx]
            descr = data['description']
            port_num = int(descr.split('/')[-1]) if 'gigabitEthernet' in descr else idx
            in_octets = data['in_octets']
            out_octets = data['out_octets']
            
            def format_octets(octets):
                for unit in ['', 'K', 'M', 'G', 'T']:
                    if octets < 1024.0:
                        return f"{octets:.2f} {unit}B"
                    octets /= 1024.0
                return f"{octets:.2f} PB"
            
            in_octets_readable = format_octets(in_octets)
            out_octets_readable = format_octets(out_octets)
            
            print(f"Port {port_num}: Incoming traffic = {in_octets_readable}, Outgoing traffic = {out_octets_readable}")
    else:
        print("No ports detected in 'Up' state.")
        severity_level = max(severity_level, 1)
        
    sys.exit(severity_level)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 script.py <DEVICE_IP_ADDRESS> [COMMUNITY_STRING]")
        sys.exit(1)

    device_ip = sys.argv[1]
    community_string = sys.argv[2] if len(sys.argv) == 3 else 'public'

    check_device_status(device_ip, community_string)
