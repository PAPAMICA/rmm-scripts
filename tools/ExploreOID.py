#!/usr/bin/env python3

from pysnmp.hlapi import *
import sys

def snmp_walk(ip, community):
    """
    Effectue un SNMP WALK sur l'équipement spécifié et affiche tous les OIDs disponibles avec leurs valeurs.
    
    :param ip: Adresse IP de l'équipement SNMP
    :param community: Chaîne de communauté SNMP
    """
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),  # SNMP v2c
        UdpTransportTarget((ip, 161), timeout=1, retries=3),
        ContextData(),
        ObjectType(ObjectIdentity('1.3.6.1')),
        lexicographicMode=False
    )

    for errorIndication, errorStatus, errorIndex, varBinds in iterator:
        if errorIndication:
            print(f"Erreur SNMP : {errorIndication}")
            break
        elif errorStatus:
            print(f"Erreur SNMP : {errorStatus.prettyPrint()}")
            break
        else:
            for varBind in varBinds:
                oid, value = varBind
                print(f"{oid.prettyPrint()} = {value.prettyPrint()}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Utilisation : python3 snmp_scan_all.py <IP> <COMMUNAUTE>")
        print("Exemple : python3 snmp_scan_all.py 192.168.0.201 public")
        sys.exit(1)

    ip = sys.argv[1]
    community = sys.argv[2]

    snmp_walk(ip, community)
