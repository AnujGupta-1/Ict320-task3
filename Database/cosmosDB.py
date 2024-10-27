import uuid
import sys
import os
import base64
from datetime import datetime
from azure.cosmos import exceptions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from resources.db_config import get_cosmos_client  # Use Cosmos DB connection from db_config.py
from Utils.logger_config import logger
from models.booking import Booking
from tenacity import retry, wait_fixed, stop_after_attempt
# Function to connect to Cosmos DB (now using db_config.py)
def connect_to_cosmos(container_name):
    """
    The function `connect_to_cosmos` establishes a connection to a specific container in a Cosmos DB
    instance.
    
    :param container_name: The `connect_to_cosmos` function is designed to connect to a specific
    container within a Cosmos DB database. The `container_name` parameter is the name of the container
    that you want to connect to in the Cosmos DB database. This function first gets the Cosmos client,
    then the database client, and
    :return: The function `connect_to_cosmos` is returning the container client for the specified
    container name in the Cosmos DB.
    """
    client = get_cosmos_client()  # Get the client first
    database = client.get_database_client('CampsiteBookingsDB' )  # Then get the database
    container = database.get_container_client(container_name)  # Finally, get the container
    logger.info(f"Connected to Cosmos DB container '{container_name}' successfully.")
    return container


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
# Function to insert booking into Cosmos DB
def insert_booking_to_cosmos(container, booking_data):
    booking_id = booking_data.get('booking_id')
    if not booking_id:
        logger.error("Booking data is missing the 'booking_id'. Skipping insertion.")
        return False  # Indicate failure

    try:
        query = "SELECT * FROM c WHERE c.booking_id = @booking_id"
        parameters = [{"name": "@booking_id", "value": booking_id}]
        existing_booking = list(container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if existing_booking:
            logger.info(f"Booking with ID {booking_id} already exists in Cosmos DB. Skipping insertion.")
            return False  # Indicate that the booking was skipped
        else:
            booking_data['id'] = str(uuid.uuid4())  # Generate unique item ID
            container.create_item(booking_data)  # Insert new booking
            logger.info(f"Booking {booking_id} inserted into Cosmos DB successfully.")
            return True  # Indicate success
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"HTTP error while inserting booking {booking_id}: {e.status_code} {e.message}")
        return False  # Indicate failure
    except Exception as e:
        logger.error(f"Error inserting booking {booking_id}: {e}")
        return False  # Indicate failure

# Function to update booking in Cosmos DB
@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def update_booking_in_cosmos(container, booking_id, update_data):
    try:
        booking = container.read_item(item=booking_id, partition_key=booking_id)
        booking.update(update_data)
        container.replace_item(item=booking['id'], body=booking)
        logger.info(f"Booking with ID {booking_id} updated successfully in Cosmos DB.")
    except exceptions.CosmosResourceNotFoundError:
        logger.error(f"Booking with ID {booking_id} not found.")
    except Exception as e:
        logger.error(f"Error updating booking {booking_id}: {e}")

# Function to delete booking from Cosmos DB
@retry(wait=wait_fixed(2), stop=stop_after_attempt(3))
def delete_booking_from_cosmos(container, booking_id):
    try:
        container.delete_item(item=booking_id, partition_key=booking_id)
        logger.info(f"Booking with ID {booking_id} deleted successfully.")
    except exceptions.CosmosResourceNotFoundError:
        logger.error(f"Booking with ID {booking_id} not found.")
    except Exception as e:
        logger.error(f"Error deleting booking {booking_id}: {e}")

# Function to fetch bookings from Cosmos DB
def fetch_cosmos_bookings(container):
    try:
        query = "SELECT * FROM c"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        bookings = [Booking.from_dict(item) for item in items]  # Convert each dictionary to a Booking object
        logger.info(f"Fetched {len(bookings)} bookings.")
        return bookings  # Return the list of Booking objects instead of the original items
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error fetching bookings: {e}")
        return []


# Function to insert a PDF for booking
def upsert_booking_pdf_to_cosmos(container, pdf_path, booking_id, campground_id):
    """
    Upserts a PDF for a specific booking into Cosmos DB.

    :param container: The Cosmos DB container.
    :param pdf_path: The local path to the PDF file.
    :param booking_id: The ID of the booking.
    :param campground_id: The campground ID (partition key).
    """
    try:
        # Read the PDF file, convert it to base64 to make it JSON serializable
        with open(pdf_path, 'rb') as pdf_file:
            pdf_data = base64.b64encode(pdf_file.read()).decode('utf-8')  # Encode and convert to string

        # Create the PDF document for Cosmos DB
        pdf_document = {
            'id': str(booking_id),  # Unique identifier for the document
            'campground_id': campground_id,  # Partition key
            'pdf_data': pdf_data,  # Encoded PDF data
            'filename': os.path.basename(pdf_path)
        }

        # Perform the upsert operation in Cosmos DB
        container.upsert_item(pdf_document)
        logger.info(f"PDF {pdf_path} upserted successfully for booking {booking_id}.")
        return True

    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"HTTP error while upserting PDF for booking {booking_id}: {e.status_code} {e.message}")
        return False
    except Exception as e:
        logger.error(f"Error upserting PDF for booking {booking_id}: {e}")
        return False

def find_booking_by_id(booking_id, cosmos_client):
    """
    Retrieves a booking from Cosmos DB by its booking ID.

    :param booking_id: The ID of the booking to retrieve.
    :param cosmos_client: The Cosmos DB client connection.
    :return: The booking object if found, otherwise None.
    """
    try:
        # Connect to the Cosmos DB container for bookings
        container = connect_to_cosmos("Bookings")  

        # Define the query to find the booking by its ID
        query = "SELECT * FROM c WHERE c.booking_id = @booking_id"
        parameters = [{"name": "@booking_id", "value": booking_id}]
        
        # Execute the query
        items = list(container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))

        if items:
            logger.info(f"Booking with ID {booking_id} found.")
            return Booking.from_dict(items[0])  # Convert dictionary to Booking object
        else:
            logger.warning(f"No booking found with ID {booking_id}.")
            return None

    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error finding booking by ID {booking_id}: {e}")
        return None
