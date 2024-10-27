from datetime import datetime
import logging
import sys
import os
from azure.cosmos import exceptions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Database.sqlDB import connect_to_sql
from Database.headOfficeDB import connect_to_head_office
from models.summary import Summary
from Utils.pdf_generator import PDFGenerator
from Database.cosmosDB import connect_to_cosmos, upsert_booking_pdf_to_cosmos
from Utils.logger_config import logger


def create_summary_object(bookings):
    """
    Creates a Summary object from the provided bookings.

    :param bookings: List of processed Booking objects.
    :return: A Summary object containing total sales and booking count.
    """
    total_sales = sum(booking.total_cost for booking in bookings if booking.campsite_id is not None)
    total_bookings = len([booking for booking in bookings if booking.campsite_id is not None])

    summary = Summary(
        campground_id=1159010,  # Your student ID as campground ID
        summary_date=datetime.now().date(),
        total_sales=total_sales,
        total_bookings=total_bookings
    )
    
    summary.validate()
    logger.info(f"Summary created and validated for {summary.summary_date}.")
    return summary




def process_summary(summary):
    """
    Processes the summary by inserting it into the databases, generating a PDF, and uploading it to Cosmos DB.

    :param summary: The Summary object containing the summary details.
    """
    try:
        # Insert summary into local and Head Office databases
        insert_summary_into_databases(summary)

        # Generate and save the summary PDF using the updated PDFGenerator
        pdf_gen = PDFGenerator("Daily Summary Report")
        pdf_path = pdf_gen.generate_summary(summary)

        # Upsert the summary PDF into Cosmos DB
        upload_summary_to_cosmos(pdf_path, summary)

        logger.info("Summary processing completed successfully.")
        print(f"Summary successfully created and processed for {summary.summary_date}.")
    except Exception as e:
        logger.error(f"Error during summary processing: {e}")
        print("An error occurred while processing the summary.")


def insert_summary_into_databases(summary):
    """
    Inserts the summary into both the local SQL and Head Office databases.

    :param summary: The Summary object to insert.
    """
    try:
        with connect_to_sql() as sql_conn:
            insert_summary_into_local(sql_conn, summary)
            logger.info("Summary inserted into the local SQL database.")

        with connect_to_head_office() as head_office_conn:
            insert_summary_into_head_office(head_office_conn, summary)
            logger.info("Summary inserted into the Head Office database.")
    except Exception as e:
        logger.error(f"Error inserting summary into databases: {e}")
        raise e


def insert_summary_into_local(conn, summary):
    """
    Inserts the summary into the local SQL database.

    :param conn: Connection to the local SQL database.
    :param summary: The Summary object to insert.
    """
    query = """
        INSERT INTO camping.summary (campground_id, summary_date, total_sales, total_bookings)
        VALUES (?, ?, ?, ?)
    """
    execute_db_query(conn, query, summary.to_dict())
    logger.info("Summary inserted into local SQL database.")


def insert_summary_into_head_office(conn, summary):
    """
    Inserts the summary into the Head Office SQL database.

    :param conn: Connection to the Head Office database.
    :param summary: The Summary object to insert.
    """
    query = """
        INSERT INTO camping.summary (campground_id, summary_date, total_sales, total_bookings)
        VALUES (?, ?, ?, ?)
    """
    execute_db_query(conn, query, summary.to_dict())
    logger.info("Summary inserted into Head Office database.")


def execute_db_query(conn, query, data):
    """
    Executes a query in the provided database connection.

    :param conn: Database connection.
    :param query: SQL query to execute.
    :param data: Dictionary containing summary details.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (
            data['campground_id'],
            data['summary_date'],
            data['total_sales'],
            data['total_bookings']
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Error executing database query: {e}")
        raise e


def upload_summary_to_cosmos(pdf_path, summary):
    """
    Uploads the summary PDF to Cosmos DB.

    :param pdf_path: Path to the generated summary PDF.
    :param summary: The Summary object containing the summary details.
    """
    try:
        # Ensure the PDF file exists before attempting the upload
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file does not exist: {pdf_path}")
            return False
        
        # Connect to the Cosmos DB container
        summary_container = connect_to_cosmos("PDFs")
        
        # Create the summary ID using campground_id and summary_date
        summary_id = f"{summary.campground_id}_{summary.summary_date.strftime('%Y-%m-%d')}"
        campground_id = summary.campground_id
        

        # Upsert the summary PDF using the partition key (campground_id)
        success = upsert_booking_pdf_to_cosmos(summary_container, pdf_path, summary_id, campground_id)
        
        if success:
            logger.info("Summary PDF upserted into Cosmos DB successfully.")
            return True
        else:
            logger.error("Failed to upsert summary PDF into Cosmos DB.")
            return False

    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"HTTP error while uploading summary PDF: {e.status_code} {e.message}")
        raise e
    except Exception as e:
        logger.error(f"Error uploading summary PDF to Cosmos DB: {e}")
        raise e


def generate_summary_report(bookings, campsites):
    """
    Generates a report summarizing booking allocations and campsite utilization.

    :param bookings: List of Booking objects.
    :param campsites: List of Campsite objects.
    :return: Dictionary containing summary data.
    """
    logger.info("Generating summary report from booking data.")

    # Calculate total sales (only for successfully allocated bookings)
    total_sales = sum(booking.total_cost for booking in bookings if booking.campsite_id is not None)

    # Count successful allocations (bookings with campsite_id) and failed allocations
    successful_allocations = len([b for b in bookings if b.campsite_id is not None])
    failed_allocations = len(bookings) - successful_allocations

    # Initialize campsite utilization dictionary
    campsite_utilization = {
        campsite.site_number: {
            'size': campsite.size,
            'rate_per_night': campsite.rate_per_night,
            'bookings_count': 0
        }
        for campsite in campsites
    }

    # Update campsite utilization based on bookings
    for booking in bookings:
        if booking.campsite_id is not None:  # Using dot notation
            if booking.campsite_id in campsite_utilization:
                campsite_utilization[booking.campsite_id]['bookings_count'] += 1


    # Prepare summary data to be returned
    summary_data = {
        'date': datetime.now().date(),
        'total_sales': total_sales,
        'total_bookings': len(bookings),
        'successful_allocations': successful_allocations,
        'failed_allocations': failed_allocations,
        'campsite_utilization': campsite_utilization
    }

    logger.info(f"Summary Data: {summary_data}")
    return summary_data
