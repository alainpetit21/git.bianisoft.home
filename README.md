# GitLab on Proxmox with Pulumi + Ansible

This project provisions a Debian 12 VM on Proxmox VE and configures GitLab CE with Ansible.

## What this stack does

- Creates a Proxmox VM on node `pve` using storage `local-lvm` and bridge `vmbr0`
- Applies your requested sizing: `4 vCPU`, `8 GB RAM`, `200 GB disk`
- Configures static networking (`192.168.0.11/24`, gateway `192.168.0.1`, DNS `192.168.0.1`)
- Creates cloud-init user `ansible` with your SSH public key
- Installs and configures GitLab CE on `https://git.bianisoft.home`
- Uses self-signed TLS certificates generated on the VM

## Project layout

- `main.py`: Pulumi entrypoint
- `iac/SettingsClasses.py`: typed settings dataclasses
- `iac/StackConfigLoader.py`: stack config loader
- `iac/ProxmoxProviderFactory.py`: Proxmox provider factory
- `iac/components/ProxmoxCloudImageDownloader.py`: cloud image detection/download component
- `iac/components/GitLabVirtualMachine.py`: VM component resource
- `iac/components/GitLabAnsibleProvisioner.py`: Ansible execution component
- `iac/GitLabInfrastructureStack.py`: stack orchestration
- `ansible/playbooks/gitlab-ce.yml`: GitLab install/config playbook
- `scripts/bootstrap_stack.sh`: baseline stack config bootstrap

## Prerequisites

- Proxmox VE reachable at `https://192.168.0.10:8006`
- Pulumi CLI installed
- Python 3.10+
- Ansible installed on the machine running Pulumi
- SSH private key matching the configured public key

## Secure config approach

- Secret values are stored in Pulumi stack config (`Pulumi.<stack>.yaml`) and marked secret.
- `Pulumi.*.yaml` is ignored by Git in `.gitignore`.
- This keeps token secrets out of Git history.

## Image bootstrap behavior

- No pre-created template VM is required.
- During `pulumi up`, the stack checks whether the Debian cloud image already exists in Proxmox datastore `local`.
- If the image is missing, Pulumi downloads it automatically.
- The GitLab VM is then created from that cloud image and resized to the configured disk size.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "import pulumi_proxmoxve as p; print(hasattr(p.vm, 'VirtualMachine'))"  # expected: True

# Initialize stack and non-secret defaults
./scripts/bootstrap_stack.sh dev

# Set secret token without committing it
read -s PROXMOX_API_TOKEN_SECRET
export PROXMOX_API_TOKEN_SECRET
./scripts/bootstrap_stack.sh dev
unset PROXMOX_API_TOKEN_SECRET

pulumi up
```

Point your IDE Python interpreter to `.venv/bin/python` so code completion and type checks use the same dependency set.

## Required secret

Set this key if not using the bootstrap script:

```bash
pulumi config set --secret proxmox:apiTokenSecret '<token-secret>'
```

When using image download/import flow (no prebuilt template), set Proxmox node SSH password as secret too:

```bash
pulumi config set proxmox:sshUsername root
pulumi config set --secret proxmox:sshPassword '<root-ssh-password>'
```

## Important notes

- `proxmox:apiTokenId` is expected in the form `user@realm!tokenid`
- Provider auth uses `apiToken = <apiTokenId>=<apiTokenSecret>`
- VM disk import requires Proxmox node SSH auth. This stack supports secret config keys `proxmox:sshUsername` and `proxmox:sshPassword`.
- `pulumi-proxmoxve` is pinned to `7.13.0` because this codebase uses `proxmoxve.vm.VirtualMachine` (v7 API surface).
- Default cloud image config:
  - `vm:imageDatastoreName=local`
  - `vm:imageContentType=iso`
  - `vm:imageFileName=debian-12-genericcloud-amd64.img`
  - `vm:imageUrl=https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2`
- If your private key path is not `~/.ssh/id_ed25519`, set `ansible:privateKeyPath`
- This playbook assumes user `ansible` can escalate with `sudo` (`become: true`)

## Useful commands

```bash
pulumi preview
pulumi up
pulumi stack output
pulumi destroy
```
