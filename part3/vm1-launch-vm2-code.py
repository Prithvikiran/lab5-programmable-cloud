#!/usr/bin/env python3
import time
from google.oauth2 import service_account
import googleapiclient.discovery

print(" VM1 is setting up VM2...")

creds = service_account.Credentials.from_service_account_file('service-credentials.json')
project = 'graphic-adviser-471303-p3'
zone = 'us-west1-b'
compute = googleapiclient.discovery.build('compute', 'v1', credentials=creds)

vm2_name = "nested-flask-vm"
machine_type = f"zones/{zone}/machineTypes/e2-micro"
startup_script = open("vm2-startup-script.sh").read()

config = {
    "name": vm2_name,
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
    "metadata": {"items": [{"key": "startup-script", "value": startup_script}]},
}

op = compute.instances().insert(project=project, zone=zone, body=config).execute()
print(" Creating VM2...")

while True:
    res = compute.zoneOperations().get(project=project, zone=zone, operation=op["name"]).execute()
    if res["status"] == "DONE":
        print(" VM2 created successfully!")
        break
    time.sleep(3)
