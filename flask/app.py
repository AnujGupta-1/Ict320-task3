import os
import logging
import sys
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template, flash, redirect, url_for
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.booking import Booking
from Utils.logger_config import logger
from Utils.Booking_Process import process_bookings
from Utils.confirm_booking import generate_booking_confirmation
from Utils.manage_campsite import initialize_campsites
from Database.cosmosDB import connect_to_cosmos, fetch_cosmos_bookings, find_booking_by_id
from Utils.manage_summary import generate_summary_report, process_summary, create_summary_object, display_summary
from Utils.pdf_generator import PDFGenerator
from Database.headOfficeDB import connect_to_head_office, fetch_bookings

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize campsites once, as this data won't change between requests
campsites = initialize_campsites()
logger.info(f"Initialized {len(campsites)} campsites.")

# Set up the PDF directory
PDF_FOLDER = "pdfs"
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

processed_bookings = []

@app.route('/')
def home():
    return render_template('home.html')

# Route to process bookings from the Head Office SQL database and allocate campsites
@app.route('/process-bookings', methods=['POST'])
def handle_bookings():
    try:
        # Connect to the Head Office SQL database
        conn = connect_to_head_office()
        if not conn:
            return jsonify({"error": "Failed to connect to Head Office database"}), 500

        # Fetch bookings from the Head Office SQL database
        booking_data = fetch_bookings(conn)

        # Convert pyodbc.Row to Booking objects directly
        bookings = [Booking.from_db_record(record) for record in booking_data]

        # Process and allocate campsites
        process_bookings(bookings, campsites, cosmos_client, conn, 1159010)  # Example campground ID

        return jsonify({"message": "Bookings processed successfully"}), 200
    except Exception as e:
        logger.error(f"Error processing bookings: {e}")
        return jsonify({"error": str(e)}), 500

# Route to generate and download booking confirmation PDF
@app.route('/generate-confirmation/<int:booking_id>', methods=['GET'])
def generate_confirmation(booking_id):
    try:
        logger.info(f"Generating confirmation for booking {booking_id}.")

        # Find the booking by ID
        booking = find_booking_by_id(booking_id, cosmos_client)
        if not booking:
            logger.error(f"Booking {booking_id} not found.")
            return jsonify({"error": "Booking not found"}), 404

        # Generate booking confirmation PDF
        confirmation_pdf_path = generate_booking_confirmation(booking)

        # Serve the generated PDF
        return send_from_directory(directory=PDF_FOLDER, filename=os.path.basename(confirmation_pdf_path), as_attachment=True)
    except Exception as e:
        logger.error(f"Error generating confirmation for booking {booking_id}: {e}")
        return jsonify({"error": str(e)}), 500

# Route to view all bookings stored in Cosmos DB
@app.route('/view-bookings', methods=['GET'])
def view_bookings():
    try:
        logger.info("Fetching bookings from Cosmos DB.")

        # Fetch all bookings from Cosmos DB
        bookings = fetch_cosmos_bookings(cosmos_client)

        # Convert each booking object to a dictionary for JSON response
        booking_dicts = [booking.to_dict() for booking in bookings]
        return render_template('view_bookings.html', bookings = booking_dicts)
    except Exception as e:
        logger.error(f"Error fetching bookings: {e}")
        return jsonify({"error": str(e)}), 500

# Route to generate and process daily summary based on bookings
@app.route('/generate-summary', methods=['GET'])
def daily_summary():
    try:
        # Fetch bookings from Head Office SQL database
        conn = connect_to_head_office()
        cosmos_conn = connect_to_cosmos('Bookings')
        raw_bookings = fetch_bookings(conn)

        # Convert raw bookings to Booking objects
        bookings = [Booking.from_db_record(record) for record in raw_bookings]

        if bookings:
            # Process bookings
            process_bookings(bookings, campsites, cosmos_conn, conn, 1159010)  # Example campground ID

            # Create a summary object based on processed bookings
            summary = create_summary_object(bookings)

            # Process the summary (insert into DB, generate PDF, upload to Cosmos DB)
            process_summary(summary)

            # Generate and serve the summary PDF
            pdf_generator = PDFGenerator("Daily Summary Report")
            summary_pdf_path = pdf_generator.generate_summary(summary)

            # Return the generated summary PDF as a file download
            pdf_folder_abs = os.path.abspath(PDF_FOLDER)  # Ensure directory is absolute
            return send_from_directory(pdf_folder_abs, os.path.basename(summary_pdf_path), as_attachment=True)

        else:
            flash('No bookings available to generate summary.', 'warning')
            return redirect(url_for('list_summaries'))  # Redirect if no bookings found

    except Exception as e:
        logger.error(f"Error generating daily summary: {e}")
        flash(f"Error generating summary: {e}", 'danger')
        return redirect(url_for('list_summaries'))  # Redirect to the list summaries page on error


@app.route('/list-summaries', methods=['GET'])
def list_summaries():
    try:
        # List all available summary PDFs in the PDF folder
        summaries = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]
        return render_template('list_summaries.html', available_summaries=summaries)
    except Exception as e:
        logger.error(f"Error listing summaries: {e}")
        return jsonify({"error": "Failed to list summaries"}), 500
    
# Error handling route
@app.errorhandler(500)
def handle_internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "An internal server error occurred"}), 500

# Running the Flask app
if __name__ == '__main__':
    logger.setLevel(logging.INFO)
    cosmos_client = connect_to_cosmos("Bookings")  # Initialize Cosmos DB connection for storing processed bookings
    app.run(debug=True, host='0.0.0.0', port=5000)
