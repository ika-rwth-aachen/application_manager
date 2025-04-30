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

from application_manager_interfaces.msg import Connection

class BaseConnection:

    def __init__(self, connection: Connection, broker_node_id: str, connection_id: str) -> None:
        """Initializes the connection
        Args:
            connection (Connection): Connection from application_manager_interfaces
            broker_node_id (str): Broker node ID
            connection_id (str): Connection ID
        """
        self.connection = connection
        self.broker_node_id = broker_node_id
        self.connection_id = connection_id

    def get_connection_type(self) -> str:
        """Returns the type of the connection
        Returns:
            str: Type of the connection
        """
        return self.connection_type
    
    def get_default_helm_chart_name(self) -> str:
        """Returns the default name of the Helm chart
        Returns:
            str: Name of the Helm chart
        """
        return self.default_helm_chart_name
