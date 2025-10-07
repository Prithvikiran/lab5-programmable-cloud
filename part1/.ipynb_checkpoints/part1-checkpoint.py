#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Part 1 - VM Creation and Application Deployment
------------------------------------------------
This script creates a Google Cloud VM instance, configures firewall
rules for port 5000, attaches a startup script that installs and runs
the Flask tutorial application, and outputs the public URL to access it.
"""

import time
import googleapiclient.discovery
import google.auth
from googleapiclient.errors import HttpError

# Authenticate and build the Compute Engine API client
credentials, project = google.auth.default()
compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

# Configuration constants
ZONE = 'us-west1-b'
INSTANCE_NAME = 'flask-tutorial-vm'
FIREWALL_NAME = 'allow-5000'
TAG = 'allow-5000'
PORT = 5000

# Read startup script from file
with open('startup-script.sh', 'r') as f:
    STARTUP_SCRIPT = f.read()


def wait_for_zone_op(op_name):
    """Wait until a zone operation finishes."""
    while True:
        result = compute.zoneOperations().get(
            project=project, zone=ZONE, operation=op_name
        ).execute()
        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            return
        time.sleep(2)


def ensure_firewall():
    """Ensure that the firewall rule for port 5000 exists."""
    try:
        compute.firewalls().get(project=project, firewall=FIREWALL_NAME).execute()
        print(f"Firewall rule '{FIREWALL_NAME}' already exists.")
    except HttpError as e:
        if e.resp.status == 404:
            print(f"Creating firewall rule '{FIREWALL_NAME}' to allow TCP port {PORT}...")
            body = {
                "name": FIREWALL_NAME,
                "network": "global/networks/default",
                "direction": "INGRESS",
                "sourceRanges": ["0.0.0.0/0"],
                "allowed": [{"IPProtocol": "tcp", "ports": [str(PORT)]}],
                "targetTags": [TAG],
            }
            compute.firewalls().insert(project=project, body=body).execute()
            print(f"Firewall rule '{FIREWALL_NAME}' created successfully.")
        else:
            raise


def create_instance():
    """Create a VM instance and attach the startup script."""
    print(f"Creating virtual machine instance '{INSTANCE_NAME}' in zone '{ZONE}'...")
    image = compute.images().getFromFamily(
        project='ubuntu-os-cloud', family='ubuntu-2204-lts'
    ).execute()

    config = {
        "name": INSTANCE_NAME,
        "machineType": f"zones/{ZONE}/machineTypes/f1-micro",
        "disks": [{
            "boot": True,
            "autoDelete": True,
            "initializeParams": {"sourceImage": image["selfLink"]}
        }],
        "networkInterfaces": [{
            "network": "global/networks/default",
            "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}]
        }],
        "metadata": {"items": [{"key": "startup-script", "value": STARTUP_SCRIPT}]},
        "tags": {"items": [TAG]},
        "serviceAccounts": [{
            "email": "default",
            "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
        }]
    }

    operation = compute.instances().insert(
        project=project, zone=ZONE, body=config
    ).execute()
    wait_for_zone_op(operation["name"])
    print(f"Instance '{INSTANCE_NAME}' created successfully.")

    return compute.instances().get(
        project=project, zone=ZONE, instance=INSTANCE_NAME
    ).execute()


def apply_tag():
    """Explicitly apply the network tag to ensure the firewall rule takes effect."""
    instance = compute.instances().get(
        project=project, zone=ZONE, instance=INSTANCE_NAME
    ).execute()
    fingerprint = instance['tags']['fingerprint']
    body = {"items": [TAG], "fingerprint": fingerprint}

    operation = compute.instances().setTags(
        project=project, zone=ZONE, instance=INSTANCE_NAME, body=body
    ).execute()
    wait_for_zone_op(operation['name'])
    print(f"Network tag '{TAG}' applied to instance '{INSTANCE_NAME}'.")


def main():
    print("\n=== Part 1: VM Creation and Configuration ===\n")
    ensure_firewall()
    instance = create_instance()
    apply_tag()

    ip_address = instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    print("\nDeployment completed successfully.")
    print(f"Flask application will be available at: http://{ip_address}:{PORT}")
    print("It may take 1–2 minutes for the application to initialize.")
    print("============================================================\n")


if __name__ == "__main__":
    main()
