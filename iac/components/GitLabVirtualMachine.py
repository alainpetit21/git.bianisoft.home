from __future__ import annotations

import pulumi
import pulumi_proxmoxve as proxmoxve

from iac.SettingsClasses import VmSettings


class GitLabVirtualMachine(pulumi.ComponentResource):
    """Provision a GitLab VM on Proxmox using cloud-init."""

    def __init__(
        self,
        name: str,
        settings: VmSettings,
        cloud_image_file_id: pulumi.Input[str],
        provider: proxmoxve.Provider,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("bianisoft:proxmox:GitLabVirtualMachine", name, None, opts)

        network_cidr = f"{settings.ipv4_address}/{settings.ip_cidr}"
        fqdn_parts = settings.fqdn.split(".", 1)
        search_domain = fqdn_parts[1] if len(fqdn_parts) == 2 else settings.fqdn

        resource_opts = pulumi.ResourceOptions(parent=self, provider=provider)

        self.vm = proxmoxve.vm.VirtualMachine(
            f"{name}-vm",
            node_name=settings.node_name,
            vm_id=settings.vm_id,
            name=settings.vm_name,
            description="GitLab CE managed by Pulumi + Ansible",
            tags=["gitlab", "pulumi", "ansible"],
            on_boot=True,
            started=True,
            bios="seabios",
            scsi_hardware="virtio-scsi-single",
            cpu={
                "cores": settings.cpu_cores,
                "sockets": 1,
                "type": "x86-64-v2-AES",
            },
            memory={
                "dedicated": settings.memory_mb,
            },
            disks=[
                {
                    "interface": "scsi0",
                    "datastore_id": settings.storage_name,
                    "file_id": cloud_image_file_id,
                    "size": settings.disk_gb,
                    "file_format": "raw",
                    "discard": "on",
                    "ssd": True,
                }
            ],
            network_devices=[
                {
                    "bridge": settings.network_bridge,
                    "model": "virtio",
                    "enabled": True,
                }
            ],
            operating_system={"type": "l26"},
            agent={
                "enabled": True,
                "trim": True,
                "type": "virtio",
                "wait_for_ip": {"ipv4": True, "ipv6": False},
            },
            initialization={
                "type": "nocloud",
                "interface": "ide2",
                "datastore_id": settings.storage_name,
                "dns": {
                    "domain": search_domain,
                    "servers": list(settings.dns_servers),
                },
                "ip_configs": [
                    {
                        "ipv4": {
                            "address": network_cidr,
                            "gateway": settings.gateway,
                        }
                    }
                ],
                "user_account": {
                    "username": settings.ansible_user,
                    "keys": [settings.ssh_public_key],
                },
            },
            opts=resource_opts,
        )

        self.vm_id = self.vm.vm_id
        self.node_name = self.vm.node_name
        self.ipv4_address = pulumi.Output.from_input(settings.ipv4_address)
        self.fqdn = pulumi.Output.from_input(settings.fqdn)

        self.register_outputs(
            {
                "vmId": self.vm_id,
                "nodeName": self.node_name,
                "ipv4Address": self.ipv4_address,
                "fqdn": self.fqdn,
            }
        )
