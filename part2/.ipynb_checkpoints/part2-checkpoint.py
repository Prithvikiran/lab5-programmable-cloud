#!/usr/bin/env python3

#!/usr/bin/env python3
"""
Part 2 – Snapshot and Clone VMs
Creates a snapshot of the Part 1 instance's boot disk, launches three
instances from that snapshot, measures creation time, and writes TIMING.md.
"""

import time
from datetime import datetime

import googleapiclient.discovery
import google.auth
from googleapiclient.errors import HttpError

# ---- config ----
zone = "us-west1-b"
base_instance = "flask-tutorial-vm"              # from Part 1
snapshot_name = f"base-snapshot-{base_instance}"
machine_type = lambda z: f"zones/{z}/machineTypes/f1-micro"

# ---- clients ----
credentials, project = google.auth.default()
compute = googleapiclient.discovery.build("compute", "v1", credentials=credentials)


def wait_for_zone_op(operation_name: str) -> None:
    """Poll a zonal operation until it completes."""
    while True:
        op = compute.zoneOperations().get(
            project=project, zone=zone, operation=operation_name
        ).execute()
        if op.get("status") == "DONE":
            if "error" in op:
                raise RuntimeError(op["error"])
            return
        time.sleep(2)


def get_boot_disk_name(instance_name: str) -> str:
    """Return the boot disk name for an instance."""
    inst = compute.instances().get(
        project=project, zone=zone, instance=instance_name
    ).execute()
    # first attached disk is the boot disk
    src_url = inst["disks"][0]["source"]
    return src_url.split("/")[-1]


def create_snapshot_from_instance(inst_name: str, snap_name: str) -> None:
    """Create a snapshot of the instance's boot disk (idempotent)."""
    try:
        # quick existence check
        compute.snapshots().get(project=project, snapshot=snap_name).execute()
        print(f"Snapshot '{snap_name}' already exists. Skipping create.")
        return
    except HttpError as e:
        if e.resp.status != 404:
            raise

    disk_name = get_boot_disk_name(inst_name)
    print(f"Creating snapshot '{snap_name}' from disk '{disk_name}'...")
    body = {"name": snap_name, "description": f"Snapshot of {inst_name} boot disk"}
    op = compute.disks().createSnapshot(
        project=project, zone=zone, disk=disk_name, body=body
    ).execute()
    wait_for_zone_op(op["name"])
    print(f"Snapshot '{snap_name}' created.\n")


def create_instance_from_snapshot(new_name: str, snap_name: str) -> float:
    """
    Create an instance from the snapshot and return elapsed seconds.
    If the name already exists, a short suffix is appended.
    """
    start = time.time()
    source_snapshot = f"projects/{project}/global/snapshots/{snap_name}"
    cfg = {
        "name": new_name,
        "machineType": machine_type(zone),
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {"sourceSnapshot": source_snapshot},
            }
        ],
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
            }
        ],
        "serviceAccounts": [
            {
                "email": "default",
                "scopes": ["https://www.googleapis.com/auth/cloud-platform"],
            }
        ],
    }

    try:
        op = compute.instances().insert(
            project=project, zone=zone, body=cfg
        ).execute()
    except HttpError as e:
        if e.resp.status == 409:  # name conflict
            suffix = str(int(time.time()) % 10000)
            cfg["name"] = f"{new_name}-{suffix}"
            print(
                f"Instance '{new_name}' already exists, retrying as '{cfg['name']}'..."
            )
            op = compute.instances().insert(
                project=project, zone=zone, body=cfg
            ).execute()
        else:
            raise

    wait_for_zone_op(op["name"])
    elapsed = round(time.time() - start, 2)
    print(f"Instance '{cfg['name']}' created in {elapsed} seconds.")
    return elapsed


def main():
    print("\nPart 2: Snapshot and clone\n")
    # 1) snapshot
    create_snapshot_from_instance(base_instance, snapshot_name)

    # 2) clones + timings
    names = ["clone-instance-1", "clone-instance-2", "clone-instance-3"]
    timings = [(n, create_instance_from_snapshot(n, snapshot_name)) for n in names]

    # 3) write TIMING.md
    with open("TIMING.md", "w") as f:
        f.write("# Instance Creation Timing Results\n")
        f.write(f"Generated on {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        for n, t in timings:
            f.write(f"- {n}: {t} seconds\n")

    print("\nTiming results saved to TIMING.md\n")


if __name__ == "__main__":
    main()
