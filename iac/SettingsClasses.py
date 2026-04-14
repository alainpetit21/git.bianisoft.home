from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pulumi


@dataclass(frozen=True)
class ProxmoxSettings:
    endpoint: str
    insecure: bool
    api_token_id: str
    api_token_secret: pulumi.Output[str]
    ssh_username: str | None
    ssh_password: pulumi.Output[str] | None


@dataclass(frozen=True)
class VmSettings:
    node_name: str
    storage_name: str
    network_bridge: str
    vm_name: str
    vm_id: int
    cpu_cores: int
    memory_mb: int
    disk_gb: int
    ipv4_address: str
    ip_cidr: int
    gateway: str
    dns_servers: Sequence[str]
    fqdn: str
    ansible_user: str
    ssh_public_key: str
    image_datastore_name: str
    image_content_type: str
    image_file_name: str
    image_url: str
    image_verify_tls: bool


@dataclass(frozen=True)
class AnsibleSettings:
    private_key_path: str
    python_interpreter: str
    playbook_path: str


@dataclass(frozen=True)
class GitLabSettings:
    external_url: str
    edition: str
    tls_mode: str


@dataclass(frozen=True)
class AppSettings:
    proxmox: ProxmoxSettings
    vm: VmSettings
    ansible: AnsibleSettings
    gitlab: GitLabSettings
