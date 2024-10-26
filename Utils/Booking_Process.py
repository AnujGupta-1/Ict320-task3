from datetime import timedelta
from Database.cosmosDB import insert_booking_to_cosmos
from models.campsite import allocate_campsite
from models.booking import create_booking_data, Booking
from Utils.confirm_booking import generate_confirmation
from Utils.logger_config import logger


def allocate_and_confirm_booking(booking, campsites, campground_id):
    """
    Allocates a campsite for the booking and generates a confirmation.

    :param booking: The Booking object to process.
    :param campsites: List of Campsite objects available for allocation.
    :param campground_id: The ID of the campground to assign to the booking.
    :return: The allocated campsite object if successful, None otherwise.
    """
    try:
        # Adjust the booking dates to start on Saturday
        adjusted_start_date = Booking.adjust_to_saturday(booking.arrival_date)
        adjusted_end_date = adjusted_start_date + timedelta(days=7)

        logger.info(f"Attempting to allocate Booking {booking.booking_id} from {adjusted_start_date} to {adjusted_end_date}.")

        # Allocate a campsite for the booking
        allocated_campsite = allocate_campsite(campsites, adjusted_start_date, adjusted_end_date, booking)

        if allocated_campsite:
            # Update booking with the allocated campsite information
            booking.campground_id = campground_id
            booking.update_campsite_info(allocated_campsite.site_number, allocated_campsite.rate_per_night)

            # Generate a confirmation PDF for the booking
            generate_confirmation(booking)
            logger.info(f"Booking {booking.booking_id} successfully allocated to Campsite {allocated_campsite.site_number}.")
            return allocated_campsite
        else:
            logger.warning(f"No available campsites for Booking {booking.booking_id}.")
            return None
    except Exception as e:
        logger.error(f"Error allocating or confirming Booking {booking.booking_id}: {e}")
        return None


def insert_booking_to_db(cosmos_conn, booking):
    """
    Inserts a booking record into Cosmos DB.

    :param cosmos_conn: Connection to Cosmos DB.
    :param booking: The Booking object to insert.
    """
    try:
        booking_data = create_booking_data(booking)
        insert_booking_to_cosmos(cosmos_conn, booking_data)
        logger.info(f"Booking {booking.booking_id} inserted into Cosmos DB successfully.")
    except Exception as e:
        logger.error(f"Error inserting Booking {booking.booking_id} into Cosmos DB: {e}")


def process_single_booking(booking, campsites, cosmos_conn, campground_id):
    """
    Processes a single booking by allocating a campsite, generating a confirmation, and inserting into Cosmos DB.

    :param booking: The Booking object to process.
    :param campsites: List of available Campsite objects.
    :param cosmos_conn: Connection to Cosmos DB.
    :param campground_id: The ID of the campground.
    """
    if not isinstance(booking, Booking):
        logger.error(f"Invalid booking type: {type(booking)}. Skipping.")
        return

    logger.info(f"Processing Booking {booking.booking_id}...")

    # Allocate a campsite and generate confirmation
    allocated_campsite = allocate_and_confirm_booking(booking, campsites, campground_id)

    if allocated_campsite:
        # Insert booking into Cosmos DB if allocation and confirmation were successful
        insert_booking_to_db(cosmos_conn, booking)
    else:
        logger.warning(f"Booking {booking.booking_id} could not be processed due to lack of availability.")


def process_bookings(bookings, campsites, cosmos_conn, campground_id):
    """
    Processes a list of bookings by allocating campsites, generating confirmations, and inserting into Cosmos DB.

    :param bookings: List of Booking objects.
    :param campsites: List of Campsite objects available for allocation.
    :param cosmos_conn: Connection to Cosmos DB.
    :param campground_id: The ID of the campground.
    """
    for booking in bookings:
        process_single_booking(booking, campsites, cosmos_conn, campground_id)
