# ==============================================================================
# MIT License

# Copyright (c) 2025 Institute for Automotive Engineering (ika), RWTH Aachen University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import asyncio
import logging

import kopf
import yaml
from kubernetes_asyncio import client, config
from kubernetes_asyncio.client.exceptions import ApiException

from helm_api import HelmAPI
from utils import get_chart_name_and_version, load_yaml_as_dict, save_dict_as_yaml

logging.getLogger('pyhelm3.command').setLevel(logging.WARNING)


@kopf.on.startup()
async def init(memo: kopf.Memo, **kwargs) -> None:
    """Initializes the operator on startup.
       This function loads the configuration, sets up the Kubernetes client, and initializes
       the Helm API and custom objects API. It also loads the Helm chart from the application registry.
    Args:
        memo (kopf.Memo): A shared memory object for storing data across handlers
        **kwargs: Additional keyword arguments
    """
    app_type = "TYPE_MQTT"
    default_chart_name = "mqtt-connection-helm"
    default_chart_version = "0.1.0"
    
    # Load configuration from file
    with open('/config/config.yml', 'r') as config_file:
        config_yml = yaml.safe_load(config_file)
    url_application_registry = config_yml.get('url_application_registry')
    configmap_application_registry_interface = config_yml.get('configmap_application_registry_interface')
    configmap_namespace = config_yml.get('configmap_namespace')
    if not configmap_namespace:
        configmap_namespace = "default"

    # Set up the Kubernetes client and the Helm API
    logging.info("Loading in-cluster configuration")
    config.load_incluster_config()
    core_v1_api = client.CoreV1Api()
    memo.helm_api = HelmAPI(url_app_registry=url_application_registry)
    memo.custom_object = client.CustomObjectsApi()

    # Load the chart from the application registry
    helm_charts_reference = None
    if configmap_application_registry_interface:
        try:
            helm_charts_configmap = await core_v1_api.read_namespaced_config_map(
                name=configmap_application_registry_interface,
                namespace=configmap_namespace
            )
            helm_charts_reference = yaml.safe_load(helm_charts_configmap.data["application_registry_interface.yml"])["helm_charts"]
        except ApiException as e:
            if e.status == 404:
                print(f"ERROR: ConfigMap '{configmap_application_registry_interface}' does not exist in namespace {configmap_namespace}.")
            else:
                print(f"Error occurred while fetching ConfigMap {configmap_application_registry_interface}: {e}")
    [chart_name, chart_version] = get_chart_name_and_version(default_chart_name, default_chart_version, app_type, helm_charts_reference)
    memo.chart = await memo.helm_api.fetch_chart(chart_name=chart_name, version=chart_version)
    # Bookkeeping of requesters:
    memo.mounted_path = "bookkeeping_data/"
    memo.bookkeeping_path = memo.mounted_path + "mqtt_bookkeeping.yml"
    memo.bookkeeping = await load_yaml_as_dict(memo.bookkeeping_path)
    # Versioning of operator configurations from CR considering resourceVersion:
    memo.versioning_path = memo.mounted_path + "mqtt_versioning.yml"
    memo.versioning = await load_yaml_as_dict(memo.versioning_path)


@kopf.on.create("ika.rwth-aachen.de", "v1", "mqttconnections")
async def create_connection(memo, spec, body, **kwargs):
    """Handles the creation of a new Custom Resource 'mqttconnections'.
       This function installs or upgrades a Helm release based on the configuration provided 
       via the Custom Resource.
    Args:
        memo (kopf.Memo): A shared memory object for storing data across handlers
        spec (dict): The specification of the Custom Resource
        body (dict): The full body of the Custom Resource
        **kwargs: Additional keyword arguments
    """
    cr_name = body['metadata']['name']
    logging.info(f"[MQTT Connection Operator] Custom Resource '{cr_name}' was created.")
    config = dict(spec) # shallow copy, as some keys will be popped
    config_operator = config.pop("operator", None)
    verify_operator_config(config_operator, "kopf.on.create('mqttconnections')")
    assert not config_operator["shutdown"], "[MQTT Connection Operator] kopf.on.create('mqttconnections'): Shutdown is requested but CR is not deployed yet."
    memo.versioning.setdefault(cr_name, {})
    memo.versioning[cr_name][body['metadata']['resourceVersion']] = config_operator
    await save_dict_as_yaml(path=memo.versioning_path, dictionary=memo.versioning)
    logging.info(f"[MQTT Connection Operator] Requesters of CR '{cr_name}' are: {config_operator['requester']}")
    await memo.helm_api.install_or_upgrade_release(
        release_name=cr_name,
        chart=memo.chart,
        config=config,
        namespace=config_operator["namespace"],
    )
    logging.info(f"[MQTT Connection Operator] Helm release for CR '{cr_name}' installed with release name '{cr_name}'")
    memo.bookkeeping[cr_name] = config_operator["requester"]
    await save_dict_as_yaml(path=memo.bookkeeping_path, dictionary=memo.bookkeeping)


