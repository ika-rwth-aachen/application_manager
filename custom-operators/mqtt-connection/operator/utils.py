#!/usr/bin/env python3

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

import aiofiles
import os
import yaml


async def save_dict_as_yaml(path: str, dictionary: dict) -> None:
    """Saves a dictionary as a YAML file asynchronously

    Args:
        path (str): The file path where the YAML file will be saved.
        dictionary (dict): The dictionary to be saved as YAML.
    """
    async with aiofiles.open(path, "w") as f:
        await f.write(yaml.dump(dictionary))

async def load_yaml_as_dict(path: str) -> dict:
    """Loads a YAML file as a dictionary asynchronously. If the file 
       does not exist, it creates the file and writes an empty YAML object to it.
    Args:
        path (str): The file path from which the YAML file will be loaded
    Returns:
        dict: The loaded dictionary from the YAML file
    """
    if not os.path.exists(path):
        # File does not exist, create it and write empty YAML object to it
        async with aiofiles.open(path, "w") as file:
            await file.write(yaml.dump({}))

    async with aiofiles.open(path, "r") as f:
        content = await f.read()
        return yaml.safe_load(content)

def get_chart_name_and_version(
        default_chart_name: str,
        default_chart_version: str,
        app_type: str, 
        helm_charts_reference: dict
    ) -> list[str]:
    """Gets chart name and version from the helm_charts_reference.
    Args:
        default_chart_name (str): Default name of the chart
        default_chart_version (str): Default version of the chart
        app_type (str): Type of the application
    Returns:
        list[str]: Chart name and version
    """
    chart_name = default_chart_name
    chart_version = default_chart_version
    if helm_charts_reference:
        for chart in helm_charts_reference:
            if chart.get("type") == app_type:
                if chart.get("chart_name"):
                    chart_name = chart.get("chart_name")
                chart_version = chart.get("chart_version")
                break
    return [chart_name, chart_version]