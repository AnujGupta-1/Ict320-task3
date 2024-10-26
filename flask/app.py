import sys
import os
import logging
import io
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from models.booking import Booking
from Utils.Booking_Process import process_bookings
from Database.sqlDB import connect_to_sql
from Database.cosmosDB import connect_to_cosmos, fetch_cosmos_bookings
from Utils.manage_summary import display_summary, generate_summary_pdf, create_summary_object,insert_summary_into_local, insert_summary_into_head_office, insert_summary_into_databases
from Utils.manage_campsite import initialize_campsites
from Database.headOfficeDB import connect_to_head_office, fetch_bookings
from Utils.logger_config import logger

# Flask app initialization
app = Flask(__name__)
app.secret_key = 'supersecret'

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Global variable for processed bookings
processed_bookings = []

# Route: Home Page
@app.route('/')
def index():
    """
    Displays the home page with bookings from Cosmos DB.
    """
    try:
        cosmos_conn = connect_to_cosmos("Bookings")
        bookings = fetch_cosmos_bookings(cosmos_conn)
        if bookings:
            logger.info(f"Fetched {len(bookings)} bookings from Cosmos DB.")
        else:
            flash('No bookings available.', 'info')
        return render_template('index.html', bookings=bookings)
    except Exception as e:
        logger.error(f"Error loading index: {str(e)}")
        flash(f'Error loading index: {str(e)}', 'danger')
        return redirect(url_for('index'))

# Route: Process Bookings
@app.route('/process_bookings', methods=['POST'])
def process_bookings_route():
    """
    Processes bookings from the Head Office DB, allocates campsites, and updates Cosmos DB.
    """
    global processed_bookings
    try:
        sql_conn = connect_to_sql()
        head_office_conn = connect_to_head_office()
        cosmos_conn = connect_to_cosmos("Bookings")

        raw_bookings = fetch_bookings(head_office_conn)
        bookings = [Booking.from_db_record(record) for record in raw_bookings]
        campsites = initialize_campsites()

        # Process bookings and update Cosmos DB
        process_bookings(bookings, campsites, head_office_conn, cosmos_conn, campground_id=1121132)
        processed_bookings = bookings
        flash('Bookings processed successfully!', 'success')
        return redirect(url_for('summary'))
    except Exception as e:
        logger.error(f"Error processing bookings: {str(e)}")
        flash(f'Error processing bookings: {str(e)}', 'danger')
        return redirect(url_for('index'))

# Route: View Bookings
@app.route('/bookings')
def view_bookings():
    """
    Displays the list of bookings from Cosmos DB.
    """
    try:
        cosmos_conn = connect_to_cosmos("Bookings")
        bookings = fetch_cosmos_bookings(cosmos_conn)
        if bookings:
            logger.info(f"Fetched {len(bookings)} bookings from Cosmos DB.")
        return render_template('bookings_list.html', bookings=bookings)
    except Exception as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        flash(f'Error fetching bookings: {str(e)}', 'danger')
        return redirect(url_for('index'))

# Route: Summary
@app.route('/summary')
def summary():
    """
    Displays the summary of the processed bookings.
    """
    global processed_bookings
    try:
        # If no processed bookings, fetch from Cosmos DB
        if not processed_bookings:
            bookings = fetch_cosmos_bookings(connect_to_cosmos("Bookings"))
        else:
            bookings = processed_bookings

        if not bookings:
            flash('No bookings available. Please process the bookings first.', 'warning')
            return redirect(url_for('index'))

        campsites = initialize_campsites()
        summary_data = generate_summary_pdf(bookings, campsites)
        display_summary(summary_data)
        create_summary_object(bookings)
        insert_summary_into_local(bookings)
        insert_summary_into_databases(bookings)
        insert_summary_into_head_office(bookings)

        flash('Summary generated and stored successfully!', 'success')
        return render_template('summary.html', summary=summary_data)
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        flash(f"Error generating summary: {str(e)}", 'danger')
        return redirect(url_for('index'))

# Route: Show PDF Confirmation
@app.route('/pdf/<int:booking_id>')
def show_pdf(booking_id):
    """
    Fetches and displays a PDF confirmation for a specific booking.
    """
    try:
        pdf_data = fetch_pdf_from_cosmos(booking_id)
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            download_name=f'confirmation_{booking_id}.pdf'
        )
    except Exception as e:
        logger.error(f"Error fetching PDF for Booking ID {booking_id}: {str(e)}")
        flash(f'Error fetching PDF for Booking ID {booking_id}: {str(e)}', 'danger')
        return redirect(url_for('view_bookings'))

# Function: Fetch PDF from Cosmos DB
def fetch_pdf_from_cosmos(booking_id):
    """
    Fetches the PDF data associated with a booking from Cosmos DB.
    """
    try:
        cosmos_conn_bookings = connect_to_cosmos("Bookings")
        cosmos_conn_pdfs = connect_to_cosmos("PDFs")

        # Query to fetch the booking and associated PDF ID
        query_booking = f"SELECT * FROM c WHERE c.booking_id = {booking_id}"
        booking_items = list(cosmos_conn_bookings.query_items(query=query_booking, enable_cross_partition_query=True))

        if not booking_items:
            raise ValueError(f"Booking not found for booking ID {booking_id}")

        booking = booking_items[0]
        pdf_id = booking.get('pdf_id')

        if not pdf_id:
            raise ValueError(f"No PDF ID found for booking ID {booking_id}")

        # Query to fetch the PDF data
        query_pdf = f"SELECT * FROM c WHERE c.pdf_id = '{pdf_id}'"
        pdf_items = list(cosmos_conn_pdfs.query_items(query=query_pdf, partition_key=pdf_id, enable_cross_partition_query=True))

        if not pdf_items:
            raise ValueError(f"PDF not found for PDF ID {pdf_id}")

        pdf_data = pdf_items[0].get('pdf_data')

        if isinstance(pdf_data, str):
            import base64
            pdf_data = base64.b64decode(pdf_data)

        return pdf_data
    except Exception as e:
        logger.error(f"Failed to fetch PDF data from Cosmos DB: {e}")
        raise

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