@kopf.on.update("ika.rwth-aachen.de", "v1", "mqttconnections")
async def update_connection(memo, spec, body, retry, **kwargs):
    """Handles the update of an existing Custom Resource 'mqttconnections'.
       This function updates the Helm release based on the configuration provided via the
       the Custom Resource, updates the Bookkeeping, and handles shutdown requests.
    Args:
        memo (kopf.Memo): A shared memory object for storing data across handlers
        spec (dict): The specification of the Custom Resource
        body (dict): The full body of the Custom Resource
        retry (bool): Indicates if this is a retry of a failed update
        **kwargs: Additional keyword arguments
    """
    cr_name = body['metadata']['name']
    logging.info(f"[MQTT Connection Operator] Custom Resource '{cr_name}' was updated.")
    config = dict(spec) # shallow copy, as some keys will be popped
    config_operator = config.pop("operator", None)
    verify_operator_config(config_operator, "kopf.on.update('mqttconnections')")
    memo.versioning[cr_name][body['metadata']['resourceVersion']] = config_operator
    await save_dict_as_yaml(path=memo.versioning_path, dictionary=memo.versioning)
    match config_operator["shutdown"]:
        case True:
            if not retry:
                for requester in config_operator["requester"]:
                    # In case of shutdown request, remove the specified requesters from the bookkeeping
                    memo.bookkeeping[cr_name].remove(requester)
                await save_dict_as_yaml(path=memo.bookkeeping_path, dictionary=memo.bookkeeping)
            if not memo.bookkeeping[cr_name]:
                # If no requesters are left, delete the CR
                logging.info(f"[MQTT Connection Operator] No Requesters left. Delete CR '{cr_name}' ..")
                await memo.custom_object.delete_namespaced_custom_object(
                    group="ika.rwth-aachen.de",
                    version="v1",
                    namespace=config_operator["namespace"],
                    plural="mqttconnections",
                    name=cr_name,
                    grace_period_seconds=5,
                )
        case False:
            if not retry:
                # Add new requesters to the bookkeeping
                memo.bookkeeping[cr_name].extend(config_operator["requester"])
                await save_dict_as_yaml(path=memo.bookkeeping_path, dictionary=memo.bookkeeping)
        case _:
            raise Exception("Unexpected Bool")
    logging.info(f"[MQTT Connection Operator] According to Bookkeeping, Requesters of CR '{cr_name}' are: '{memo.bookkeeping[cr_name]}'")


@kopf.on.delete("ika.rwth-aachen.de", "v1", "mqttconnections")
async def delete_connection(memo, spec, body, **kwargs):
    """Handles the deletion of an existing Custom Resource 'mqttconnections'.
       This function uninstalls the Helm release associated with the Custom Resource and 
       updates the Bookkeeping.
    Args:
        memo (kopf.Memo): A shared memory object for storing data across handlers
        spec (dict): The specification of the Custom Resource
        body (dict): The full body of the Custom Resource
        **kwargs: Additional keyword arguments
    """
    cr_name = body['metadata']['name']
    logging.info(f"[MQTT Connection Operator] Custom Resource '{cr_name}' was deleted.")
    await memo.helm_api.uninstall_release(
        release_name=cr_name, 
        namespace=spec["operator"]["namespace"]
    )
    memo.bookkeeping.pop(cr_name, None)
    await save_dict_as_yaml(path=memo.bookkeeping_path, dictionary=memo.bookkeeping)


def verify_operator_config(config: dict, caller_name: str) -> None:
    """Verifies the operator configuration.
       This function checks whether the required keys are present in the operator configuration.
    Args:
        config (dict): The operator configuration
        caller_name (str): The name of the caller function for logging purposes
    Raises:
        AssertionError: If any required key is missing from the configuration
    """
    assert config.get("requester", None) is not None, (
        caller_name + " cannot find the requester of the MQTT connection in the operator config"
    )
    assert config.get("namespace", None) is not None, (
        caller_name + " cannot find the namespace of the MQTT connection in the operator config"
    )
    assert config.get("shutdown", None) is not None, (
        caller_name + " cannot find the shutdown flag of the MQTT connection in the operator config"
    )


if __name__ == "__main__":
    asyncio.run(kopf.run())