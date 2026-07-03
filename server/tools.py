"""
Tools module for the MCP server.

This module defines all the tools (functions) that the MCP server exposes to clients.
Tools are the core functionality of an MCP server - they are callable functions that
AI assistants and other clients can invoke to perform specific actions.

Each tool should:
- Have a clear, descriptive name
- Include comprehensive docstrings (used by AI to understand when to call the tool)
- Return structured data (typically dict or list)
- Handle errors gracefully
"""

from server import utils


def load_tools(mcp_server):
    """
    Register all MCP tools with the server.

    This function is called during server initialization to register all available
    tools with the MCP server instance. Tools are registered using the @mcp_server.tool
    decorator, which makes them available to clients via the MCP protocol.

    Args:
        mcp_server: The FastMCP server instance to register tools with. This is the
                   main server object that handles tool registration and routing.

    Example:
        To add a new tool, define it within this function using the decorator:

        @mcp_server.tool
        def my_new_tool(param: str) -> dict:
            '''Description of what the tool does.'''
            return {"result": f"Processed {param}"}
    """

    @mcp_server.tool
    def health() -> dict:
        """
        Check the health of the MCP server and Databricks connection.

        This is a simple diagnostic tool that confirms the server is running properly.
        It's useful for:
        - Monitoring and health checks
        - Testing the MCP connection
        - Verifying the server is responsive

        Returns:
            dict: A dictionary containing:
                - status (str): The health status ("healthy" if operational)
                - message (str): A human-readable status message

        Example response:
            {
                "status": "healthy",
                "message": "Custom MCP Server is healthy and connected to Databricks Apps."
            }
        """
        return {
            "status": "healthy",
            "message": "Custom MCP Server is healthy and connected to Databricks Apps.",
        }

    @mcp_server.tool
    def get_current_user() -> dict:
        """
        Get information about the current authenticated user.

        This tool retrieves details about the user who is currently authenticated
        with the MCP server. When deployed as a Databricks App, this returns
        information about the end user making the request. When running locally,
        it returns information about the developer's Databricks identity.

        Useful for:
        - Personalizing responses based on the user
        - Authorization checks
        - Audit logging
        - User-specific operations

        Returns:
            dict: A dictionary containing:
                - display_name (str): The user's display name
                - user_name (str): The user's username/email
                - active (bool): Whether the user account is active

        Example response:
            {
                "display_name": "John Doe",
                "user_name": "john.doe@example.com",
                "active": true
            }

        Raises:
            Returns error dict if authentication fails or user info cannot be retrieved.
        """
        try:
            w = utils.get_user_authenticated_workspace_client()
            user = w.current_user.me()
            return {
                "display_name": user.display_name,
                "user_name": user.user_name,
                "active": user.active,
            }
        except Exception as e:
            return {"error": str(e), "message": "Failed to retrieve user information"}

    @mcp_server.tool
    def list_catalogs() -> dict:
        """
        List all catalogs visible to the current Databricks workspace client.

        This tool queries the Databricks Catalog API and returns the names of
        catalogs accessible to the configured authentication context.

        Returns:
            dict: A dictionary containing the result of the catalog listing.

        Example response:
            {
                "catalogs": ["main", "sales"],
                "count": 2
            }

        Raises:
            Returns error dict if the list operation fails.
        """
        return utils.list_catalogs()

    @mcp_server.tool
    def list_schemas(catalog_name: str) -> dict:
        """
        List schemas for a given catalog.

        This tool retrieves schema metadata for the requested catalog using the
        Databricks Schemas API. It returns the names, full names, and comments
        of the schemas available to the current user.

        Args:
            catalog_name (str): The catalog name to list schemas from.

        Returns:
            dict: A dictionary with schema metadata or an error payload.

        Example response:
            {
                "schemas": [
                    {"name": "public", "full_name": "main.public", "comment": ""}
                ]
            }
        """
        return utils.list_schemas(catalog_name=catalog_name)

    @mcp_server.tool
    def list_tables(catalog_name: str, schema_name: str) -> dict:
        """
        List tables in a specific catalog and schema.

        This tool queries the Databricks Tables API and returns the table names,
        fully qualified names, and types for the requested catalog/schema.

        Args:
            catalog_name (str): The catalog containing the schema.
            schema_name (str): The schema containing tables.

        Returns:
            dict: A dictionary with table metadata or an error payload.

        Example response:
            {
                "tables": [
                    {"name": "customers", "full_name": "main.public.customers", "table_type": "MANAGED"}
                ]
            }
        """
        return utils.list_tables(catalog_name=catalog_name, schema_name=schema_name)

    @mcp_server.tool
    def get_table(full_name: str) -> dict:
        """
        Retrieve metadata for a specific table.

        This tool returns table metadata and column definitions for the requested
        fully qualified table name.

        Args:
            full_name (str): The fully qualified table name (e.g. "main.public.customers").

        Returns:
            dict: A dictionary containing table details, columns, and comments,
                  or an error payload.

        Example response:
            {
                "name": "customers",
                "full_name": "main.public.customers",
                "table_type": "MANAGED",
                "columns": [
                    {"name": "id", "type": "INT", "comment": ""}
                ]
            }
        """
        return utils.get_table(full_name=full_name)

    @mcp_server.tool
    def list_volumes(catalog_name: str, schema_name: str) -> dict:
        """
        List volumes in a specific catalog and schema.

        This tool queries the Databricks Volumes API and returns information about
        the volumes visible to the current user.

        Args:
            catalog_name (str): The catalog containing the schema.
            schema_name (str): The schema containing volumes.

        Returns:
            dict: A dictionary with volume metadata or an error payload.

        Example response:
            {
                "volumes": [
                    {"name": "data_vol", "full_name": "main.public.data_vol", "volume_type": "DELTA_LAKE"}
                ]
            }
        """
        return utils.list_volumes(catalog_name=catalog_name, schema_name=schema_name)

    @mcp_server.tool
    def list_dbfs(path: str = "/") -> dict | str:
        """
        List files and directories in DBFS at the specified path.

        This tool returns the contents of a DBFS directory, including paths,
        directory flags, and file sizes.

        Args:
            path (str): The DBFS path to list. Defaults to "/".

        Returns:
            str | dict: A JSON string of directory contents or an error payload.

        Example response:
            [
                {"path": "/tmp", "is_dir": true, "file_size": 0}
            ]
        """
        return utils.list_dbfs(path=path)

    @mcp_server.tool
    def dbfs_mkdirs(path: str) -> dict | str:
        """
        Create one or more directories in DBFS.

        This tool creates the requested DBFS directory path and returns a status
        payload that confirms the creation.

        Args:
            path (str): The DBFS path to create.

        Returns:
            str | dict: A JSON string containing creation status or an error payload.

        Example response:
            {"path": "/tmp/newdir", "status": "created"}
        """
        return utils.dbfs_mkdirs(path=path)

    @mcp_server.tool
    def dbfs_delete(path: str, recursive: bool = False) -> dict | str:
        """
        Delete a DBFS file or directory.

        This tool deletes the specified DBFS path. If deleting a directory,
        set recursive=True to remove all nested entries.

        Args:
            path (str): The DBFS path to delete.
            recursive (bool): Whether to delete recursively. Defaults to False.

        Returns:
            str | dict: A JSON string containing deletion status or an error payload.

        Example response:
            {"path": "/tmp/old", "status": "deleted"}
        """
        return utils.dbfs_delete(path=path, recursive=recursive)

    @mcp_server.tool
    def dbfs_move(source_path: str, destination_path: str) -> dict | str:
        """
        Move a DBFS file or directory from one path to another.

        This tool moves the specified source path to the destination path in DBFS.

        Args:
            source_path (str): The source DBFS path.
            destination_path (str): The destination DBFS path.

        Returns:
            str | dict: A JSON string containing move status or an error payload.

        Example response:
            {"from": "/tmp/a", "to": "/tmp/b", "status": "moved"}
        """
        return utils.dbfs_move(source_path=source_path, destination_path=destination_path)

    @mcp_server.tool
    def dbfs_read(path: str, length: int = 2048) -> dict | str:
        """
        Read the contents of a DBFS file.

        This tool reads up to the specified number of bytes from a DBFS file and
        returns its decoded content.

        Args:
            path (str): The DBFS file path to read.
            length (int): The number of bytes to read. Defaults to 2048.

        Returns:
            str | dict: The file contents as a string or an error payload.

        Example response:
            "Hello, world\n"
        """
        return utils.dbfs_read(path=path, length=length)

    @mcp_server.tool
    def list_notebooks(path: str = "/") -> dict:
        """
        List notebooks and other workspace objects under a given workspace path.

        Args:
            path (str): The workspace path to inspect. Defaults to "/".

        Returns:
            dict: A dictionary containing notebook metadata or an error payload.
        """
        return utils.list_notebooks(path=path)

    @mcp_server.tool
    def export_notebook(path: str) -> dict:
        """
        Export a notebook from the Databricks workspace as source text.

        Args:
            path (str): The workspace path to the notebook.

        Returns:
            dict: A dictionary containing the exported notebook content or an error payload.
        """
        return utils.export_notebook(path=path)

    @mcp_server.tool
    def import_notebook(path: str, content: str, language: str = "PYTHON", overwrite: bool = True) -> dict:
        """
        Import or overwrite a notebook in the Databricks workspace.

        Args:
            path (str): The workspace path for the notebook.
            content (str): The notebook content as source text.
            language (str): The notebook language, such as PYTHON or SQL.
            overwrite (bool): Whether to overwrite an existing notebook.

        Returns:
            dict: A dictionary confirming import success or an error payload.
        """
        return utils.import_notebook(path=path, content=content, language=language, overwrite=overwrite)

    @mcp_server.tool
    def list_clusters() -> dict:
        """
        List the Databricks clusters visible to the current workspace client.

        Returns:
            dict: A dictionary with cluster metadata or an error payload.
        """
        return utils.list_clusters()

    @mcp_server.tool
    def list_warehouses() -> dict:
        """
        List the Databricks SQL warehouses visible to the current workspace client.

        Returns:
            dict: A dictionary with warehouse metadata or an error payload.
        """
        return utils.list_warehouses()

    """
    TODO: Add more tools as necessary
    """
