from Utils.logger_config import logger
from resources.db_config import get_sql_connection
import pyodbc
import uuid


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
def fetch_bookings(conn, campground_id=1):
    """
    Fetches bookings from the head office camping.booking table and includes customer names.
    
    :param conn: The connection object to the SQL database.
    :param campground_id: The campground ID to filter bookings by.
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
            b.campground_id = ?;
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (campground_id,))
            rows = cursor.fetchall()
            logger.info(f"Fetched {len(rows)} bookings from the Head Office database for campground {campground_id}.")
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

def insert_booking_to_head_office(head_office_conn, booking_data):
    """
    Inserts a booking record into the Head Office database.

    :param head_office_conn: Connection to the Head Office database (using pyodbc).
    :param booking_data: The booking data to insert.
    :return: True if the booking was successfully inserted, False otherwise.
    """
    booking_id = booking_data.get('booking_id')
    if not booking_id:
        logger.error("Booking data is missing the 'booking_id'. Skipping insertion.")
        return False  # Indicate failure

    try:
        # Prepare a cursor for executing queries
        cursor = head_office_conn.cursor()

        # Check if the booking already exists in the Head Office database
        check_query = "SELECT COUNT(*) FROM camping.booking WHERE booking_id = ?"
        cursor.execute(check_query, (booking_id,))
        existing_booking_count = cursor.fetchone()[0]

        if existing_booking_count > 0:
            logger.info(f"Booking with ID {booking_id} already exists in Head Office database. Skipping insertion.")
            return False  # Indicate that the booking was skipped
        else:
            # Generate a new unique ID for the booking record
            new_id = str(uuid.uuid4())

            # Insert the booking into the Head Office database
            insert_query = """
                INSERT INTO camping.booking (id, booking_id, customer_name, arrival_date, departure_date, campsite_number, rate_per_night)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_query, (
                new_id,
                booking_data.get('booking_id'),
                booking_data.get('customer_name'),
                booking_data.get('arrival_date'),
                booking_data.get('departure_date'),
                booking_data.get('campsite_number'),
                booking_data.get('rate_per_night')
            ))

            # Commit the transaction to save changes
            head_office_conn.commit()

            logger.info(f"Booking {booking_id} inserted into Head Office database successfully.")
            return True  # Indicate success

    except pyodbc.DatabaseError as e:
        logger.error(f"Database error while inserting booking {booking_id} into Head Office database: {str(e)}")
        return False  # Indicate failure
    except Exception as e:
        logger.error(f"Error inserting booking {booking_id} into Head Office database: {str(e)}")
        return False  # Indicate failure
    finally:
        cursor.close()  # Ensure the cursor is closed after use
