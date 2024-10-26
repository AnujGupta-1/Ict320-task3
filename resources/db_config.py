from azure.cosmos import CosmosClient
import pyodbc
from Utils.logger_config import logger


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
    try:
        client = CosmosClient(COSMOS_URI, COSMOS_KEY)
        logger.info("Successfully connected to Cosmos DB.")
        return client.get_database_client(DATABASE_NAME)
    except Exception as e:
        logger.error(f"Failed to connect to Cosmos DB: {e}")
        raise


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
    


SQL_SERVER_LOCAL = 'campserver.database.windows.net'
SQL_DATABASE_LOCAL = 'CampsiteSQL'
SQL_USERNAME_LOCAL = 'anuj'
SQL_PASSWORD_LOCAL = 'Hammer@345'

def get_sql_connection_local():
    """
    Establishes a connection to the local SQL database using pyodbc.
    
    Returns:
        pyodbc.Connection: The connection object to interact with the local SQL database.
    """
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            f'SERVER={SQL_SERVER_LOCAL};'
            f'DATABASE={SQL_DATABASE_LOCAL};'
            f'UID={SQL_USERNAME_LOCAL};'
            f'PWD={SQL_PASSWORD_LOCAL};'
            'Encrypt=no;'  # Encryption might not be needed for local connections
            'TrustServerCertificate=yes;'  # Often useful for local development
            'Connection Timeout=30;'
        )
        logger.info("Successfully connected to Local SQL Database.")
        return conn
    except pyodbc.Error as e:
        logger.error(f"Failed to connect to Local SQL Database: {e}")
        raise
