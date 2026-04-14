from __future__ import annotations

import pulumi
import pulumi_proxmoxve as proxmoxve

from iac.SettingsClasses import VmSettings


class ProxmoxCloudImageDownloader(pulumi.ComponentResource):
    """Ensure the cloud image exists on Proxmox and expose its file identifier."""

    def __init__(
        self,
        name: str,
        settings: VmSettings,
        provider: proxmoxve.Provider,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__("bianisoft:proxmox:ProxmoxCloudImageDownloader", name, None, opts)

        invoke_opts = pulumi.InvokeOptions(provider=provider)
        existing_file_id = self._try_get_existing_file_id(settings, invoke_opts)

        if existing_file_id is not None:
            pulumi.log.info(
                f"Reusing existing cloud image '{settings.image_file_name}' in datastore '{settings.image_datastore_name}'.",
                resource=self,
            )
            self.file_id = pulumi.Output.from_input(existing_file_id)
            self.download = None
        else:
            resource_opts = pulumi.ResourceOptions(parent=self, provider=provider)
            self.download = proxmoxve.download.File(
                f"{name}-download",
                node_name=settings.node_name,
                datastore_id=settings.image_datastore_name,
                content_type=settings.image_content_type,
                file_name=settings.image_file_name,
                url=settings.image_url,
                verify=settings.image_verify_tls,
                overwrite=False,
                overwrite_unmanaged=False,
                opts=resource_opts,
            )
            self.file_id = self.download.id

        self.register_outputs({"fileId": self.file_id})

    @staticmethod
    def _try_get_existing_file_id(
        settings: VmSettings,
        invoke_opts: pulumi.InvokeOptions,
    ) -> str | None:
        try:
            file_info = proxmoxve.get_file(
                node_name=settings.node_name,
                datastore_id=settings.image_datastore_name,
                content_type=settings.image_content_type,
                file_name=settings.image_file_name,
                opts=invoke_opts,
            )
            return file_info.id
        except Exception:
            return None
