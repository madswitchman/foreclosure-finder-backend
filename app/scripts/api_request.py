import datetime
import time
import io
import json
import csv
import os
import sys
import requests
import websocket
# import firebase_admin
from google.cloud import storage
from google.cloud import firestore
from google.oauth2 import service_account

# credentials = service_account.Credentials.from_service_account_file(
#     'serviceAccountKey.json')


# Extract the port from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python api_request.py <port>")
    sys.exit(1)

# port = sys.argv[1]
# Extract host and port from environment variables or use default values
ws_protocol = sys.argv[1]
host = sys.argv[2]
port = sys.argv[3]


# def load_service_account_key():
#     service_account_key_json = os.environ.get('SERVICE_ACCOUNT_KEY')

#     if service_account_key_json:
#         return json.loads(service_account_key_json)
#     else:
#         # raise ValueError(
#         #     'Service account key not found in environment variable.')
#         return service_account.Credentials.from_service_account_file(
#             'serviceAccountKey.json')

def load_service_account_key():
    service_account_key_json = os.environ.get('SERVICE_ACCOUNT_KEY')

    # Check if running locally
    if service_account_key_json:
        # Load credentials from Cloud Run environment variable
        credentials = service_account.Credentials.from_service_account_info(
            {
                "type": os.getenv('TYPE'),
                "project_id": os.getenv('PROJECT_ID'),
                "private_key_id": os.getenv('PRIVATE_KEY_ID'),
                "private_key": os.getenv('PRIVATE_KEY').replace('\\n', '\n'),
                "client_email": os.getenv('CLIENT_EMAIL'),
                "client_id": os.getenv('CLIENT_ID'),
                "auth_uri": os.getenv('AUTH_URI'),
                "token_uri": os.getenv('TOKEN_URI'),
                "auth_provider_x509_cert_url": os.getenv('AUTH_PROVIDER_X509_CERT_URL'),
                "client_x509_cert_url": os.getenv('CLIENT_X509_CERT_URL')
            }
        )
        return credentials
    else:
        return service_account.Credentials.from_service_account_file(
            'serviceAccountKey.json')


# Get the current date and time
current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Read POST data from nodeJS Python stdin
post_data = sys.stdin.read()

# Parse the JSON data
request_data = json.loads(post_data)

# Construct the WebSocket server address
websocket_server_address = f"{ws_protocol}{host}:{port}"

# Extract params from request_data
state = request_data.get("state", "")
# sortByEndingSoonest = request_data.get("sortByEndingSoonest", "")
# limit = request_data.get("limit", 100)  # Default limit value if not provided


# Define the search parameters for the primary API call
search_params = {
    "state": state,
    "sortByEndingSoonest": True,
    # "limit": limit
    # Add other search parameters as needed
}

# Create a dynamic file name with the current date, time, and state
csv_filename = f"auction_data_{current_datetime}_{search_params['state']}.csv"

# Define the base URLs for the primary and secondary API calls
PRIMARY_BASE_URL = "https://www.servicelinkauction.com/api/listingsvc/v1/listings"
SECONDARY_BASE_URL = ("https://www.servicelinkauction.com/api/auctiongatewaysvc/" +
                      "v1/PropertyReportData")

# Define the base directory
BASE_DIRECTORY = "_output"

# Define the log file path
log_file_path = os.path.join(BASE_DIRECTORY, "scraping.log")

# Initialize Firebase Admin SDK
# firebase_admin.initialize_app()

# Initialize Firestore client
# db = firestore.Client()
db = firestore.Client(credentials=load_service_account_key())

# Initialize the Cloud Storage client
client = storage.Client(credentials=load_service_account_key())

# Get a reference to the default bucket
bucket = client.get_bucket(client.project)

# Retrieve the bucket name
bucket_name = "foreclosurefinderbackend"

# After processing, upload the CSV file to Cloud Storage
csv_data = io.StringIO()
blob = bucket.blob(csv_filename)

# Define the headers for the CSV file
csv_headers = [
    "Address", "City", "State", "Zip", "County", "Living Square Feet",
    "Year Built", "Lot (Acres)", "Lot (Square Feet)", "Subdivision",
    "APN", "Property Use", "Units Count", "Bedrooms",
    "Bathrooms", "# of Stories", "Garage Type",
    "Air Conditioning Type", "Heating Type", "Fireplace", "Vacant?", "Listing Status",
    "Opening bid", "Recording Date", "Auction Date",
    "Tax Amount", "Assessment Year", "Assessed Total Value", "Assessed Land Value",
    "Assessed Improvement Value", "Market Value", "Market Land Value",
    "Market Improvement Value", "URL"
]


def send_progress(progress):
    sys.stdout.write(f"{{\"progress\": {progress}}}\n")
    sys.stdout.flush()


