from Utils.logger_config import logger
from resources.db_config import get_sql_connection
import pyodbc


# Function to connect to the Head Office SQL database
def connect_to_head_office():
    """
    Connects to the Head Office SQL database using the get_sql_connection function from db_config.py.

    :return: Connection object to the Head Office SQL database or None if connection fails.
    """
    try:
        conn = get_sql_connection()  # Get the connection from db_config
        logger.info("Connected to Head Office SQL database successfully.")
        return conn

    except pyodbc.InterfaceError as ie:
        logger.error(f"Interface error connecting to Head Office SQL database: {ie}")
        return None

    except pyodbc.DatabaseError as de:
        logger.error(f"Database error connecting to Head Office SQL database: {de}")
        return None

    except Exception as ex:
        logger.error(f"An unexpected error occurred while connecting to Head Office SQL database: {ex}")
        return None


# Function to fetch bookings from the Head Office SQL database
def fetch_bookings(conn):
    """
    Fetches bookings from the head office camping.booking table and includes customer names.

    :param conn: The connection object to the SQL database.
    :return: A list of booking records or an empty list if an error occurs.
    """
    query = """
        SELECT 
            b.booking_id, 
            b.customer_id, 
            b.booking_date, 
            b.arrival_date, 
            b.campground_id, 
            b.campsite_size, 
            b.num_campsites, 
            CONCAT(c.first_name, ' ', c.last_name) AS customer_name
        FROM 
            camping.booking b
        JOIN 
            camping.customers c ON b.customer_id = c.customer_id
        WHERE 
            b.campground_id = 1;
    """

    try:
        # Using a context manager ensures the cursor is properly closed after use
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info(f"Fetched {len(rows)} bookings from the Head Office database.")
            return rows

    except pyodbc.DatabaseError as de:
        logger.error(f"Database error fetching bookings from Head Office SQL database: {de}")
        return []

    except Exception as ex:
        logger.error(f"An unexpected error occurred while fetching bookings: {ex}")
        return []


# Function to update the campground_id of a specific booking in the camping.booking table
def update_booking_campground(conn, booking_id, new_campground_id):
    """
    Updates the campground_id of a specific booking in the camping.booking table.

    :param conn: The connection object to the SQL database.
    :param booking_id: The ID of the booking to be updated.
    :param new_campground_id: The new campground ID to be set.
    :return: True if update is successful, False otherwise.
    """
    query = "UPDATE camping.booking SET campground_id = ? WHERE booking_id = ?"

    try:
        # Using a context manager ensures the cursor is properly closed after use
        with conn.cursor() as cursor:
            cursor.execute(query, (new_campground_id, booking_id))
            conn.commit()
            logger.info(f"Booking {booking_id} updated with new campground ID {new_campground_id} successfully.")
            return True

    except pyodbc.DatabaseError as de:
        logger.error(f"Database error updating booking {booking_id} in Head Office SQL database: {de}")
        return False

    except Exception as ex:
        logger.error(f"An unexpected error occurred while updating booking {booking_id}: {ex}")
        return False
