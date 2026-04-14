from __future__ import annotations

import pulumi

from .components.GitLabAnsibleProvisioner import GitLabAnsibleProvisioner
from .components.ProxmoxCloudImageDownloader import ProxmoxCloudImageDownloader
from .components.GitLabVirtualMachine import GitLabVirtualMachine
from .StackConfigLoader import StackConfigLoader
from .ProxmoxProviderFactory import ProxmoxProviderFactory


class GitLabInfrastructureStack:
    """Orchestrates the complete Proxmox + Ansible GitLab deployment."""

    def __init__(self) -> None:
        self.settings = StackConfigLoader.load()

    def deploy(self) -> None:
        provider = ProxmoxProviderFactory(self.settings.proxmox).build()
        cloud_image = ProxmoxCloudImageDownloader(
            "gitlab-cloud-image",
            settings=self.settings.vm,
            provider=provider,
        )

        vm = GitLabVirtualMachine(
            "gitlab",
            settings=self.settings.vm,
            cloud_image_file_id=cloud_image.file_id,
            provider=provider,
        )

        provisioner = GitLabAnsibleProvisioner(
            "gitlab-provisioner",
            vm_settings=self.settings.vm,
            ansible_settings=self.settings.ansible,
            gitlab_settings=self.settings.gitlab,
            vm_component=vm,
        )

        pulumi.export("gitlabUrl", self.settings.gitlab.external_url)
        pulumi.export("gitlabVmId", vm.vm_id)
        pulumi.export("gitlabVmNode", vm.node_name)
        pulumi.export("gitlabVmIpv4", vm.ipv4_address)
        pulumi.export("gitlabCloudImageFileId", cloud_image.file_id)
        pulumi.export("ansibleProvisionStdout", provisioner.run.stdout)
