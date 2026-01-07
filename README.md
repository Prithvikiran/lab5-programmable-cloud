# Programmable Cloud Lab – Automated GCP VM Provisioning

This project demonstrates **programmatic control** of Google Cloud Platform (GCP) infrastructure using Python, focusing on creating, configuring, and chaining virtual machines (VMs) via APIs.

## Overview

The lab is structured into three parts, each building a deeper level of automation on top of Google Compute Engine. It showcases how to treat cloud infrastructure as code, from initial VM provisioning to image-based scaling and service-account–driven automation.

## Part 1 – Automated VM Provisioning

- Programmatically creates a Compute Engine VM instance using the GCP Python client and REST APIs
- Clones an application from a Git repository onto the VM and installs required software
- Configures firewall rules so the deployed application is reachable via a public HTTP endpoint
- Outputs the external URL for users to access the web application

## Part 2 – Images, Snapshots, and Scaling

- Takes a snapshot of the configured VM and converts it into a reusable custom image
- Launches multiple VM instances from that image and measures the creation/boot times for each instance
- Demonstrates faster, consistent scaling by using images instead of configuring each VM from scratch

## Part 3 – Service Accounts and Chained VM Creation

- Creates and configures a dedicated GCP service account with least-privilege access
- Uses that service account's credentials from within a VM to authenticate against GCP APIs
- Implements "VM that creates VMs": one instance programmatically provisions another instance using the same automation logic as Part 1

## Key Concepts

- Infrastructure as Code for GCP Compute Engine
- Python-based interaction with GCP REST APIs and client libraries
- Service accounts, identity, and access control for applications running on VMs
- Image-based scaling and automation patterns for datacenter-style workloads

## Tech Stack

- **Language:** Python (primary), Shell scripts for setup
- **Platform:** Google Cloud Platform – Compute Engine, Images, Snapshots, Firewall, IAM Service Accounts
- **Tooling:** GCP SDK, GCP Python client libraries, Git

## Getting Started

Each part contains a dedicated `README.md` with detailed instructions and requirements. It's recommended to:

1. Review the GCP [Python guide](https://cloud.google.com/compute/docs/tutorials/python-guide) to familiarize yourself with the API structure
2. Perform each task manually in the Google Cloud Console first
3. Then implement the Python automation for the same operations
4. Use SSH keys or Personal Access Tokens for Git authentication in GCP VMs

## Directory Structure

```
├── part1/          # VM creation and application deployment
├── part2/          # Image creation and multi-instance scaling
├── part3/          # Service accounts and VM-to-VM automation
└── README.md       # This file
```
