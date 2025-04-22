#!/usr/bin/env python3

from kubernetes import client, config
from typing import Optional


class KubernetesAPI:

    def __init__(self, kube_config_file: Optional[str] = None) -> None:
        """Initializes the KubernetesAPI object
        Args:
            kube_config_file (str, optional): Path to the Kubernetes config file. Defaults to None
        """
        if kube_config_file == None:
            config.load_incluster_config()
        else:
            config.load_kube_config(kube_config_file)
        self.client_core_api = client.CoreV1Api()
        self.custom_object = client.CustomObjectsApi()

    def read_namespaced_configmap(self, configmap_name: str, namespace: Optional[str] = "default") -> client.V1ConfigMap:
        """Reads a ConfigMap from a namespace
        Args:
            configmap_name (str): Name of the ConfigMap
            namespace (str, optional): Namespace where the ConfigMap resides. Defaults to "default"
        Returns:
            client.V1ConfigMap: ConfigMap object
        """
        try:
            configmap = self.client_core_api.read_namespaced_config_map(configmap_name, namespace)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                print(f"ERROR: ConfigMap '{configmap_name}' does not exist in namespace {namespace}.")
                return None
            else:
                print(f"Error occurred while fetching ConfigMap {configmap_name}: {e}")
                return None
        return configmap

    def read_namespaced_secret(self, secret_name: str, namespace: Optional[str] = "default") -> client.V1Secret:
        """Reads a secret from a namespace
        Args:
            secret_name (str): Name of the secret
            namespace (str, optional): Namespace where the secret resides. Defaults to "default"
        Returns:
            client.V1Secret: Secret object
        """
        try:
            secret = self.client_core_api.read_namespaced_secret(secret_name, namespace)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                print(f"ERROR: Secret '{secret_name}' does not exist in namespace {namespace}.")
                return None
            else:
                print(f"Error occurred while fetching Secret {secret_name}: {e}")
                return None
        return secret

    def create_custom_resource(
        self,
        group: str,
        version: str,
        namespace: str,
        plural: str,
        body: dict,
    ) -> object:
        """Creates a custom resource in a namespace
        Args:
            group (str): Group of the custom resource
            version (str): Version of the custom resource
            namespace (str): Namespace where the custom resource resides
            plural (str): Plural name of the custom resource
            body (dict): Body of the custom resource
        Returns:
            object: Created custom resource object
        """
        return self.custom_object.create_namespaced_custom_object(
            group=group, version=version, namespace=namespace, plural=plural, body=body
        )

    def update_custom_resource(
        self,
        group: str,
        version: str,
        namespace: str,
        plural: str,
        name: str,
        body: dict,
    ) -> object:
        """Updates a custom resource in a namespace
        Args:
            group (str): Group of the custom resource
            version (str): Version of the custom resource
            namespace (str): Namespace where the custom resource resides
            plural (str): Plural name of the custom resource
            name (str): Name of the custom resource
            body (dict): Body of the custom resource
        Returns:
            object: Updated custom resource object
        """
        return self.custom_object.patch_namespaced_custom_object(
            group=group, version=version, namespace=namespace, plural=plural, name=name, body=body
        )

    def list_custom_resource(
        self,
        group: str,
        version: str,
        namespace: str,
        plural: str,
    ) -> object:
        """Lists custom resources in a namespace
        Args:
            group (str): Group of the custom resource
            version (str): Version of the custom resource
            namespace (str): Namespace where the custom resource resides
            plural (str): Plural name of the custom resource
        Returns:
            object: List of custom resources
        """
        return self.custom_object.list_namespaced_custom_object(
            group=group, version=version, namespace=namespace, plural=plural
        )
