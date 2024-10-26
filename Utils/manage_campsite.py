from models.campsite import Campsite
from Utils.logger_config import logger

def create_campsites(start, end, size, rate_per_night):
    """
    Creates a list of Campsite objects for a given range of site numbers, size, and rate.

    :param start: Starting number for campsite IDs.
    :param end: Ending number for campsite IDs.
    :param size: Size of the campsites (e.g., 'Small', 'Medium', 'Large').
    :param rate_per_night: Rate per night for the campsites.
    :return: A list of Campsite objects for the given range.
    """
    return [Campsite(site_number=i, size=size, rate_per_night=rate_per_night) for i in range(start, end + 1)]

def initialize_campsites():
    """
    Initializes a list of campsites with predefined sizes and rates.

    :return: A list of Campsite objects.
    """
    # Create campsites for different size categories
    small_campsites = create_campsites(start=1, end=10, size='Small', rate_per_night=50)
    medium_campsites = create_campsites(start=11, end=20, size='Medium', rate_per_night=60)
    large_campsites = create_campsites(start=21, end=30, size='Large', rate_per_night=70)

    # Combine all campsites into one list
    campsites = small_campsites + medium_campsites + large_campsites

    # Log the successful initialization of campsites
    logger.info(f"Initialized {len(campsites)} campsites: "
                f"{len(small_campsites)} Small, {len(medium_campsites)} Medium, {len(large_campsites)} Large.")

    return campsites
