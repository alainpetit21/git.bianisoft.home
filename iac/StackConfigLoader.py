import pulumi

from iac.SettingsClasses import *


class StackConfigLoader:
    """Loads and validates Pulumi stack configuration into typed settings."""

    @staticmethod
    def load() -> AppSettings:
        proxmox_cfg = pulumi.Config("proxmox")
        vm_cfg = pulumi.Config("vm")
        ansible_cfg = pulumi.Config("ansible")
        gitlab_cfg = pulumi.Config("gitlab")

        api_token_secret = proxmox_cfg.get_secret("apiTokenSecret")
        if api_token_secret is None:
            raise pulumi.RunError(
                "Missing required secret config: proxmox:apiTokenSecret. "
                "Set it with: pulumi config set --secret proxmox:apiTokenSecret '<token-secret>'"
            )

        dns_servers = vm_cfg.get_object("dnsServers")
        if not dns_servers:
            dns_servers_csv = vm_cfg.get("dnsServersCsv") or "192.168.0.1"
            dns_servers = [entry.strip() for entry in dns_servers_csv.split(",") if entry.strip()]

        vm_fqdn = vm_cfg.get("fqdn") or "git.bianisoft.home"
        external_url = gitlab_cfg.get("externalUrl") or f"https://{vm_fqdn}"

        proxmox = ProxmoxSettings(
            endpoint=proxmox_cfg.get("endpoint") or "https://192.168.0.10:8006/api2/json",
            insecure=proxmox_cfg.get_bool("insecure") if proxmox_cfg.get_bool("insecure") is not None else True,
            api_token_id=proxmox_cfg.get("apiTokenId") or "pulumi@pve!iac",
            api_token_secret=api_token_secret,
            ssh_username=proxmox_cfg.get("sshUsername"),
            ssh_password=proxmox_cfg.get_secret("sshPassword"),
        )

        vm = VmSettings(
            node_name=vm_cfg.get("nodeName") or "pve",
            storage_name=vm_cfg.get("storageName") or "local-lvm",
            network_bridge=vm_cfg.get("networkBridge") or "vmbr0",
            vm_name=vm_cfg.get("name") or "gitlab-ce",
            vm_id=vm_cfg.get_int("vmId") or 611,
            cpu_cores=vm_cfg.get_int("cpuCores") or 4,
            memory_mb=vm_cfg.get_int("memoryMb") or 8192,
            disk_gb=vm_cfg.get_int("diskGb") or 200,
            ipv4_address=vm_cfg.get("ipAddress") or "192.168.0.11",
            ip_cidr=vm_cfg.get_int("ipCidr") or 24,
            gateway=vm_cfg.get("gateway") or "192.168.0.1",
            dns_servers=dns_servers,
            fqdn=vm_fqdn,
            ansible_user=vm_cfg.get("ansibleUser") or "ansible",
            ssh_public_key=vm_cfg.require("sshPublicKey"),
            image_datastore_name=vm_cfg.get("imageDatastoreName") or "local",
            image_content_type=vm_cfg.get("imageContentType") or "iso",
            image_file_name=vm_cfg.get("imageFileName") or "debian-12-genericcloud-amd64.img",
            image_url=vm_cfg.get("imageUrl")
            or "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2",
            image_verify_tls=vm_cfg.get_bool("imageVerifyTls") if vm_cfg.get_bool("imageVerifyTls") is not None else True,
        )

        ansible = AnsibleSettings(
            private_key_path=ansible_cfg.get("privateKeyPath") or "~/.ssh/id_ed25519",
            python_interpreter=ansible_cfg.get("pythonInterpreter") or "/usr/bin/python3",
            playbook_path=ansible_cfg.get("playbookPath") or "ansible/playbooks/gitlab-ce.yml",
        )

        gitlab = GitLabSettings(
            external_url=external_url,
            edition=gitlab_cfg.get("edition") or "ce",
            tls_mode=gitlab_cfg.get("tlsMode") or "self-signed",
        )

        return AppSettings(
            proxmox=proxmox,
            vm=vm,
            ansible=ansible,
            gitlab=gitlab,
        )
