from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import sys 
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Database.cosmosDB import connect_to_cosmos
from models.booking import Booking
from models.campsite import Campsite
from Utils.Booking_Process import allocate_and_confirm_booking
from Utils.confirm_booking import generate_booking_confirmation
from Utils.logger_config import logger
from Utils.manage_campsite import initialize_campsites
from Utils.manage_summary import create_summary_object, process_summary, generate_summary_report
from azure.cosmos import exceptions

app = Flask(__name__)

# Initialize campsites (assuming enough campsites are available)
campsites = initialize_campsites()

# Cosmos DB connection
container_name = 'your_container_name'  # Replace with actual container name
cosmos_container = connect_to_cosmos(container_name)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/booking', methods=['POST'])
def booking():
    try:
        # Capture form data
        booking_data = {
            "booking_id": request.form['booking_id'],
            "customer_id": request.form['customer_id'],
            "booking_date": request.form['booking_date'],
            "arrival_date": request.form['arrival_date'],
            "campsite_size": request.form['campsite_size'],
            "num_campsites": request.form['num_campsites'],
            "campground_id": request.form['campground_id'],
            "customer_name": request.form['customer_name'],
        }

        # Create Booking object
        booking = Booking(**booking_data)

        # Allocate campsite and generate confirmation
        allocated_campsite = allocate_and_confirm_booking(booking, campsites, booking_data["campground_id"])
        
        if allocated_campsite:
            # Insert booking into Cosmos DB (if it doesn't already exist)
            booking_id = booking_data["booking_id"]
            query = "SELECT * FROM c WHERE c.booking_id = @booking_id"
            parameters = [{"name": "@booking_id", "value": booking_id}]
            existing_booking = list(cosmos_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

            if existing_booking:
                return render_template('error.html', error="Booking already exists.")
            else:
                booking_data['id'] = str(uuid.uuid4())  # Generate unique item ID
                cosmos_container.create_item(booking_data)  # Insert new booking
                logger.info(f"Booking {booking_id} inserted into Cosmos DB successfully.")

            # Generate confirmation PDF and send it to the user
            confirmation_file = generate_booking_confirmation(booking, allocated_campsite)
            return send_file(confirmation_file, as_attachment=True)
        else:
            return render_template('failure.html', data=booking_data)

    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/showData')
def showData():
    try:
        # Retrieve all bookings from Cosmos DB
        query = "SELECT * FROM c"
        bookings = list(cosmos_container.query_items(query=query, enable_cross_partition_query=True))
        return render_template("showData.html", bookings=bookings)
    except exceptions.CosmosHttpResponseError as e:
        return render_template('error.html', error=str(e))

@app.route('/manage_campsites', methods=['GET', 'POST'])
def manage_campsites():
    if request.method == 'POST':
        try:
            # Add a new campsite from form input
            site_number = int(request.form['site_number'])
            size = request.form['size']
            rate_per_night = float(request.form['rate_per_night'])

            # Check if the campsite already exists
            if any(campsite.site_number == site_number for campsite in campsites):
                raise ValueError(f"Campsite {site_number} already exists.")

            # Create and add new campsite
            new_campsite = Campsite(site_number=site_number, size=size, rate_per_night=rate_per_night)
            campsites.append(new_campsite)
            logger.info(f"Added new campsite {site_number} successfully.")
            
            return redirect(url_for('manage_campsites'))
        except Exception as e:
            return render_template('error.html', error=str(e))

    # GET request: Show the current campsites
    return render_template('manage_campsites.html', campsites=campsites)

@app.route('/remove_campsite', methods=['POST'])
def remove_campsite_route():
    try:
        site_number = int(request.form['site_number'])
        global campsites
        
        # Find and remove the campsite
        campsites = [campsite for campsite in campsites if campsite.site_number != site_number]
        logger.info(f"Campsite {site_number} removed successfully.")
        
        return redirect(url_for('manage_campsites'))
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/summary', methods=['GET'])
def summary():
    try:
        # Retrieve all bookings from Cosmos DB
        query = "SELECT * FROM c"
        bookings = list(cosmos_container.query_items(query=query, enable_cross_partition_query=True))

        # Generate summary object
        summary = create_summary_object(bookings)

        # Process summary (insert into databases, generate PDF, etc.)
        process_summary(summary)

        # Generate summary data for displaying
        summary_data = generate_summary_report(bookings, campsites)
        return render_template('summary.html', summary=summary_data)

    except Exception as e:
        return render_template('error.html', error=str(e))

# 404 error handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    if os.environ.get('FLASK_RUN_FROM_CLI') != 'true':  # Check if Flask is not running from CLI to avoid duplicate messages
        host = '127.0.0.1'
        port = 5000
        print(f"Flask app is running! Access it at http://{host}:{port}/")
    app.run(debug=True)