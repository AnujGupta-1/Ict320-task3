from datetime import datetime, date
from Utils.logger_config import logger

class Summary:
    def __init__(self, campground_id, summary_date, total_sales, total_bookings):
        """
        Initializes a Summary object.

        :param campground_id: ID of the campground.
        :param summary_date: Date of the summary.
        :param total_sales: Total sales amount for the summary period.
        :param total_bookings: Total number of bookings for the summary period.
        """
        self.campground_id = campground_id
        self.summary_date = self._validate_date(summary_date)  # Ensure date is validated
        self.total_sales = total_sales
        self.total_bookings = total_bookings

    def _validate_date(self, date_input):
        """
        Validates and converts input to a datetime object.

        :param date_input: Input date which can be a datetime, date, or string.
        :return: Validated datetime object.
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
                logger.error(f"Invalid date format: {date_input}. Expected format is 'YYYY-MM-DD'.")
                raise ValueError(f"Invalid date format for {date_input}. Expected 'YYYY-MM-DD'.")
        else:
            logger.error(f"Unsupported date input type: {type(date_input)}")
            raise TypeError(f"Unsupported date input type: {type(date_input)}")

    def to_dict(self):
        """
        Converts the Summary object into a dictionary format.

        :return: Dictionary containing summary details.
        """
        return {
            "campground_id": self.campground_id,
            "summary_date": self.summary_date.strftime('%Y-%m-%d'),  # Format date as string
            "total_sales": self.total_sales,
            "total_bookings": self.total_bookings
        }

    def validate(self):
        """
        Validates the Summary object data to ensure it meets expected constraints.

        :raises ValueError: If any required fields are empty or if any values are negative.
        """
        # Check if campground_id and summary_date are not empty
        if not self.campground_id:
            logger.error("Validation Error: Campground ID must not be empty.")
            raise ValueError("Campground ID must not be empty.")
        
        if not self.summary_date:
            logger.error("Validation Error: Summary date must not be empty.")
            raise ValueError("Summary date must not be empty.")
        
        # Ensure total sales and bookings are non-negative
        if self.total_sales < 0:
            logger.error("Validation Error: Total sales cannot be negative.")
            raise ValueError("Total sales cannot be negative.")
        
        if self.total_bookings < 0:
            logger.error("Validation Error: Total bookings cannot be negative.")
            raise ValueError("Total bookings cannot be negative.")
        
        logger.info(f"Summary for Campground {self.campground_id} on {self.summary_date.strftime('%Y-%m-%d')} is valid.")

    @staticmethod
    def from_dict(data):
        """
        Creates a Summary object from a dictionary.

        :param data: Dictionary containing summary data.
        :return: Summary object.
        """
        return Summary(
            campground_id=data.get('campground_id'),
            summary_date=data.get('summary_date'),
            total_sales=data.get('total_sales', 0),
            total_bookings=data.get('total_bookings', 0)
        )

