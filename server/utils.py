import base64
import contextvars
import os
import subprocess
import sys
from typing import Any

from databricks.sdk import WorkspaceClient

header_store = contextvars.ContextVar("header_store")


def get_workspace_client():
    return WorkspaceClient()


def get_user_authenticated_workspace_client():
    # Check if running in a Databricks App environment
    is_databricks_app = "DATABRICKS_APP_NAME" in os.environ

    if not is_databricks_app:
        # Running locally, use default authentication
        return WorkspaceClient()

    # Running in Databricks App, require user authentication token
    headers = header_store.get({})
    token = headers.get("x-forwarded-access-token")

    if not token:
        raise ValueError(
            "Authentication token not found in request headers (x-forwarded-access-token). "
        )

    return WorkspaceClient(token=token, auth_type="pat")

def list_catalogs() -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        catalogs = [{"name": c.name, "comment": c.comment} for c in w.catalogs.list()]
        return {"catalogs": catalogs}
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve catalogs or doesn't have access to the user"}


def list_schemas(catalog_name: str) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        schemas = [
            {"name": s.name, "full_name": s.full_name, "comment": s.comment}
            for s in w.schemas.list(catalog_name=catalog_name)
        ]
        return {"schemas": schemas}
    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to retrieve schemas for catalog '{catalog_name}' or doesn't have access to the user",
        }


def list_tables(catalog_name: str, schema_name: str) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        tables = [
            {
                "name": t.name,
                "full_name": t.full_name,
                "table_type": t.table_type.value if t.table_type else None,
            }
            for t in w.tables.list(catalog_name=catalog_name, schema_name=schema_name)
        ]
        return {"tables": tables}
    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to retrieve tables for catalog '{catalog_name}' and schema '{schema_name}' or doesn't have access to the user",
        }


def get_table(full_name: str) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        t = w.tables.get(full_name=full_name)
        cols = [{"name": c.name, "type": str(c.type_text), "comment": c.comment} for c in (t.columns or [])]
        return {
            "name": t.name,
            "full_name": t.full_name,
            "table_type": t.table_type.value if t.table_type else None,
            "columns": cols,
            "comment": t.comment,
        }
    except Exception as e:
        return {"error": str(e), "message": f"Failed to retrieve table '{full_name}' or doesn't have access to the user"}

def list_volumes(catalog_name: str, schema_name: str) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        volumes = [
            {
                "name": v.name,
                "full_name": v.full_name,
                "volume_type": v.volume_type.value if v.volume_type else None,
            }
            for v in w.volumes.list(catalog_name=catalog_name, schema_name=schema_name)
        ]
        return {"volumes": volumes}
    except Exception as e:
        return {
            "error": str(e),
            "message": f"Failed to retrieve volumes for catalog '{catalog_name}' and schema '{schema_name}' or doesn't have access to the user",
        }


def list_dbfs(path: str = "/") -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        files = [
            {"path": f.path, "is_dir": f.is_dir, "file_size": f.file_size}
            for f in w.dbfs.list(path=path)
        ]
        return {"entries": files}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to retrieve DBFS contents for path '{path}' or doesn't have access to the user"}


def dbfs_mkdirs(path: str) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        w.dbfs.mkdirs(path=path)
        return {"path": path, "status": "created"}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to create directory '{path}' in DBFS or doesn't have access to the user"}


def dbfs_delete(path: str, recursive: bool = False) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        w.dbfs.delete(path=path, recursive=recursive)
        return {"path": path, "status": "deleted"}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to delete '{path}' in DBFS or doesn't have access to the user"}


def dbfs_move(source_path: str, destination_path: str) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        w.dbfs.move(source_path=source_path, destination_path=destination_path)
        return {"from": source_path, "to": destination_path, "status": "moved"}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to move '{source_path}' to '{destination_path}' in DBFS or doesn't have access to the user"}


def dbfs_read(path: str, length: int = 2048) -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        result = w.dbfs.read(path=path, length=length, offset=0)
        content = base64.b64decode(result.data).decode("utf-8", errors="replace") if result.data else ""
        return {"path": path, "content": content}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to read '{path}' in DBFS or doesn't have access to the user"}

def list_notebooks(path: str = "/") -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        items = list(w.workspace.list(path=path))
        result = [{"path": i.path, "type": i.object_type.value if i.object_type else None, "language": i.language.value if i.language else None} for i in items]
        return {"notebooks": result}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to list notebooks for path '{path}' or doesn't have access to the user"}

def export_notebook(path: str) -> dict:
    try:
        from databricks.sdk.service.workspace import ExportFormat
        w = get_user_authenticated_workspace_client()
        exported = w.workspace.export(path=path, format=ExportFormat.SOURCE)
        content = base64.b64decode(exported.content).decode("utf-8") if exported.content else ""
        return {'content': content}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to export notebook '{path}' or doesn't have access to the user"}
    
def import_notebook(path: str, content: str, language: str = "PYTHON", overwrite: bool = True) -> dict:
    try:
        from databricks.sdk.service.workspace import ImportFormat, Language
        w = get_user_authenticated_workspace_client()
        lang_map = {"PYTHON": Language.PYTHON, "SQL": Language.SQL, "SCALA": Language.SCALA, "R": Language.R}
        encoded = base64.b64encode(content.encode()).decode()
        w.workspace.import_(
            path=path,
            content=encoded,
            format=ImportFormat.SOURCE,
            language=lang_map.get(language.upper(), Language.PYTHON),
            overwrite=overwrite,
        )
        return {"path": path, "status": "imported"}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to import notebook '{path}' or doesn't have access to the user"}
    
def list_clusters() -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        clusters = list(w.clusters.list())
        result = [{"cluster_id": c.cluster_id, "cluster_name": c.cluster_name, "state": c.state.value if c.state else None, "spark_version": c.spark_version} for c in clusters]
        return {'result': result}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to list clusters or doesn't have access to the user"}

def list_warehouses() -> dict:
    try:
        w = get_user_authenticated_workspace_client()
        warehouses = list(w.warehouses.list())
        result = [{"warehouse_id": w.id, "warehouse_name": w.name, "state": w.state.value if w.state else None} for w in warehouses]
        return {'result': result}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to list warehouses or doesn't have access to the user"}



