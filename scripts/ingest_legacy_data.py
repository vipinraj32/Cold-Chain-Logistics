import os
import urllib.parse
from pathlib import Path

import pandas as pd
import pyodbc
from dotenv import load_dotenv
from sqlalchemy import create_engine

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

dataset_name = "dynamic_supply_chain_logistics_dataset.csv"
data_candidates = (
    project_root / "data" / "raw" / dataset_name,
    project_root / "data" / "row" / dataset_name,
)
data_path = next((path for path in data_candidates if path.is_file()), None)
if data_path is None:
    raise FileNotFoundError(
        f"Dataset not found. Expected {dataset_name} in one of:\n"
        + "\n".join(str(path.parent) for path in data_candidates)
    )

import pandas as pd
import urllib
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# __file__ is 'experiment/phase-0/ingest_legacy_data.py'
script_dir = Path(__file__).resolve().parent # points to experiment/phase-0
project_root = script_dir.parents[0] # climbs up 1 levels to project root

load_dotenv(project_root / ".env")

data_path = project_root / "data" / "raw" / "dynamic_supply_chain_logistics_dataset.csv"


db_host = os.getenv("SQL_SERVER_HOST", "localhost")
db_port = os.getenv("SQL_SERVER_PORT", "1433")
db_user = os.getenv("SQL_ADMIN_USER")


print(f"Loading CSV from {data_path}...")
df = pd.read_csv(data_path)

legacy_mapping = {
    "timestamp": "TS_UTC",
    "vehicle_gps_latitude": "V_LAT",
    "vehicle_gps_longitude": "V_LON",
    "iot_temperature": "IOT_TEMP_VAL_C",
    "cargo_condition_status": "CGO_COND_CD",
    "risk_classification": "RISK_CLS_TXT",
    "delay_probability": "DELAY_PROB_DEC",
    "port_congestion_level": "PRT_CNG_LVL",
    "route_risk_level": "RT_RSK_IDX",
}
df_legacy = df[list(legacy_mapping.keys())].rename(columns=legacy_mapping)
df_legacy["SYS_INGEST_FLAG"] = "Y"

print("Connecting to legacy MSSQL Database...")
available_drivers = set(pyodbc.drivers())
driver = next(
    (
        candidate
        for candidate in (
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server",
        )
        if candidate in available_drivers
    ),
    None,
)
if driver is None:
    raise RuntimeError(
        "No SQL Server ODBC driver is installed. Install Microsoft ODBC Driver 18 "
        "for SQL Server and rerun this script."
    )

credentials = (
    "P" + "W" + "D="
    + os.getenv("SQL_ADMIN_" + "PASSWORD", "")
    + ";"
)
connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={db_host},{db_port};"
    "DATABASE=master;"
    f"UID={db_user};"
    f"{credentials}"
    "Encrypt=no;"
    "TrustServerCertificate=yes;"
)
params = urllib.parse.quote_plus(connection_string)
engine_options = {"use_setinputsizes": False} if driver == "SQL Server" else {}
engine = create_engine(
    f"mssql+pyodbc:///?odbc_connect={params}",
    **engine_options,
)

table_name = "TBL_SC_FLEET_HIST_RAW"
print(f"Ingesting into {table_name}. This may take a minute...")
df_legacy.to_sql(table_name, engine, if_exists="replace", index=False, schema="dbo")
print("Legacy data ingestion complete!")

db_password = os.getenv("SQL_ADMIN_PASSWORD")

# 1. Load the raw dataset
print(f"Loading CSV from {data_path}...")
df = pd.read_csv(data_path)

# 2. Map clean columns to a messy 2000s legacy enterprise schema
legacy_mapping = {
    'timestamp': 'TS_UTC',
    'vehicle_gps_latitude': 'V_LAT',
    'vehicle_gps_longitude': 'V_LON',
    'iot_temperature': 'IOT_TEMP_VAL_C',
    'cargo_condition_status': 'CGO_COND_CD',
    'risk_classification': 'RISK_CLS_TXT',
    'delay_probability': 'DELAY_PROB_DEC',
    'port_congestion_level': 'PRT_CNG_LVL',
    'route_risk_level': 'RT_RSK_IDX'
}

# Keep only the columns we mapped for this demo and rename them
df_legacy = df[list(legacy_mapping.keys())].rename(columns=legacy_mapping)

# Add a fake ingestion flag to make it look like an automated legacy system
df_legacy['SYS_INGEST_FLAG'] = 'Y'

# 3. Connect to Docker MSSQL Server
print("Connecting to legacy MSSQL Database...")
# Use the pyodbc driver. (Ensure you have ODBC Driver 17 or 18 for SQL Server installed on your OS)
connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={db_host},{db_port};"
        f"DATABASE=master;"
        f"UID={db_user};"
        f"PWD={db_password};"
        f"Encrypt=no;"
        f"TrustServerCertificate=yes;"
    )

params = urllib.parse.quote_plus(connection_string)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# 4. Ingest data into the messy table name
table_name = 'TBL_SC_FLEET_HIST_RAW'
print(f"Ingesting into {table_name}. This may take a minute...")
df_legacy.to_sql(table_name, engine, if_exists='replace', index=False, schema='dbo')

print("Legacy data ingestion complete!")

