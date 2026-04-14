from __future__ import annotations

import hashlib
import json
import os
import shlex

import pulumi
from pulumi_command import local

from iac.SettingsClasses import AnsibleSettings, GitLabSettings, VmSettings
from .GitLabVirtualMachine import GitLabVirtualMachine


class GitLabAnsibleProvisioner(pulumi.ComponentResource):
    """Run the Ansible playbook that installs/configures GitLab on the VM."""

    def __init__(
        self,
        name: str,
        vm_settings: VmSettings,
        ansible_settings: AnsibleSettings,
        gitlab_settings: GitLabSettings,
        vm_component: GitLabVirtualMachine,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("bianisoft:ansible:GitLabProvisioner", name, None, opts)

        create_cmd = self._build_ansible_command(
            vm_settings=vm_settings,
            ansible_settings=ansible_settings,
            gitlab_settings=gitlab_settings,
        )

        ansible_config_path = os.path.abspath("ansible/ansible.cfg")
        playbook_path = os.path.abspath(ansible_settings.playbook_path)

        environment = {
            "ANSIBLE_CONFIG": ansible_config_path,
            "ANSIBLE_HOST_KEY_CHECKING": "False",
        }

        self.run = local.Command(
            f"{name}-apply",
            create=create_cmd,
            update=create_cmd,
            delete="echo 'Skipping GitLab package removal; VM lifecycle is managed by Pulumi Proxmox resources.'",
            triggers=[
                vm_component.vm_id,
                vm_component.ipv4_address,
                gitlab_settings.external_url,
                self._file_sha256(playbook_path),
                self._file_sha256(ansible_config_path),
            ],
            environment=environment,
            opts=pulumi.ResourceOptions(parent=self, depends_on=[vm_component.vm]),
        )

        self.register_outputs(
            {
                "stdout": self.run.stdout,
                "stderr": self.run.stderr,
            }
        )

    @staticmethod
    def _build_ansible_command(
        vm_settings: VmSettings,
        ansible_settings: AnsibleSettings,
        gitlab_settings: GitLabSettings,
    ) -> str:
        playbook_path = os.path.abspath(ansible_settings.playbook_path)
        private_key_path = os.path.expanduser(ansible_settings.private_key_path)

        extra_vars = {
            "ansible_python_interpreter": ansible_settings.python_interpreter,
            "gitlab_ipv4": vm_settings.ipv4_address,
            "gitlab_external_url": gitlab_settings.external_url,
            "gitlab_fqdn": vm_settings.fqdn,
            "gitlab_edition": gitlab_settings.edition,
            "gitlab_tls_mode": gitlab_settings.tls_mode,
        }

        return " ".join(
            [
                "ansible-playbook",
                "-i",
                shlex.quote(f"{vm_settings.ipv4_address},"),
                "-u",
                shlex.quote(vm_settings.ansible_user),
                "--private-key",
                shlex.quote(private_key_path),
                "--ssh-common-args",
                shlex.quote("-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"),
                shlex.quote(playbook_path),
                "--extra-vars",
                shlex.quote(json.dumps(extra_vars)),
            ]
        )

    @staticmethod
    def _file_sha256(path: str) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as file_handle:
            hasher.update(file_handle.read())
        return hasher.hexdigest()
