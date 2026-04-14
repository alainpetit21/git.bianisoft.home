from __future__ import annotations

import pulumi
import pulumi_proxmoxve as proxmoxve

from .SettingsClasses import ProxmoxSettings


class ProxmoxProviderFactory:
    """Creates a configured Proxmox provider instance."""

    def __init__(self, settings: ProxmoxSettings) -> None:
        self._settings = settings

    def build(self) -> proxmoxve.Provider:
        api_token = pulumi.Output.concat(
            self._settings.api_token_id,
            "=",
            self._settings.api_token_secret,
        )

        ssh_config = None
        if self._settings.ssh_username is not None and self._settings.ssh_password is not None:
            ssh_config = {
                "username": self._settings.ssh_username,
                "password": self._settings.ssh_password,
            }

        return proxmoxve.Provider(
            "proxmox-provider",
            endpoint=self._settings.endpoint,
            insecure=self._settings.insecure,
            api_token=api_token,
            ssh=ssh_config,
        )
