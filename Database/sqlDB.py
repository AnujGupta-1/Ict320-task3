import pyodbc
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Utils.logger_config import logger
from resources.db_config import get_sql_connection_local  # Importing the local SQL connection function

def connect_to_sql():
    """
    Connects to the local SQL Server database using the `get_sql_connection_local()` function.
    
    :return: Connection object if successful, or None if connection fails.
    """
    try:
        conn = get_sql_connection_local()  # Using the local SQL connection function
        logger.info("Connected to Local SQL database successfully.")
        return conn  # Return the connection object
    except pyodbc.Error as e:
        logger.error(f"Error connecting to Local SQL database: {e}")
        return None  # Return None if the connection fails

def create_schema_if_not_exists(cursor):
    """
    Creates the schema 'camping' if it does not exist.

    :param cursor: Database cursor object.
    """
    try:
        query = """
        IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'camping')
        BEGIN
            EXEC('CREATE SCHEMA camping');
        END
        """
        cursor.execute(query)  # Execute the query
        logger.info("Schema 'camping' checked/created successfully.")
    except pyodbc.Error as e:
        logger.error(f"Error creating schema: {e}")

def create_tables(cursor):
    """
    Creates the necessary tables in the SQL database if they do not exist.

    :param cursor: Database cursor object.
    """
    create_customers_table = """
    IF OBJECT_ID('camping.customers', 'U') IS NULL
    BEGIN
        CREATE TABLE camping.customers (
            customer_id INT IDENTITY(1,1) PRIMARY KEY,
            first_name VARCHAR(255) NOT NULL,
            last_name VARCHAR(255) NOT NULL,
            phone VARCHAR(25) NULL,
            address VARCHAR(255) NULL,
            post_code VARCHAR(4) NULL
        );
    END
    """

    create_booking_table = """
    IF OBJECT_ID('camping.booking', 'U') IS NULL
    BEGIN
        CREATE TABLE camping.booking (
            booking_id INT IDENTITY(1,1) PRIMARY KEY,
            customer_id INT NULL FOREIGN KEY REFERENCES camping.customers(customer_id),
            booking_date DATE NOT NULL,
            arrival_date DATE NOT NULL,
            campground_id INT NOT NULL,
            campsite_size VARCHAR(10),
            num_campsites INT
        );
    END
    """

    create_summary_table = """
    IF OBJECT_ID('camping.summary', 'U') IS NULL
    BEGIN
        CREATE TABLE camping.summary (
            summary_id INT IDENTITY(1,1) PRIMARY KEY,
            campground_id INT NOT NULL,
            summary_date DATE NOT NULL,
            total_sales DECIMAL(10, 2) NOT NULL,
            total_bookings INT NOT NULL
        );
    END
    """

    try:
        cursor.execute(create_customers_table)
        cursor.execute(create_booking_table)
        cursor.execute(create_summary_table)
        logger.info("Tables created successfully.")
    except pyodbc.Error as e:
        logger.error(f"Error creating tables: {e}")

def execute_sql_file(cursor, file_path):
    """
    Executes an SQL script from a file.

    :param cursor: Cursor object for the SQL connection.
    :param file_path: Path to the .sql file to be executed.
    """
    try:
        with open(file_path, 'r') as file:
            sql_script = file.read()
        cursor.execute(sql_script)
        logger.info(f"SQL script {file_path} executed successfully.")
    except FileNotFoundError:
        logger.error(f"SQL file not found: {file_path}")
    except pyodbc.Error as e:
        logger.error(f"Error executing SQL script: {e}")

def setup_database():
    """
    Main function to set up the SQL database: create schema, tables, and load initial data.
    """
    conn = connect_to_sql()  # Establish connection to the local SQL database
    if conn:
        cursor = conn.cursor()
        try:
            create_schema_if_not_exists(cursor)  # Create schema if not exists
            create_tables(cursor)  # Create required tables
            conn.commit()  # Commit the changes to the database

            # Correct the path formatting using os.path.join and raw strings
            base_dir = os.path.dirname(os.path.abspath(__file__))
            create_schema_path = os.path.join(base_dir, "resources", "sql", "create_head_office.sql")
            load_data_path = os.path.join(base_dir, "resources", "sql", "Head Office - Load Data (1).sql")

            execute_sql_file(cursor, create_schema_path)
            execute_sql_file(cursor, load_data_path)
            conn.commit()  # Commit the changes after executing scripts

        except Exception as e:
            logger.error(f"An error occurred during database setup: {e}")
            conn.rollback()

        finally:
            cursor.close()  # Close the cursor
            conn.close()  # Close the database connection
            logger.info("Database setup completed and connection closed.")

if __name__ == "__main__":
    setup_database()