def notify_file_uploaded():
    doc_ref = db.collection("fileUploads").document()
    # Replace "example.txt" with the actual file name
    doc_ref.set({"fileName": csv_filename})


def send_data(data):
    # Convert data to JSON format
    json_data = json.dumps(data)
    # Add this line for logging
    sys.stdout.write("Sending data from Python: " + json_data)
    # Send JSON data over WebSocket
    ws.send(json_data)


try:
    # Connect to WebSocket server
    print(websocket_server_address)
    ws = websocket.create_connection(websocket_server_address)
    print("WebSocket connection opened from api_request.py with address: " +
          websocket_server_address)

    continuation_token = None
    total_records = None
    processed_records = 0
    # Capture the start time
    start_time = time.time()

    # Create a CSV file in memory
    csv_writer = csv.DictWriter(
        csv_data, fieldnames=csv_headers, lineterminator='\n')
    csv_writer.writeheader()

    # Create an empty list to collect all the rows
    csv_rows = []

    while True:
        sys.stdout.write("Entering the main loop.")
        if continuation_token:
            # Add continuation token to search parameters
            search_params["continuationToken"] = continuation_token

        # Send a GET request to the primary API URL with the search parameters
        # logging.debug("Sending request to primary API...")

        primary_response = requests.get(
            PRIMARY_BASE_URL, params=search_params, timeout=10)
        print("Request URL: ", primary_response.request.url)

        # Print the request URL and response status code for the primary API
        # logging.debug("Request URL: %s", primary_response.request.url)
        # logging.debug("Response Status Code: %s", primary_response.status_code)

        # Check the response status code
        if primary_response.status_code == 200:
            print("Primary Response was 200")
            # Parse the JSON response from the primary API
            primary_data = primary_response.json()

            # Pretty-print the JSON response for the primary API
            # logging.debug("Primary API Response:\n%s",
            #               json.dumps(primary_data, indent=4))

            # Grab the continuation_token from the response
            continuation_token = primary_data.get("continuationToken", "")

            # Calculate the total number of records from the API response
            if total_records is None:
                print("Total records is none")
                total_records = primary_data.get("searchResultCount", 0)

            if primary_data.get("data"):
                print("Primary Data get")
                # Initialize a CSV file for writing
                # with open(csv_file_path, "a", encoding="utf-8", newline="") as csvfile:
                #     writer = csv.DictWriter(csvfile, fieldnames=csv_headers)

                # Write the CSV headers in the first iteration
                # if csvfile.tell() == 0:
                #     writer.writeheader()

                # Extract and write the data to the CSV file
                for item in primary_data.get("data", []):
                    print("Processing data in the main loop (primary_data)...")
                    data_row = {}  # Create a dictionary for each row of data

                    property_info = item.get("propertyInfo", {})
                    listing_status = item.get("listingStatus", {})
                    auction_info = item.get("auctionRunInfo", {})

                    # Increment the processed records count
                    processed_records += 1

                    # Calculate and display progress
                    progress = (processed_records / total_records) * 100
                    # logging.info("Progress: %.2f%%", progress)
                    progress_message = f"Progress: {progress:.2f}%"
                    print(f"Progress: {progress:.2f}%")
                    # Send progress update as JSON
                    sys.stdout.write(f"{{\"progress\": {progress}}}\n")
                    sys.stdout.flush()
                    # logging.info(progress_message)

                    data_row["Address"] = property_info.get("address", "")
                    data_row["City"] = property_info.get("city", "")
                    data_row["State"] = property_info.get("state", "")
                    data_row["Zip"] = property_info.get("postalCode", "")
                    data_row["County"] = property_info.get("county", "")
                    data_row["Living Square Feet"] = property_info.get(
                        "interiorSqFt", "")
                    data_row["Year Built"] = property_info.get(
                        "yearBuilt", "")
                    data_row["Lot (Acres)"] = property_info.get(
                        "lotSize", "")
                    data_row["Bedrooms"] = property_info.get(
                        "bedrooms", "")
                    data_row["Bathrooms"] = property_info.get(
                        "fullBathrooms", "")
                    data_row["Property Use"] = property_info.get(
                        "propertyType", "")
                    data_row["Vacant?"] = property_info.get(
                        "occupancyStatus", "")
                    data_row["Listing Status"] = listing_status.get(
                        "statusText", "")
                    data_row["Opening bid"] = auction_info.get(
                        "startingBid", "")
                    data_row["Auction Date"] = auction_info.get(
                        "endDate", "")
                    data_row["URL"] = f'=HYPERLINK("{property_info.get("websiteUrl", "")}", "Link")'

                    # csv_writer.writerow(data_row)

                    # Make the secondary API call to retrieve additional data
                    global_property_id = property_info.get(
                        "globalPropertyId", "")
                    secondary_params = {
                        "GlobalPropertyId": global_property_id
                    }
                    # logging.debug("Sending request to secondary API...")
                    secondary_response = requests.get(
                        SECONDARY_BASE_URL, params=secondary_params, timeout=10)

                    # Print the request URL and response status code for the secondary API
                    # logging.debug("Request URL: %s",
                    #               secondary_response.request.url)
                    # logging.debug("Response Status Code: %s",
                    #               secondary_response.status_code)

                    # Check the response status code for the secondary API call
                    if secondary_response.status_code == 200:
                        print("Processing data in the main loop (secondary_data)...")
                        # Parse the JSON response from the secondary API
                        secondary_data = secondary_response.json()

                        # Pretty-print the JSON response for the secondary API
                        # logging.debug("Secondary API Response:\n%s", json.dumps(
                        #     secondary_data, indent=4))

                        # Extract and update data_row with additional
                        # data from the secondary API response
                        data_row["Lot (Square Feet)"] = secondary_data.get(
                            "additionalPropertyCharacteristicsModel", {}).get("lotSize", "")
                        data_row["Subdivision"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("subdivisionName", "")
                        data_row["APN"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("apn", "")
                        data_row["Units Count"] = secondary_data.get(
                            "additionalPropertyCharacteristicsModel", {}).get("numUnits", "")
                        data_row["# of Stories"] = secondary_data.get(
                            "additionalPropertyCharacteristicsModel", {}).get("numStories", "")
                        data_row["Garage Type"] = secondary_data.get(
                            "additionalPropertyCharacteristicsModel", {}).get("garageType", "")
                        data_row["Air Conditioning Type"] = secondary_data.get(
                            "additionalPropertyCharacteristicsModel", {}).get("ac", "")
                        data_row["Heating Type"] = secondary_data.get(
                            "additionalPropertyCharacteristicsModel", {}).get("heating", "")
                        data_row["Fireplace"] = secondary_data.get(
                            "additionalPropertyCharacteristicsModel", {}).get("firePlace", "")
                        data_row["Tax Amount"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("taxAmount", "")
                        data_row["Assessment Year"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("assessmentYear", "")
                        data_row["Assessed Total Value"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("totalAssessedValue", "")
                        data_row["Assessed Land Value"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("assessedLandValue", "")
                        data_row["Assessed Improvement Value"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("assessedImprovement", "")
                        data_row["Market Value"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("totalMarketValue", "")
                        data_row["Market Land Value"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("marketLandValue", "")
                        data_row["Market Improvement Value"] = secondary_data.get(
                            "countyTaxAssessmentModel", {}).get("marketImprovementValue", "")

                        # Write the data_row to the CSV file
                        # writer.writerow(data_row)
                        # csv_writer.writerow(item)
                        # Filter data_row to include only fields present in csv_headers
                        filtered_data_row = {key: item.get(
                            key, "") for key in csv_headers}

                        # Merge primary and secondary data
                        merged_data = {**item, **filtered_data_row}

                        # Filter merged_data to include only fields present in csv_headers
                        filtered_merged_data = {key: merged_data.get(
                            key, "") for key in csv_headers}

                        # csv_rows.append(data_row)
                        # Write the row to the CSV file in memory
                        # csv_rows.append(filtered_merged_data)
                        csv_writer.writerow(data_row)

                # Send progress update to Node.js server
                send_progress(progress)

            # else:
                # logging.warning(
                #     "No data returned in the response. CSV file not created.")

            if not continuation_token:
                print("No continuation token")
                break  # No more data, exit the loop

        else:
            print("Failed to fetch data from the primary API. Status code: %s",
                  primary_response.status_code)
            # logging.error(
            #     "Failed to fetch data from the primary API. Status code: %s",
            #     primary_response.status_code)
            break

    # Write all rows to the CSV file
    csv_writer.writerows(csv_rows)

    print(csv_rows)

    # Upload the CSV file to Cloud Storage
    blob.upload_from_string(csv_data.getvalue(), content_type='text/csv')

    # Get the public URL of the uploaded file
    file_url = blob.public_url
    # file_url = blob.generate_signed_url(
    # datetime.timedelta(days=1), method='GET')

    # Send the file info (name and URL) to the Node.js server
    send_data({"type": "fileInfo", "fileName": blob.name, "fileUrl": file_url})

    # After successfully uploading the file
    notify_file_uploaded()

    # Send progress update to Node.js server
    send_progress(100)
    # csv_data.seek(0)  # Reset the pointer to the beginning of the StringIO

    print("Main loop finished.")

except Exception as e:
    print("Failed to connect to WebSocket server:", e)

finally:
    # Close WebSocket connection
    ws.close()
