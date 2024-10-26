# db_config.py

from azure.cosmos import CosmosClient
import pyodbc


# Cosmos DB connection details
COSMOS_URI = "https://findacampsitebookings.documents.azure.com:443/"
COSMOS_KEY = "WA3cA5mSjNEwYoPxHJKt3LJ6XMEYvkyUcPK08kxo5eQ4qWrrjG3ItOD1v5L1fHJgsxYcaHSIoBpIACDbhCWAdA=="
DATABASE_NAME = "CampsiteBookingsDB"

def get_cosmos_client():
    """
    Establishes a connection to the Cosmos DB instance and returns a database client.
    
    Returns:
        CosmosClient: The client to interact with the Cosmos DB database.
    """
    client = CosmosClient(COSMOS_URI, COSMOS_KEY)
    return client.get_database_client(DATABASE_NAME)

# Azure SQL connection details
SQL_SERVER = 'headoffice1.database.windows.net'
SQL_DATABASE = 'camping'
SQL_USERNAME = 'anuj'
SQL_PASSWORD = 'Hammer@345'

def get_sql_connection():
    """
    Establishes a connection to the Azure SQL database using pyodbc.
    
    Returns:
        pyodbc.Connection: The connection object to interact with the SQL database.
    """
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={SQL_SERVER};'
        f'DATABASE={SQL_DATABASE};'
        f'UID={SQL_USERNAME};'
        f'PWD={SQL_PASSWORD}'
    )
    return conn
