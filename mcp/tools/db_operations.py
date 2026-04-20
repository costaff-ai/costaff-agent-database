import os
import json
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from pathlib import Path

# Load multi-DB config from env
def _get_db_config():
    raw = os.getenv("DATABASE_CONFIG", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}

def _workspace():
    return os.getenv("DATABASE_WORKSPACE_DIR", "/app/data/workspace")

def get_connected_databases() -> str:
    """
    Returns a list of all connected database aliases and their descriptions.
    Use this to know which DBs are available for querying.
    """
    conf = _get_db_config()
    if not conf:
        return "No databases configured. Please set DATABASE_CONFIG env var."
    
    summary = []
    for alias, info in conf.items():
        summary.append({
            "alias": alias,
            "type": info.get("type", "unknown"),
            "description": info.get("desc", "No description")
        })
    return json.dumps(summary, ensure_ascii=False, indent=2)

def inspect_database(db_alias: str) -> str:
    """
    Lists all tables in the specified database.
    """
    conf = _get_db_config()
    if db_alias not in conf:
        return f"Error: Database alias '{db_alias}' not found."
    
    try:
        engine = create_engine(conf[db_alias]["url"])
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return json.dumps({"database": db_alias, "tables": tables}, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error connecting to '{db_alias}': {str(e)}"

def inspect_table(db_alias: str, table_name: str) -> str:
    """
    Gets the schema (columns and types) and a few sample rows from a specific table.
    """
    conf = _get_db_config()
    if db_alias not in conf:
        return f"Error: Database alias '{db_alias}' not found."
    
    try:
        engine = create_engine(conf[db_alias]["url"])
        inspector = inspect(engine)
        
        # Get columns
        columns = [
            {"name": c["name"], "type": str(c["type"]), "nullable": c["nullable"]}
            for c in inspector.get_columns(table_name)
        ]
        
        # Get sample rows
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
            samples = [dict(row._mapping) for row in result]
            
        return json.dumps({
            "table": table_name,
            "columns": columns,
            "sample_rows": json.loads(pd.DataFrame(samples).to_json(orient="records"))
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error inspecting table '{table_name}' in '{db_alias}': {str(e)}"

def query(db_alias: str, sql: str, output_filename: str = None) -> str:
    """
    Executes a SQL query on the specified database.
    If output_filename is provided, saves result as CSV in workspace and returns the path.
    Otherwise, returns JSON result (limited to 100 rows).
    """
    conf = _get_db_config()
    if db_alias not in conf:
        return f"Error: Database alias '{db_alias}' not found."
    
    try:
        engine = create_engine(conf[db_alias]["url"])
        df = pd.read_sql(text(sql), engine)
        
        if output_filename:
            os.makedirs(_workspace(), exist_ok=True)
            path = Path(_workspace()) / output_filename
            df.to_csv(path, index=False)
            return f"Success: Query results saved to {output_filename}"
        
        # Limit JSON return to prevent context overflow
        result_subset = df.head(100).to_dict(orient="records")
        return json.dumps({
            "database": db_alias,
            "row_count": len(df),
            "data": result_subset,
            "note": "Returning first 100 rows. Use output_filename to save full results."
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Error executing query on '{db_alias}': {str(e)}"
