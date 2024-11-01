from datetime import datetime
import logging
from Database.sqlDB import connect_to_sql
from Database.headOfficeDB import connect_to_head_office, fetch_bookings
from Database.cosmosDB import connect_to_cosmos
from models.booking import Booking
from Utils.Booking_Process import process_bookings
from Utils.manage_campsite import initialize_campsites
from Utils.manage_summary import *
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


def process_all_bookings(bookings, campsites, cosmos_conn,head_office_conn, campground_id):
    """
    Processes all bookings by allocating campsites and updating databases.

    :param bookings: List of Booking objects.
    :param campsites: List of Campsite objects.
    :param head_office_conn: Connection to the Head Office database.
    :param cosmos_conn: Connection to the Cosmos DB.
    """
    campground_id = 1159010  # Student ID as campground ID
    process_bookings(bookings, campsites, cosmos_conn, head_office_conn, campground_id)
    logger.info("Processed all bookings and allocated campsites.")


def process_and_display_summary(bookings, campsites):
    """
    Generates and processes the summary for the bookings and campsite utilization.

    :param bookings: List of Booking objects.
    :param campsites: List of Campsite objects.
    """
    try:
        # Step 1: Generate Summary Data (booking allocations and campsite utilization)
        summary_data = generate_summary_report(bookings, campsites)

        # Step 2: Create the Summary object for further processing (database insertion, PDF generation)
        summary = create_summary_object(bookings)

        # Step 3: Process the summary, including database insertion and PDF generation
        process_summary(summary)

        # Step 4: Generate and save the summary PDF using the PDFGenerator
        pdf_gen = PDFGenerator("Daily Summary Report")
        pdf_path = pdf_gen.generate_summary(summary)
        logger.info(f"Summary PDF generated and saved at {pdf_path}")

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
        campground_id = 1159010
        process_all_bookings(bookings, campsites, cosmos_conn, head_office_conn, campground_id)

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
