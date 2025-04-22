#!/usr/bin/env python3

import logging
from typing import Optional

from pyhelm3 import Chart, Client, Error, ReleaseRevision
from pyhelm3.errors import ChartNotFoundError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


class HelmAPI:

    def __init__(
        self,
        url_app_registry: str,
        kube_config_file: Optional[str] = None,
    ) -> None:
        """Initializes the Helm API
        Args:
            url_app_registry (str): URL of the application registry
            kube_config_file (str, optional): Path to the kubeconfig file. Defaults to None.
        """
        self.url_application_registry = url_app_registry

        if kube_config_file is None:
            self.client = Client()
        else:
            self.client = Client(kubeconfig=kube_config_file)

    async def fetch_chart(self, chart_name: str, version: Optional[str] = None) -> Chart:
        """Fetches a chart from the application registry
        Args:
            chart_name (str): Name of the chart
            version (str, optional): Version of the chart. Defaults to None. Per default, Helm fetches the latest version.
        Returns:
            Chart: Chart object
        """
        try:
            chart = await self.client.get_chart(
                chart_ref=f"{self.url_application_registry}/v{version}/{chart_name}-{version}.tgz"
            )
        except ChartNotFoundError as e:
            logging.error(f"Failed to fetch chart '{chart_name}': {e}")
            raise e
        return chart

    async def install_or_upgrade_release(
        self, release_name: str, chart: Chart, config: dict, namespace: str) -> ReleaseRevision:
        """Upgrades or install a release
        Args:
            release_name (str): Release name
            chart (Chart): Chart object
            config (dict): Values to be set in the values.yaml file
            namespace (str): Namespace to install the release to
        Returns:
            ReleaseRevision: Metadata of the release revision
        """
        revision = await self.client.install_or_upgrade_release(release_name, chart, config, namespace=namespace)
        return revision

    async def uninstall_release(self, release_name: str, namespace: str) -> None:
        """Uninstalls a release identified by release name and namespace
        Args:
            release_name (str): Release name
            namespace (str): Namespace of the release name
        """
        try:
            await self.client.uninstall_release(release_name=release_name, namespace=namespace)
        except Error as e:
            logging.error(f"Failed to uninstall helm release: {e}")