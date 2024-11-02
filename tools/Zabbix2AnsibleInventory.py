import os

import requests
import yaml

# Zabbix API configuration
ZABBIX_API_URL = f"https://{os.getenv('ZABBIX_URL')}/api_jsonrpc.php"
ZABBIX_USER = os.getenv("ZABBIX_USER")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD")


def get_auth_token():
    """
    Authenticate to the Zabbix API and get an authentication token.

    Returns:
        str: The authentication token if successful, None otherwise
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
        "id": 1,
        "auth": None,
    }
    response = requests.post(ZABBIX_API_URL, json=payload, timeout=60)
    try:
        return response.json().get("result")
    except Exception:
        print("Error: Response is not valid JSON.")
        print("Raw response content:", response.text)
        return None


def get_hosts(auth_token):
    """
    Retrieve hosts from Zabbix API.

    Args:
        auth_token (str): The authentication token for Zabbix API

    Returns:
        list: List of hosts with their properties (host, name, tags, interfaces)
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host", "name", "tags", "interfaces"],
            "selectInterfaces": ["ip", "dns", "port", "type", "main", "useip"],
            "selectTags": "extend",
        },
        "auth": auth_token,
        "id": 2,
    }
    response = requests.post(ZABBIX_API_URL, json=payload, timeout=60)
    return response.json().get("result")


def generate_inventory_yaml(hosts):
    """
    Generate Ansible inventory file in YAML format from Zabbix hosts.

    Args:
        hosts (list): List of host dictionaries containing host information

    Creates a YAML file named 'inventory.yml' with the Ansible inventory structure
    """
    inventory = {}

    for host in hosts:
        host_name = host["host"]
        # Use IP if available, otherwise use DNS if configured, else use hostname
        if host["interfaces"] and host["interfaces"][0].get("ip"):
            ansible_host = host["interfaces"][0]["ip"]
        elif host["interfaces"] and host["interfaces"][0].get("dns"):
            ansible_host = host["interfaces"][0]["dns"]
        else:
            ansible_host = host_name

        ansible_host_info = {"ansible_host": ansible_host, "ansible_port": 22}

        # Find "ansible" tag to determine group
        groups = [
            tag["value"]
            for tag in host.get("tags", [])
            if tag["tag"].lower() == "ansible"
        ]

        # If groups exist, add them to inventory
        for group in groups:
            if group not in inventory:
                inventory[group] = {"hosts": {}}
            inventory[group]["hosts"][host_name] = ansible_host_info

    with open("inventory.yml", "w") as file:
        yaml.dump(inventory, file, default_flow_style=False)
    print("Ansible inventory in YAML generated successfully.")


# Main
if __name__ == "__main__":
    auth_token = get_auth_token()
    if auth_token:
        hosts = get_hosts(auth_token)
        if hosts:
            generate_inventory_yaml(hosts)
        else:
            print("No hosts found.")
    else:
        print("Authentication failed.")
