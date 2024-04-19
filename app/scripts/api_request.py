import datetime
import io
import json
import csv
import os
import sys
import requests
from google.cloud import storage
from google.cloud import firestore
from google.oauth2 import service_account


def load_service_account_key():
    service_account_key_json = os.environ.get('SERVICE_ACCOUNT_KEY')

    if service_account_key_json:
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
                "client_x509_cert_url": os.getenv('CLIENT_X509_CERT_URL'),
                "universe_domain": os.getenv('UNIVERSE_DOMAIN')
            }
        )
        return credentials
    else:
        return service_account.Credentials.from_service_account_file(
            'serviceAccountKey.json')


current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

post_data = sys.stdin.read()
print("post_data:", post_data)
request_data = json.loads(post_data)

db = firestore.Client(credentials=load_service_account_key())

client = storage.Client(credentials=load_service_account_key())
bucket = client.get_bucket(client.project)

state = request_data.get("state", "")
sys.stdout.write(f"{{\"state\": {state}}}\n")

PRIMARY_BASE_URL = "https://www.servicelinkauction.com/api/listingsvc/v1/listings"
SECONDARY_BASE_URL = ("https://www.servicelinkauction.com/api/auctiongatewaysvc/" +
                      "v1/PropertyReportData")

BASE_DIRECTORY = "_output"

csv_filename = f"auction_data_{current_datetime}_{request_data['state']}.csv"

csv_data = io.StringIO()

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

search_params = {
    "state": state,
    "sortByEndingSoonest": True,
    # "limit": limit
    # Add other search parameters as needed
}


def send_progress(progress):
    sys.stdout.write(f"{{\"progress\": {progress}}}\n")
    sys.stdout.flush()


def send_file_info(file_name, file_url):
    sys.stdout.write(json.dumps(
        {"type": "fileInfo", "fileName": file_name, "fileUrl": file_url}) + '\n')
    sys.stdout.flush()


try:
    continuation_token = None
    total_records = None
    processed_records = 0
    start_time = datetime.datetime.now()

    csv_writer = csv.DictWriter(
        csv_data, fieldnames=csv_headers, lineterminator='\n')
    csv_writer.writeheader()

    while True:
        if continuation_token:
            search_params["continuationToken"] = continuation_token

        primary_response = requests.get(
            PRIMARY_BASE_URL, params=search_params, timeout=10)
        print("Request URL: ", primary_response.request.url)

        if primary_response.status_code == 200:
            primary_data = primary_response.json()
            continuation_token = primary_data.get("continuationToken", "")

            if total_records is None:
                total_records = primary_data.get("searchResultCount", 0)

            if primary_data.get("data"):
                for item in primary_data.get("data", []):
                    processed_records += 1
                    progress = (processed_records / total_records) * 100
                    send_progress(progress)

                    property_info = item.get("propertyInfo", {})
                    listing_status = item.get("listingStatus", {})
                    auction_info = item.get("auctionRunInfo", {})

                    data_row = {
                        "Address": property_info.get("address", ""),
                        "City": property_info.get("city", ""),
                        "State": property_info.get("state", ""),
                        "Zip": property_info.get("postalCode", ""),
                        "County": property_info.get("county", ""),
                        "Living Square Feet": property_info.get("interiorSqFt", ""),
                        "Year Built": property_info.get("yearBuilt", ""),
                        "Lot (Acres)": property_info.get("lotSize", ""),
                        "Bedrooms": property_info.get("bedrooms", ""),
                        "Bathrooms": property_info.get("fullBathrooms", ""),
                        "Property Use": property_info.get("propertyType", ""),
                        "Vacant?": property_info.get("occupancyStatus", ""),
                        "Listing Status": listing_status.get("statusText", ""),
                        "Opening bid": auction_info.get("startingBid", ""),
                        "Auction Date": auction_info.get("endDate", ""),
                        "URL": f'=HYPERLINK("{property_info.get("websiteUrl", "")}", "Link")'
                    }

                    csv_writer.writerow(data_row)

                    global_property_id = property_info.get(
                        "globalPropertyId", "")
                    secondary_params = {
                        "GlobalPropertyId": global_property_id}
                    secondary_response = requests.get(
                        SECONDARY_BASE_URL, params=secondary_params, timeout=10)

                    if secondary_response.status_code == 200:
                        secondary_data = secondary_response.json()

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

                        csv_writer.writerow(data_row)

                send_progress(progress)

            if not continuation_token:
                break

        else:
            print("Failed to fetch data from the primary API. Status code:",
                  primary_response.status_code)
            sys.exit(1)

    csv_contents = csv_data.getvalue()
    blob = bucket.blob(csv_filename)
    blob.upload_from_string(csv_contents)

    doc_ref = db.collection("fileUploads").document()
    doc_ref.set({"fileName": csv_filename})

    send_file_info(csv_filename, blob.public_url)

except Exception as e:
    print("Error:", e)
