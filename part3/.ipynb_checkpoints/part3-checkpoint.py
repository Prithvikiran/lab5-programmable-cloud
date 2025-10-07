#!/usr/bin/env python3
"""
Part 3 – Nested VM Creation using Google Cloud API

This script demonstrates automated orchestration of Compute Engine instances
using a Service Account. It creates a VM (VM1) that, upon startup, launches
another VM (VM2) running a Flask web application. The workflow illustrates
how service accounts can securely automate resource provisioning.

"""

import os
import time
from google.oauth2 import service_account
from googleapiclient import discovery


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

PROJECT_ID = "graphic-adviser-471303-p3"
ZONE = "us-west1-b"
SERVICE_ACCOUNT_EMAIL = "flask-builder@graphic-adviser-471303-p3.iam.gserviceaccount.com"
CREDENTIALS_FILE = "service-credentials.json"

# Authenticate using the service account credentials
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
compute = discovery.build("compute", "v1", credentials=credentials)


# -------------------------------------------------------------------
# Helper Function
# -------------------------------------------------------------------

def wait_for_operation(compute, project: str, zone: str, operation: dict) -> None:
    """Waits for an asynchronous Google Cloud operation to complete."""
    print("Waiting for operation to complete...")
    while True:
        result = compute.zoneOperations().get(
            project=project, zone=zone, operation=operation["name"]
        ).execute()
        if result.get("status") == "DONE":
            print("Operation completed successfully.\n")
            if "error" in result:
                raise RuntimeError(f"Operation failed: {result['error']}")
            return
        time.sleep(3)


# -------------------------------------------------------------------
# VM1 Startup Script
# -------------------------------------------------------------------

VM1_STARTUP_SCRIPT = """#!/bin/bash
set -euxo pipefail

echo "[VM1] Initializing environment..."
mkdir -p /srv && cd /srv

echo "[VM1] Retrieving metadata files..."
curl -H "Metadata-Flavor: Google" http://metadata/computeMetadata/v1/instance/attributes/vm2-startup-script > vm2-startup-script.sh
curl -H "Metadata-Flavor: Google" http://metadata/computeMetadata/v1/instance/attributes/vm1-launch-vm2-code > vm1-launch-vm2-code.py
curl -H "Metadata-Flavor: Google" http://metadata/computeMetadata/v1/instance/attributes/service-credentials > service-credentials.json

echo "[VM1] Installing dependencies..."
apt-get update -y
apt-get install -y python3-pip
pip3 install --upgrade google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib

echo "[VM1] Launching nested VM (VM2)..."
python3 vm1-launch-vm2-code.py
"""


# -------------------------------------------------------------------
# Main Execution
# -------------------------------------------------------------------

def main():
    """Creates VM1, which programmatically launches another VM (VM2)."""

    # Read files to embed as metadata
    with open("vm1-launch-vm2-code.py", "r") as f:
        vm1_launcher_code = f.read()
    with open("vm2-startup-script.sh", "r") as f:
        vm2_startup_script = f.read()
    with open(CREDENTIALS_FILE, "r") as f:
        service_credentials = f.read()

    vm1_name = "vm1-launcher"
    machine_type = f"zones/{ZONE}/machineTypes/e2-micro"

    # Define VM1 configuration
    config = {
        "name": vm1_name,
        "machineType": machine_type,
        "disks": [{
            "boot": True,
            "autoDelete": True,
            "initializeParams": {
                "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
            }
        }],
        "networkInterfaces": [{
            "network": "global/networks/default",
            "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}]
        }],
        "metadata": {
            "items": [
                {"key": "startup-script", "value": VM1_STARTUP_SCRIPT},
                {"key": "vm2-startup-script", "value": vm2_startup_script},
                {"key": "vm1-launch-vm2-code", "value": vm1_launcher_code},
                {"key": "service-credentials", "value": service_credentials},
            ]
        },
        "serviceAccounts": [{
            "email": SERVICE_ACCOUNT_EMAIL,
            "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
        }]
    }

    print(f"Creating VM1: {vm1_name}")
    operation = compute.instances().insert(project=PROJECT_ID, zone=ZONE, body=config).execute()
    wait_for_operation(compute, PROJECT_ID, ZONE, operation)
    print(f"VM1 '{vm1_name}' created successfully.")
    print("VM1 will automatically execute 'vm1-launch-vm2-code.py' to create VM2.\n")


# -------------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------------

if __name__ == "__main__":
    try:
        main()
        print("Execution completed. Use 'gcloud compute instances list' to verify VM creation.")
    except Exception as e:
        print(f"Error during execution: {e}")
