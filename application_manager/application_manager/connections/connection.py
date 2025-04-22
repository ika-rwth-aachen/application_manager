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
