import os
from fpdf import FPDF
from Database.cosmosDB import connect_to_cosmos, upsert_booking_pdf_to_cosmos
from Utils.logger_config import logger

def ensure_directory_exists(directory):
    """
    Ensures the given directory exists, creating it if necessary.

    :param directory: The path to the directory.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Directory {directory} created.")
    else:
        logger.info(f"Directory {directory} already exists.")


class BookingPDFGenerator:
    """
    A class responsible for creating and saving PDF files for booking confirmations.
    """

    def __init__(self, booking):
        """
        Initialize with the booking object to generate a PDF.

        :param booking: Booking object with details for the PDF.
        """
        self.booking = booking

    def create_pdf(self):
        """
        Create a PDF object using FPDF for the given booking details.

        :return: An FPDF object representing the generated PDF.
        """
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, txt=f"Booking Confirmation - {self.booking.customer_name}", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, txt=f"Booking ID: {self.booking.booking_id}", ln=True)
        pdf.cell(200, 10, txt=f"Customer Name: {self.booking.customer_name}", ln=True)
        pdf.cell(200, 10, txt=f"Arrival Date: {self.booking.arrival_date.strftime('%Y-%m-%d')}", ln=True)
        pdf.cell(200, 10, txt=f"Campsite Size: {self.booking.campsite_size}", ln=True)
        pdf.cell(200, 10, txt=f"Number of Sites Booked: {self.booking.num_campsites}", ln=True)

        return pdf

    def save_pdf(self, directory):
        """
        Saves the generated PDF to the specified directory.

        :param directory: The directory where the PDF will be saved.
        :return: The file path of the saved PDF.
        """
        ensure_directory_exists(directory)
        file_path = os.path.join(directory, f"confirmation_{self.booking.booking_id}.pdf")
        pdf = self.create_pdf()
        pdf.output(file_path)
        logger.info(f"PDF saved at {file_path}")
        return file_path


def insert_pdf_to_cosmos(file_path, booking_id):
    """
    Inserts the generated PDF into Cosmos DB.

    :param file_path: Path to the PDF file.
    :param booking_id: The ID of the booking to associate with the PDF.
    """
    try:
        cosmos_container = connect_to_cosmos("PDFs")
        upsert_booking_pdf_to_cosmos(cosmos_container, file_path, booking_id)
        logger.info(f"Successfully inserted PDF {file_path} into Cosmos DB for booking {booking_id}.")
    except Exception as e:
        logger.error(f"Failed to insert PDF into Cosmos DB: {e}")
        raise


def generate_booking_confirmation(booking):
    """
    Generates a booking confirmation PDF and inserts it into Cosmos DB.

    :param booking: Booking object containing the booking details.
    """
    try:
        # Generate and save the PDF to the 'pdfs' folder
        pdf_generator = BookingPDFGenerator(booking)
        pdf_directory = "pdfs"
        pdf_path = pdf_generator.save_pdf(pdf_directory)

        # Insert the PDF into Cosmos DB
        insert_pdf_to_cosmos(pdf_path, booking.booking_id)

    except Exception as e:
        logger.error(f"An error occurred during confirmation generation for booking {booking.booking_id}: {e}")
