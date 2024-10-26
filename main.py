from datetime import datetime
import logging
from Database.sqlDB import connect_to_sql
from Database.headOfficeDB import connect_to_head_office, fetch_bookings
from Database.cosmosDB import connect_to_cosmos
from models.booking import Booking
from Utils.Booking_Process import process_bookings
from Utils.manage_campsite import initialize_campsites
from Utils.manage_summary import generate_summary_report, display_summary, create_summary_object, process_summary
from Utils.logger_config import logger



# Configure logging to display only INFO level and above
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger('azure.cosmos').setLevel(logging.WARNING)  # Suppress detailed Cosmos DB logs
logging.getLogger('urllib3').setLevel(logging.WARNING)       # Suppress urllib3 logs


def connect_to_databases():
    sql_conn, head_office_conn, cosmos_conn = None, None, None  # Initialize variables
    try:
        sql_conn = connect_to_sql()  # Try to connect to SQL
    except Exception as e:
        logger.error(f"Error connecting to SQL: {e}")

    try:
        head_office_conn = connect_to_head_office()  # Try to connect to Head Office
    except Exception as e:
        logger.error(f"Error connecting to Head Office: {e}")

    try:
        cosmos_conn = connect_to_cosmos("Bookings")  # Try to connect to Cosmos DB
    except Exception as e:
        logger.error(f"Error connecting to Cosmos DB: {e}")

    return sql_conn, head_office_conn, cosmos_conn


def fetch_and_prepare_bookings(head_office_conn):
    """
    Fetches raw booking records from Head Office and converts them into Booking objects.

    :param head_office_conn: Connection to the Head Office database.
    :return: List of Booking objects.
    """
    bookings = []
    raw_bookings = fetch_bookings(head_office_conn)

    for record in raw_bookings:
        try:
            booking = Booking.from_db_record(record)
            bookings.append(booking)
        except Exception as e:
            logger.error(f"Error processing booking record: {e}")

    logger.info(f"Fetched and processed {len(bookings)} bookings from Head Office.")
    return bookings


def process_all_bookings(bookings, campsites, head_office_conn, cosmos_conn):
    """
    Processes all bookings by allocating campsites and updating databases.

    :param bookings: List of Booking objects.
    :param campsites: List of Campsite objects.
    :param head_office_conn: Connection to the Head Office database.
    :param cosmos_conn: Connection to the Cosmos DB.
    """
    campground_id = 1121132  # Student ID as campground ID
    process_bookings(bookings, campsites, head_office_conn, cosmos_conn, campground_id)
    logger.info("Processed all bookings and allocated campsites.")


def process_and_display_summary(bookings, campsites):
    """
    Generates, displays, and processes the summary for the bookings and campsite utilization.

    :param bookings: List of Booking objects.
    :param campsites: List of Campsite objects.
    """
    try:
        # Step 1: Generate Summary
        summary_data = generate_summary_report(bookings, campsites)

        # Step 2: Display the generated summary
        display_summary(summary_data)

        # Step 3: Create the summary object for database insertion and Cosmos upload
        summary = create_summary_object(bookings)

        # Step 4: Insert into databases, generate PDF, and upload to Cosmos
        process_summary(summary)

    except Exception as e:
        logger.error(f"Error in processing the summary: {e}")
        raise e


def close_connections(sql_conn, head_office_conn, cosmos_conn):
    if sql_conn:
        sql_conn.close()
        logger.info("SQL connection closed.")
    if head_office_conn:
        head_office_conn.close()
        logger.info("Head Office connection closed.")
    if cosmos_conn:
        cosmos_conn.close()
        logger.info("Cosmos DB connection handled internally.")



def main_workflow():
    """
    Main workflow function that orchestrates database connections, booking processing,
    campsite initialization, summary generation, and final cleanup.
    """
    try:
        # Step 1: Connect to databases
        sql_conn, head_office_conn, cosmos_conn = connect_to_databases()

        # Step 2: Initialize campsites
        campsites = initialize_campsites()
        logger.info(f"Initialized {len(campsites)} campsites.")

        # Step 3: Fetch and prepare bookings
        bookings = fetch_and_prepare_bookings(head_office_conn)

        # Step 4: Process bookings and allocate campsites
        process_all_bookings(bookings, campsites, head_office_conn, cosmos_conn)

        # Step 5: Generate, display, and process the summary
        process_and_display_summary(bookings, campsites)

    except Exception as e:
        logger.error(f"An error occurred during the main workflow: {e}")
    finally:
        # Step 6: Close all connections
        close_connections(sql_conn, head_office_conn, cosmos_conn)


if __name__ == '__main__':
    # Set logger to INFO level to suppress DEBUG-level messages
    logger.setLevel(logging.INFO)
    main_workflow()
