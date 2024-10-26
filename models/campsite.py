from datetime import datetime, timedelta
from Utils.logger_config import logger 

class Campsite:
    def __init__(self, site_number, size, rate_per_night):
        """
        Initializes a Campsite object.

        :param site_number: The number of the campsite.
        :param size: The size category of the campsite (e.g., 'Small', 'Medium', 'Large').
        :param rate_per_night: The rate per night for the campsite.
        """
        self.site_number = site_number
        self.size = size
        self.rate_per_night = rate_per_night
        self.bookings = []  # List of booked periods as tuples (start_date, end_date)

    def is_available(self, start_date, end_date):
        """
        Checks if the campsite is available for the given date range.

        :param start_date: Start date of the booking.
        :param end_date: End date of the booking.
        :return: True if the campsite is available, False otherwise.
        """
        for existing_start, existing_end in self.bookings:
            # Check if the new booking overlaps with any existing booking
            if start_date < existing_end and end_date > existing_start:
                return False  # Overlap detected, campsite is not available
        return True  # No overlap, campsite is available

    def book_campsite(self, start_date, end_date):
        """
        Books the campsite for the given date range if available.

        :param start_date: Start date of the booking.
        :param end_date: End date of the booking.
        :return: True if booking is successful, False otherwise.
        """
        if self.is_available(start_date, end_date):
            self.bookings.append((start_date, end_date))  # Add the full booking period
            logger.info(f"Campsite {self.site_number} successfully booked from {start_date.date()} to {end_date.date()}.")
            return True
        logger.warning(f"Campsite {self.site_number} is not available from {start_date.date()} to {end_date.date()}.")
        return False  # Booking failed because the campsite is not available

def allocate_campsite(campsites, start_date, end_date, booking):
    """
    Allocates a campsite based on the availability between the start and end dates.

    :param campsites: List of Campsite objects.
    :param start_date: Start date of the booking.
    :param end_date: End date of the booking.
    :param booking: Booking object containing booking details.
    :return: The allocated campsite object or None if no campsite is available.
    """
    logger.info(f"Attempting to allocate Booking {booking.booking_id} from {start_date.date()} to {end_date.date()}...")
    
    for campsite in campsites:
        if campsite.is_available(start_date, end_date):
            # Try to book the campsite
            if campsite.book_campsite(start_date, end_date):
                logger.info(f"Booking {booking.booking_id} successfully allocated to Campsite {campsite.site_number} ({campsite.size}).")
                booking.campsite_allocated = campsite.site_number  # Assign campsite to booking
                return campsite
    logger.warning(f"No available campsites for Booking {booking.booking_id} from {start_date.date()} to {end_date.date()}.")
    return None  # Return None if no campsites are available
