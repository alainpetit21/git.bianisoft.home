#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="${1:-dev}"

if ! command -v pulumi >/dev/null 2>&1; then
  echo "pulumi CLI not found in PATH." >&2
  exit 1
fi

pulumi stack select "${STACK_NAME}" >/dev/null 2>&1 || pulumi stack init "${STACK_NAME}"

pulumi config set proxmox:endpoint "https://192.168.0.10:8006/api2/json"
pulumi config set proxmox:insecure true
pulumi config set proxmox:apiTokenId "pulumi@pve!iac"
pulumi config set proxmox:sshUsername "root"

if [[ -n "${PROXMOX_API_TOKEN_SECRET:-}" ]]; then
  pulumi config set --secret proxmox:apiTokenSecret "${PROXMOX_API_TOKEN_SECRET}"
else
  echo "Skipping proxmox:apiTokenSecret (set PROXMOX_API_TOKEN_SECRET to configure it)."
fi

if [[ -n "${PROXMOX_SSH_PASSWORD:-}" ]]; then
  pulumi config set --secret proxmox:sshPassword "${PROXMOX_SSH_PASSWORD}"
else
  echo "Skipping proxmox:sshPassword (set PROXMOX_SSH_PASSWORD to configure it)."
fi

pulumi config set vm:nodeName "pve"
pulumi config set vm:storageName "local-lvm"
pulumi config set vm:networkBridge "vmbr0"
pulumi config set vm:name "gitlab-ce"
pulumi config set vm:vmId 611
pulumi config set vm:cpuCores 4
pulumi config set vm:memoryMb 8192
pulumi config set vm:diskGb 200
pulumi config set vm:imageDatastoreName "local"
pulumi config set vm:imageContentType "iso"
pulumi config set vm:imageFileName "debian-12-genericcloud-amd64.img"
pulumi config set vm:imageUrl "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2"
pulumi config set vm:imageVerifyTls true
pulumi config set vm:ipAddress "192.168.0.11"
pulumi config set vm:ipCidr 24
pulumi config set vm:gateway "192.168.0.1"
pulumi config set --path vm:dnsServers[0] "192.168.0.1"
pulumi config set vm:fqdn "git.bianisoft.home"
pulumi config set vm:ansibleUser "ansible"
pulumi config set vm:sshPublicKey "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBKNsZrURbyZyD+AY7l2cnkoXHO4CMbeHs5/EDlIw3pp proxmox"

pulumi config set ansible:privateKeyPath "~/.ssh/id_ed25519"
pulumi config set ansible:pythonInterpreter "/usr/bin/python3"
pulumi config set ansible:playbookPath "ansible/playbooks/gitlab-ce.yml"

pulumi config set gitlab:edition "ce"
pulumi config set gitlab:tlsMode "self-signed"
pulumi config set gitlab:externalUrl "https://git.bianisoft.home"

echo "Stack '${STACK_NAME}' initialized with baseline config."
echo "If needed, set PROXMOX_API_TOKEN_SECRET and rerun this script to store the secret securely."
