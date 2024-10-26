from datetime import datetime, timedelta, date
from models.campsite import allocate_campsite
from Utils.logger_config import logger


class Booking:
    def __init__(self, booking_id, customer_id, booking_date, arrival_date, campsite_size, num_campsites, campground_id=None, customer_name=None):
        """
        Initializes a Booking object with relevant details.

        :param booking_id: Unique identifier for the booking.
        :param customer_id: Unique identifier for the customer.
        :param booking_date: Date when the booking was made.
        :param arrival_date: Date when the customer will arrive.
        :param campsite_size: Size category of the campsite (e.g., 'Small', 'Medium', 'Large').
        :param num_campsites: Number of campsites booked.
        :param campground_id: Identifier of the campground (optional).
        :param customer_name: Name of the customer (optional).
        """
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.booking_date = self._validate_date(booking_date)
        self.arrival_date = self._validate_date(arrival_date)
        self.campsite_size = campsite_size
        self.num_campsites = num_campsites
        self.campground_id = campground_id
        self.campsite_id = None  # Initially set campsite_id to None until allocated
        self.total_cost = 0  # Default total cost set to zero
        self.customer_name = customer_name

    def __repr__(self):
        """Provides a string representation of the Booking object."""
        return f"<Booking {self.booking_id} - Customer {self.customer_id}>"

    def _validate_date(self, date_input):
        """
        Validates and converts input to a datetime object.

        :param date_input: Input date which can be a datetime, date, or string.
        :return: datetime object.
        :raises ValueError: If the date format is incorrect.
        :raises TypeError: If the input type is unsupported.
        """
        if isinstance(date_input, datetime):
            return date_input
        elif isinstance(date_input, date):
            return datetime.combine(date_input, datetime.min.time())
        elif isinstance(date_input, str):
            try:
                return datetime.strptime(date_input, '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Invalid date format for {date_input}. Expected 'YYYY-MM-DD'.")
        else:
            raise TypeError(f"Unsupported date input type: {type(date_input)}")

    def is_arrival_today(self):
        """
        Checks if the arrival date is today.

        :return: True if the arrival date is today, False otherwise.
        """
        return self.arrival_date.date() == datetime.now().date()

    def update_campsite_info(self, campsite_id, rate_per_night):
        """
        Updates campsite information and calculates the total cost.

        :param campsite_id: The campsite ID allocated.
        :param rate_per_night: The nightly rate for the campsite.
        """
        self.campsite_id = campsite_id
        self.total_cost = rate_per_night * 7 * self.num_campsites  # Calculate cost based on the 7-day booking duration

    def to_dict(self):
        """
        Converts the booking object to a dictionary format.

        :return: Dictionary representation of the booking object.
        """
        return {
            "booking_id": self.booking_id,
            "customer_id": self.customer_id,
            "booking_date": self.booking_date.strftime('%Y-%m-%d'),
            "arrival_date": self.arrival_date.strftime('%Y-%m-%d'),
            "campsite_size": self.campsite_size,
            "num_campsites": self.num_campsites,
            "campground_id": self.campground_id,
            "campsite_id": self.campsite_id,
            "total_cost": self.total_cost,
            "customer_name": self.customer_name
        }

    def from_db_record(record):
        """
        Creates a Booking object from a database record (pyodbc.Row).
        """
        record_dict = dict(zip([column[0] for column in record.cursor_description], record))
        return Booking(
            booking_id=record_dict['booking_id'],
            customer_id=record_dict['customer_id'],
            booking_date=record_dict['booking_date'],
            arrival_date=record_dict['arrival_date'],
            campsite_size=record_dict['campsite_size'],
            num_campsites=record_dict['num_campsites'],
            campground_id=record_dict.get('campground_id'),
            customer_name=record_dict.get('customer_name')
        )

    
    @staticmethod
    def adjust_to_saturday(start_date):
        """
        Adjusts a given date to the nearest Saturday.

        :param start_date: The start date to adjust.
        :return: Adjusted date on Saturday.
        """
        days_to_saturday = (5 - start_date.weekday() + 7) % 7  # Calculate days to next Saturday
        return start_date if days_to_saturday == 0 else start_date + timedelta(days=days_to_saturday)

    def allocate_campsite(self, campsites, head_office_conn, update_booking_campground_func):
        """
        Attempts to allocate a campsite for the booking.

        :param campsites: List of available campsites.
        :param head_office_conn: Connection to the head office database.
        :param update_booking_campground_func: Function to update the campground in the database.
        :return: Allocated campsite object or None.
        """
        # Adjust booking dates to start and end on a Saturday
        adjusted_start_date = Booking.adjust_to_saturday(self.arrival_date)
        adjusted_end_date = adjusted_start_date + timedelta(days=7)

        # Attempt to allocate a campsite
        allocated_campsite = allocate_campsite(campsites, adjusted_start_date, adjusted_end_date, self)
        if allocated_campsite:
            # Update campsite info and log the successful allocation
            self.update_campsite_info(allocated_campsite.site_number, allocated_campsite.rate_per_night)
            update_booking_campground_func(head_office_conn, self.booking_id, self.campground_id)
            logger.info(f"Booking {self.booking_id} successfully allocated to Campsite {allocated_campsite.site_number}.")
        else:
            # Log if no campsite is available
            logger.warning(f"No available campsites for Booking {self.booking_id} from {adjusted_start_date} to {adjusted_end_date}.")
        return allocated_campsite

    @staticmethod
    def from_dict(data):
        """
        Creates a Booking object from a dictionary.

        :param data: Dictionary containing booking data.
        :return: Booking object.
        """
        return Booking(
            booking_id=data['booking_id'],
            customer_id=data['customer_id'],
            booking_date=data['booking_date'],
            arrival_date=data['arrival_date'],
            campsite_size=data['campsite_size'],
            num_campsites=data['num_campsites'],
            campground_id=data.get('campground_id', None),
            customer_name=data.get('customer_name', None)
        ).set_total_cost(data.get('total_cost', 0))

    def set_total_cost(self, total_cost):
        """
        Sets the total cost for the booking.

        :param total_cost: The total cost value to be set.
        :return: Self for chaining.
        """
        self.total_cost = total_cost
        return self


def create_booking_data(booking):
    """
    Prepares booking data to be stored in Cosmos DB.

    :param booking: The Booking object.
    :return: Dictionary of booking data.
    """
    booking_data = booking.to_dict()
    booking_data["confirmation"] = f"confirmation_{booking.booking_id}.pdf"  # Reference the confirmation PDF
    booking_data["customer_name"] = booking.customer_name  # Ensure customer_name is included correctly
    
    return booking_data
