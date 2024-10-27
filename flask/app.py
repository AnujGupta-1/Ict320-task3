
import os
import sys
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.booking import Booking
from Utils.logger_config import logger
from Utils.Booking_Process import process_bookings
from Utils.confirm_booking import generate_booking_confirmation
from Utils.manage_campsite import initialize_campsites
from Database.cosmosDB import connect_to_cosmos, fetch_cosmos_bookings, find_booking_by_id
from Utils.manage_summary import generate_summary_report, process_summary
from Utils.pdf_generator import PDFGenerator
from Database.headOfficeDB import connect_to_head_office, fetch_bookings
# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize Cosmos DB client for storing processed bookings
cosmos_client = connect_to_cosmos("Bookings")

# Initialize campsites
campsites = initialize_campsites()

# Set up the PDF directory
PDF_FOLDER = "pdfs"
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

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
        
        # Process and allocate campsites
        process_bookings(booking_data, campsites, cosmos_client, 1159010)  # Example campground ID
        
        return jsonify({"message": "Bookings processed successfully"}), 200
    except Exception as e:
        logger.error(f"Error processing bookings: {e}")
        return jsonify({"error": str(e)}), 500

# Route to generate and download booking confirmation PDF
@app.route('/generate-confirmation/<int:booking_id>', methods=['GET'])
def generate_confirmation(booking_id):
    try:
        # Find the booking by ID
        booking = find_booking_by_id(booking_id, cosmos_client)
        if not booking:
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
        # Fetch all bookings from Cosmos DB
        bookings = fetch_cosmos_bookings(cosmos_client)
        # Convert each booking object to a dictionary
        booking_dicts = [booking.to_dict() for booking in bookings]
        return jsonify(booking_dicts), 200
    except Exception as e:
        logger.error(f"Error fetching bookings: {e}")
        return jsonify({"error": str(e)}), 500

# Route to generate and download daily summary report
@app.route('/generate-summary', methods=['GET'])
def daily_summary():
    try:
        # Fetch bookings from Cosmos DB
        bookings = fetch_cosmos_bookings(cosmos_client)
        
        # Debug: Log the raw bookings fetched from Cosmos DB
        logger.debug(f"Fetched bookings from Cosmos DB: {bookings}")

        # Convert fetched bookings to Booking objects
        booking_objects = [Booking.from_dict(b) for b in bookings]
        
        # Debug: Log the converted Booking objects
        logger.debug(f"Converted Booking objects: {booking_objects}")

        # Generate the summary report using Booking objects and campsites
        summary_data = generate_summary_report(booking_objects, campsites)

        # Debug: Log the summary data
        logger.debug(f"Generated summary data: {summary_data}")

        # Generate PDF for the summary
        pdf_generator = PDFGenerator("Daily Summary Report")
        summary_pdf_path = pdf_generator.generate_summary(summary_data)

        # Process and store the summary
        process_summary(summary_data)

        # Serve the generated PDF
        return send_from_directory(directory=PDF_FOLDER, filename=os.path.basename(summary_pdf_path), as_attachment=True)
    except Exception as e:
        logger.error(f"Error generating daily summary: {e}")
        return jsonify({"error": str(e)}), 500

# Error handling route
@app.errorhandler(500)
def handle_internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "An internal server error occurred"}), 500

# Running the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)