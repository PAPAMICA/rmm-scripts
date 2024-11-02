#!/usr/bin/env python3

import os
import sys

import requests

# Base configuration from environment variables
ZABBIX_API_URL = f"https://{os.getenv('ZABBIX_URL')}/api_jsonrpc.php"
ZABBIX_USER = os.getenv("ZABBIX_USER")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD")


# Authenticate to Zabbix API
def get_auth_token():
    """
    Get authentication token from Zabbix API
    Returns: Authentication token string
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
        "id": 1,
        "auth": None,
    }

    try:
        response = requests.post(ZABBIX_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["result"]
    except Exception as e:
        print(f"Authentication error: {e}")
        sys.exit(1)


# Get value of a specific item for a given host
def get_item_value(auth_token, host, item_key):
    """
    Get item value from a specific host
    Args:
        auth_token: Zabbix authentication token
        host: Hostname to query
        item_key: Item key to retrieve
    Returns: Item value
    """
    # Get host ID
    host_payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {"output": ["hostid"], "filter": {"host": [host]}},
        "auth": auth_token,
        "id": 2,
    }

    try:
        host_response = requests.post(ZABBIX_API_URL, json=host_payload, timeout=60)
        host_response.raise_for_status()
        host_data = host_response.json()

        if "result" not in host_data:
            print("Invalid response from Zabbix API: 'result' key missing")
            sys.exit(1)

        if not host_data["result"]:
            print(f"Host {host} not found.")
            sys.exit(2)
        host_id = host_data["result"][0]["hostid"]
    except Exception as e:
        print(f"Error retrieving host: {e}")
        sys.exit(1)

    # Get item value
    item_payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["lastvalue"],
            "hostids": host_id,
            "filter": {"key_": item_key},
        },
        "auth": auth_token,
        "id": 3,
    }

    try:
        item_response = requests.post(ZABBIX_API_URL, json=item_payload, timeout=60)
        item_response.raise_for_status()
        item_data = item_response.json()
        if not item_data["result"]:
            print(f"Item {item_key} not found for host {host}.")
            sys.exit(2)
        item_value = item_data["result"][0]["lastvalue"]
        return item_value
    except Exception as e:
        print(f"Error retrieving item: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: script.py <hostname> <item_key>")
        sys.exit(1)

    host = sys.argv[1]
    item_key = sys.argv[2]

    host = host.replace("'", "")

    token = get_auth_token()
    value = get_item_value(token, host, item_key)
    print(host)
    print(f"{item_key}: {value}")
    sys.exit(0)
