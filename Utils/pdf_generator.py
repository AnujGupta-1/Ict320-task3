import os
from fpdf import FPDF
from Utils.logger_config import logger

# Define the folder to save PDFs
PDF_FOLDER = "pdfs"

# Ensure the folder exists
def ensure_pdf_folder_exists():
    """
    Ensures that the PDF folder exists.
    """
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        logger.info(f"Created directory {PDF_FOLDER}.")
    else:
        logger.info(f"Directory {PDF_FOLDER} already exists.")

# Initialize the PDF folder
ensure_pdf_folder_exists()


class PDFGenerator(FPDF):
    """
    A class to handle the generation of PDF documents for booking confirmations and daily summaries.
    """

    def __init__(self, title):
        """
        Initialize the PDF with a title.
        
        :param title: The title to use in the PDF header.
        """
        super().__init__()
        self.title = title  # Set the PDF title
        self.add_page()  # Automatically add a page when initializing

    def header(self):
        """
        Sets the header for the PDF.
        """
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, self.title, 0, 1, "C")  # Centered title in the header

    def footer(self):
        """
        Sets the footer for the PDF, displaying the page number.
        """
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def add_content_line(self, label, value, currency=False):
        """
        Adds a single line of content to the PDF.

        :param label: The label for the content (e.g., 'Booking ID').
        :param value: The value for the content (e.g., 'B12345').
        :param currency: If True, formats the value as a currency.
        """
        formatted_value = f"${value:.2f}" if currency else value
        self.cell(0, 10, f"{label}: {formatted_value}", 0, 1)  # Add the label and value as a line

    def save_pdf(self, filename):
        """
        Saves the current PDF to a specified file.

        :param filename: The full path where the PDF will be saved.
        """
        self.output(filename)
        logger.info(f"PDF saved as {filename}")
        return filename

    def generate_confirmation(self, booking):
        """
        Generates a booking confirmation PDF.

        :param booking: The Booking object containing booking details.
        :return: The file path to the saved confirmation PDF.
        """
        self.set_title("Booking Confirmation")
        self.add_content_line("Booking Confirmation", booking.customer_name)
        self.add_content_line("Booking ID", booking.booking_id)
        self.add_content_line("Customer", booking.customer_name)
        self.add_content_line("Arrival Date", booking.arrival_date.strftime('%Y-%m-%d'))
        self.add_content_line("Campsite Size", booking.campsite_size)
        self.add_content_line("Total Sites Booked", booking.num_campsites)
        self.add_content_line("Total Cost", booking.total_cost, currency=True)

        # Define the filename and save the PDF
        filename = os.path.join(PDF_FOLDER, f"confirmation_{booking.booking_id}.pdf")
        return self.save_pdf(filename)

    def generate_summary(self, summary):
        """
        Generates a summary PDF for a day's bookings.

        :param summary: The Summary object containing summary details.
        :return: The file path to the saved summary PDF.
        """
        self.set_title("Daily Summary Report")
        self.add_content_line("Daily Summary Report", "")
        self.add_content_line("Campground ID", summary.campground_id)
        self.add_content_line("Summary Date", summary.summary_date)
        self.add_content_line("Total Sales", summary.total_sales, currency=True)
        self.add_content_line("Total Bookings", summary.total_bookings)

        # Define the filename and save the PDF
        filename = os.path.join(PDF_FOLDER, f"summary_{summary.summary_date}.pdf")
        return self.save_pdf(filename)


# Usage example:
# Assuming `booking` and `summary` objects are available

# pdf_generator = PDFGenerator("Booking Confirmation")
# confirmation_pdf_path = pdf_generator.generate_confirmation(booking)

# pdf_generator = PDFGenerator("Daily Summary Report")
# summary_pdf_path = pdf_generator.generate_summary(summary)
