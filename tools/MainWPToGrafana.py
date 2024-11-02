#!/usr/bin/env python3

import configparser
import logging
from datetime import datetime

import requests

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Read configuration from .ini file
config = configparser.ConfigParser()
config.read("MainWPToGrafana.ini")

# Configuration
MAINWP_API_URL = config["MainWP"]["API_URL"]
CONSUMER_KEY = config["MainWP"]["CONSUMER_KEY"]
CONSUMER_SECRET = config["MainWP"]["CONSUMER_SECRET"]
INFLUXDB_URL = config["InfluxDB"]["URL"]
INFLUXDB_DB = config["InfluxDB"]["DB"]


def get_mainwp_data():
    """
    Retrieves available update data from the MainWP API.

    This function sends a GET request to the MainWP API to obtain information
    about available updates for WordPress, plugins, themes and translations.

    Returns:
        dict: Update data if request is successful, None otherwise.
    """
    url = f"{MAINWP_API_URL}/updates/available-updates"
    params = {"consumer_key": CONSUMER_KEY, "consumer_secret": CONSUMER_SECRET}

    logger.info(f"Attempting to retrieve data from MainWP API: {url}")
    response = requests.get(url, params=params, timeout=60)

    if response.status_code == 200:
        logger.info("MainWP data retrieved successfully")
        return response.json()
    else:
        logger.error(f"Error retrieving MainWP data: {response.status_code}")
        return None


def insert_data_to_influxdb(
    total_wp_updates,
    total_plugin_updates,
    total_theme_updates,
    total_translation_updates,
):
    """
    Inserts update data into InfluxDB.

    This function takes the totals of different updates and sends them to InfluxDB
    for storage and later visualization in Grafana.

    Args:
        total_wp_updates (int): Total number of WordPress updates.
        total_plugin_updates (int): Total number of plugin updates.
        total_theme_updates (int): Total number of theme updates.
        total_translation_updates (int): Total number of translation updates.
    """
    # Format data for InfluxDB
    data = f"""
    mainwp_updates,host=mainwp_server wordpress_updates={total_wp_updates},plugin_updates={total_plugin_updates},theme_updates={total_theme_updates},translation_updates={total_translation_updates} {int(datetime.now().timestamp())}000000000
    """

    logger.info("Attempting to insert data into InfluxDB")
    # Send data to InfluxDB
    response = requests.post(
        f"{INFLUXDB_URL}/write?db={INFLUXDB_DB}", data=data, timeout=60
    )

    if response.status_code == 204:
        logger.info("Data successfully inserted into InfluxDB")
    else:
        logger.error(f"Error inserting into InfluxDB: {response.status_code}")
        logger.error(f"InfluxDB response: {response.text}")


def main():
    """
    Main script function.

    This function orchestrates the process of retrieving data from MainWP,
    calculating update totals, and inserting this data into InfluxDB.
    """
    logger.info("Starting MainWP to Grafana script")
    data = get_mainwp_data()

    if data:
        total_wp_updates = 0
        total_plugin_updates = 0
        total_theme_updates = 0
        total_translation_updates = 0

        logger.info("Processing MainWP data")
        for _, site_data in data.items():
            total_wp_updates += len(site_data.get("wp", []))
            total_plugin_updates += len(site_data.get("plugins", []))
            total_theme_updates += len(site_data.get("themes", []))
            total_translation_updates += len(site_data.get("translations", []))

        logger.info(
            f"Update summary - WordPress: {total_wp_updates}, Plugins: {total_plugin_updates}, Themes: {total_theme_updates}, Translations: {total_translation_updates}"
        )

        # Insert data into InfluxDB
        insert_data_to_influxdb(
            total_wp_updates,
            total_plugin_updates,
            total_theme_updates,
            total_translation_updates,
        )
    else:
        logger.warning("No data was retrieved from MainWP")

    logger.info("End of MainWP to Grafana script")


if __name__ == "__main__":
    main()
