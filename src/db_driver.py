import pyodbc

PREFERRED_DRIVERS = (
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server",
)


def get_sql_server_driver() -> str:
    """Returns the best installed SQL Server ODBC driver."""
    available_drivers = set(pyodbc.drivers())
    for candidate in PREFERRED_DRIVERS:
        if candidate in available_drivers:
            return candidate
    raise RuntimeError(
        "No SQL Server ODBC driver is installed. Install Microsoft ODBC Driver 18 "
        "for SQL Server and restart the app."
    )


SQL_SERVER_DRIVER = get_sql_server_driver()

# The legacy "SQL Server" driver breaks on pyodbc's setinputsizes calls
ENGINE_OPTIONS = {"use_setinputsizes": False} if SQL_SERVER_DRIVER == "SQL Server" else {}
