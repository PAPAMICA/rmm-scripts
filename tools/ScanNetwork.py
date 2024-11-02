#!/usr/bin/env python3

import ipaddress
import re
import socket
import subprocess
import sys
import threading
import time
from queue import Queue

import netifaces
import requests


def get_mac_vendor(mac_address):
    """
    Récupère le nom du fabricant à partir de l'adresse MAC en utilisant l'API MAC Vendors.
    """
    url = f"https://api.macvendors.com/{mac_address}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Inconnu"
    except requests.RequestException:
        return "Inconnu"


def ping_ip(ip):
    """
    Pinge une adresse IP pour vérifier si elle est active.
    """
    if sys.platform == "win32":
        command = ["ping", "-n", "1", "-w", "1000", ip]
    else:
        command = ["ping", "-c", "1", "-W", "1", ip]
    return (
        subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        == 0
    )


def get_mac(ip):
    """
    Récupère l'adresse MAC associée à une adresse IP en utilisant la table ARP.
    """
    if sys.platform == "win32":
        command = ["arp", "-a", ip]
        pattern = r"([0-9a-f]{2}-){5}[0-9a-f]{2}"
    else:
        command = ["arp", "-n", ip]
        pattern = r"(([0-9a-f]{1,2}:){5}[0-9a-f]{1,2})"
    try:
        result = subprocess.check_output(command, stderr=subprocess.DEVNULL).decode()
        mac = re.search(pattern, result.lower())
        if mac:
            return mac.group().replace("-", ":").lower()
        else:
            return None
    except subprocess.CalledProcessError:
        return None


def worker():
    while True:
        ip = q.get()
        start_time = time.time()
        if ping_ip(ip):
            hostname = ""
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                hostname = "Inconnu"
            mac = get_mac(ip)
            if mac:
                vendor = get_mac_vendor(mac)
            else:
                mac = "Inconnu"
                vendor = "Inconnu"
            devices.append(
                {"IP": ip, "Hostname": hostname, "MAC": mac, "Fabricant": vendor}
            )
        elapsed_time = time.time() - start_time
        if elapsed_time < 10:
            time.sleep(10 - elapsed_time)
        q.task_done()


def get_local_cidr():
    """
    Récupère le CIDR de l'interface réseau principale de la machine locale.
    """
    gateways = netifaces.gateways()
    default_gateway = gateways["default"][netifaces.AF_INET][1]
    addrs = netifaces.ifaddresses(default_gateway)
    ip_info = addrs[netifaces.AF_INET][0]
    ip_address = ip_info["addr"]
    netmask = ip_info["netmask"]

    network = ipaddress.IPv4Network(f"{ip_address}/{netmask}", strict=False)
    return str(network)


if __name__ == "__main__":
    if len(sys.argv) > 2:
        print("Usage: python3 scan_network.py [CIDR]")
        print("Exemple: python3 scan_network.py 192.168.1.0/24")
        sys.exit(1)

    if len(sys.argv) == 2:
        cidr = sys.argv[1]
    else:
        cidr = get_local_cidr()
        print(f"Aucun CIDR fourni. Utilisation du CIDR local : {cidr}")

    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
    except ValueError:
        print("CIDR invalide.")
        sys.exit(1)

    q = Queue()
    devices = []

    # Démarrer les threads
    for _ in range(100):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    # Ajouter les IP à la file d'attente
    for ip in network.hosts():
        q.put(str(ip))

    q.join()

    # Afficher le tableau des appareils détectés
    if devices:
        print(f"\nAppareils détectés ({len(devices)} au total):\n")
        print(
            "{:<16} {:<30} {:<18} {:<}".format(
                "Adresse IP", "Nom d'hôte", "Adresse MAC", "Fabricant"
            )
        )
        print("-" * 80)
        for device in devices:
            print(
                "{:<16} {:<30} {:<18} {:<}".format(
                    device["IP"], device["Hostname"], device["MAC"], device["Fabricant"]
                )
            )
    else:
        print("Aucun appareil détecté.")

    print(f"\nNombre total d'équipements détectés: {len(devices)}")
