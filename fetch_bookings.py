import sys
from azure.cosmos import CosmosClient, exceptions
from Utils.logger_config import logger
from resources.db_config import get_cosmos_client  # Import the connection setup from db_config

# Connects to the Cosmos DB container using db_config
def connect_to_cosmos(container_name):
    """
    Connects to Cosmos DB container using configuration from db_config.py.
    
    :param container_name: Name of the container to connect to.
    :return: The Cosmos DB container client.
    """
    try:
        client = get_cosmos_client()  # Get the Cosmos client from db_config
        database = client.get_database_client("CampsiteBookingsDB")  # Specify the database name here
        container = database.get_container_client(container_name)
        logger.info(f"Connected to Cosmos DB container: {container_name}")
        return container
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Failed to connect to Cosmos DB: {e}")
        print("Failed to connect to Cosmos DB. Please check your configuration.")
        sys.exit(1)

# Function to retrieve booking details by booking ID or customer name
def retrieve_booking(cosmos_container, identifier):
    try:
        if identifier.isdigit():
            # Search by booking ID
            query = "SELECT * FROM c WHERE c.booking_id = @booking_id"
            parameters = [{"name": "@booking_id", "value": int(identifier)}]
        else:
            # Search by customer name
            query = "SELECT * FROM c WHERE CONTAINS(c.customer_name, @customer_name)"
            parameters = [{"name": "@customer_name", "value": identifier}]

        # Execute the query and retrieve the results
        items = list(cosmos_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if items:
            logger.info(f"Found {len(items)} bookings for identifier: {identifier}")
            for item in items:
                print(f"\nBooking ID: {item.get('booking_id')}")
                print(f"Customer Name: {item.get('customer_name')}")
                print(f"Arrival Date: {item.get('arrival_date')}")
                print(f"Campsite Size: {item.get('campsite_size')}")
                print(f"Total Cost: ${item.get('total_cost'):.2f}")
                print(f"Number of Campsites: {item.get('num_campsites')}")
                
                allocations = item.get('campsite_allocations', 'None')
                if isinstance(allocations, list) and allocations:
                    print(f"Campsite Allocations: {', '.join(map(str, allocations))}\n")
                else:
                    print("Campsite Allocations: None\n")
        else:
            logger.info(f"No bookings found for identifier: {identifier}")
            print(f"No bookings found for identifier: {identifier}")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error retrieving booking from Cosmos DB: {e}")
        print(f"Error retrieving booking from Cosmos DB: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")

def main():
    # Connect to the Cosmos DB container
    container_name = "Bookings"
    cosmos_container = connect_to_cosmos(container_name)

    print("Welcome to the Booking Retrieval System!")
    while True:
        identifier = input("Enter Booking ID or Customer Name (or type 'exit' to quit): ").strip()
        if identifier.lower() == 'exit':
            print("Exiting the Booking Retrieval System.")
            break

        # Retrieve and display booking details
        if identifier:
            retrieve_booking(cosmos_container, identifier)
        else:
            print("Please enter a valid Booking ID or Customer Name.")

if __name__ == "__main__":
    main()
