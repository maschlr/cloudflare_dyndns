import os
from pathlib import Path
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Cloudflare API details
API_KEY = os.getenv("API_KEY")
API_EMAIL = os.getenv("API_EMAIL")
ZONE_ID = os.getenv("ZONE_ID")
DNS_RECORD_ID = os.getenv("DNS_RECORD_ID")

TESTING = os.getenv("TESTING") == "1"

def get_current_ip():
    try:
        # Use a public IP service to get the current public IP address
        response = requests.get("https://api.ipify.org?format=json")
        data = response.json()
        return data["ip"]
    except Exception as e:
        logging.error("Error fetching current IP: %s", e)
        return None

def get_dns_record_ip():
    try:
        headers = {
            "X-Auth-Email": API_EMAIL,
            "X-Auth-Key": API_KEY,
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{DNS_RECORD_ID}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data["result"]["content"]
        else:
            logging.error("Error fetching DNS record IP: %s %s", response.status_code, response.text)
            return None
    except Exception as e:
        logging.error("Error fetching DNS record IP: %s", e)
        return None

def update_dns_record(ip):
    try:
        headers = {
            "X-Auth-Email": API_EMAIL,
            "X-Auth-Key": API_KEY,
            "Content-Type": "application/json"
        }
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{DNS_RECORD_ID}"
        payload = {
            "type": "A",
            "name": "tribalgathering.com",  # Replace with your DNS record name
            "content": ip,
            "ttl": 1,  # TTL in seconds (1 means automatic)
            "proxied": True  # Whether the traffic should be proxied through Cloudflare
        }

        if TESTING:
            logging.info("Testing mode enabled. Not updating DNS record. Payload: %s", payload)
            return
        response = requests.put(url, headers=headers, json=payload)
        if response.status_code == 200:
            logging.info("DNS record updated successfully.")
        else:
            logging.error("Error updating DNS record: %s %s", response.status_code, response.text)
    except Exception as e:
        logging.error("Error updating DNS record: %s", e)

if __name__ == "__main__":
    script_dir = Path(__file__).parent.absolute()
    logging.basicConfig(filename=script_dir / 'ip_update.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    current_ip = get_dns_record_ip()
    new_ip = get_current_ip()
    
    if new_ip is not None:
        if current_ip is None:
            logging.info("Initial DNS record IP: %s", new_ip)
        elif new_ip != current_ip:
            logging.info("Public IP has changed. Updating DNS record...")
            update_dns_record(new_ip)
        else:
            logging.info("Public IP has not changed.")
    else:
        logging.info("Public IP retrieval failed.")
