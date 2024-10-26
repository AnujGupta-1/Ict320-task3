import logging
import os

# Ensure the Logs directory exists
log_dir = os.path.join(os.path.dirname(__file__), 'Logs')
os.makedirs(log_dir, exist_ok=True)  # Create Logs directory if it doesn't exist

# Define the log file path in the Logs directory
log_file_path = os.path.join(log_dir, 'CampgroundApp.log')

# Create a file handler for logging to a file (INFO level and above)
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)  # Logs INFO level and above to the file
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Create a stream handler for logging to the console (WARNING level and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Logs WARNING and above to the console
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,  # Base logging level, INFO and above will be captured
    handlers=[file_handler, console_handler]  # Add both file and console handlers
)

# Create a logger instance for the application
logger = logging.getLogger('CampgroundAppLogger')

# Suppress verbose logs from external libraries (e.g., Azure SDK, urllib3)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.cosmos').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# Example logging usage
logger.info("Campground application logging setup complete.")
logger.warning("This is a warning message that will appear in the console and log file.")
logger.error("This is an error message.")
