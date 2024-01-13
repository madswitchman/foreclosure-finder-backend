"""Module providing webscraping functionality for foreclosures"""
import json
import csv
import datetime
import logging
import os
import requests

# Define the base URLs for the primary and secondary API calls
PRIMARY_BASE_URL = "https://www.servicelinkauction.com/api/listingsvc/v1/listings"
SECONDARY_BASE_URL = ("https://www.servicelinkauction.com/api/auctiongatewaysvc/" +
                      "v1/PropertyReportData")

# Define the base directory
BASE_DIRECTORY = "_output"
os.makedirs(BASE_DIRECTORY, exist_ok=True)

# Define the log file path
log_file_path = os.path.join(BASE_DIRECTORY, "scraping.log")

# Define the search parameters for the primary API call
search_params = {
    "state": "AL",
    "sortByEndingSoonest": "true"
    # Add other search parameters as needed
}

# Get the current date and time
current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Create a dynamic file name with the current date, time, and state
csv_filename = f"auction_data_{current_datetime}_{search_params['state']}.csv"

# Defin csv file path
csv_file_path = os.path.join(BASE_DIRECTORY, csv_filename)

# Define the log file path
log_file_path = os.path.join(BASE_DIRECTORY,
                             f"auction_data_{current_datetime}_{search_params['state']}.log")

# Configure logging
logging.basicConfig(filename=log_file_path,
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s"
                    )

# Add a StreamHandler to display log messages in the console
console_handler = logging.StreamHandler()
# Set the desired log level for console output
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logging.getLogger("").addHandler(console_handler)

# Define the headers for the CSV file
csv_headers = [
    "Address", "City", "State", "Zip", "County", "Living Square Feet",
    "Year Built", "Lot (Acres)", "Lot (Square Feet)", "Land Use", "Subdivision",
    "APN", "Legal Description", "Property Use", "Units Count", "Bedrooms",
    "Bathrooms", "# of Stories", "Garage Type", "Garage Square Feet",
    "Air Conditioning Type", "Heating Type", "Fireplace",
    "Owner 1 First Name", "Owner 1 Last Name", "Owner 2 First Name",
    "Owner 2 Last Name", "Owner Mailing Address", "Owner Mailing City",
    "Owner Mailing State", "Owner Mailing Zip", "Ownership Length (Months)",
    "Owner Type", "Owner Occupied", "Vacant?", "Listing Status",
    "Listing Price", "Days on Market", "Last Updated", "Listing Agent Full Name",
    "Listing Agent First Name", "Listing Agent Last Name", "Listing Agent Email",
    "Listing Agent Phone", "Listing Office Phone", "MLS Type", "Last Sale Date",
    "Foreclosure Sale Date", "Last Sale Amount", "Estimated Value",
    "Estimated Equity", "Equity Percent",
    "Open Mortgage Balance", "Mortgage Interest Rate", "Mortgage Document Date",
    "Mortgage Loan Type", "Lender Name", "Deed Type", "Position", "Status",
    "Default Amount", "Opening bid", "Recording Date", "Auction Date",
    "Tax Amount", "Assessment Year", "Assessed Total Value", "Assessed Land Value",
    "Assessed Improvement Value", "Market Value", "Market Land Value",
    "Market Improvement Value"
]

try:
    # Initialize continuation token
    continuation_token = None  # pylint: disable=C0103

    while True:
        if continuation_token:
            # Add continuation token to search parameters
            search_params["continuationToken"] = continuation_token

        # Send a GET request to the primary API URL with the search parameters
        logging.info("Sending request to primary API...")
        primary_response = requests.get(
            PRIMARY_BASE_URL, params=search_params, timeout=10)

        # Print the request URL and response status code for the primary API
        logging.info("Request URL: %s", primary_response.request.url)
        logging.info("Response Status Code: %s", primary_response.status_code)

        # Check the response status code
        if primary_response.status_code == 200:
            # Parse the JSON response from the primary API
            primary_data = primary_response.json()

            # Pretty-print the JSON response for the primary API
            logging.info("Primary API Response:\n%s",
                         json.dumps(primary_data, indent=4))

            # Grab the continuation_token from the response
            continuation_token = primary_data.get("continuationToken", "")

            if primary_data.get("data"):
                # Initialize a CSV file for writing
                with open(csv_file_path, "a", encoding="utf-8", newline="") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=csv_headers)

                    # Write the CSV headers in the first iteration
                    if csvfile.tell() == 0:
                        writer.writeheader()

                    # Extract and write the data to the CSV file
                    for item in primary_data.get("data", []):
                        data_row = {}  # Create a dictionary for each row of data
                        property_info = item.get("propertyInfo", {})
                        listing_status = item.get("listingStatus", {})
                        auction_info = item.get("auctionRunInfo", {})

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
                        data_row["Bathrooms"] = property_info.get("baths", "")

                        data_row["Property Use"] = property_info.get(
                            "propertyType", "")

                        data_row["Vacant?"] = property_info.get(
                            "occupancyStatus", "")
                        data_row["Listing Status"] = listing_status.get(
                            "statusText", "")
                        data_row["Last Updated"] = property_info.get(
                            "lastUpdated", "")

                        data_row["Foreclosure Sale Date"] = property_info.get(
                            "foreclosureSaleDate", "")
                        #
                        # Below looks to be coming from a different source
                        #
                        # data_row["Listing Price"] = item.get("listingPrice", "")
                        # data_row["Days on Market"] = item.get("daysOnMarket", "")
                        # data_row["Land Use"] = property_info.get("landUse", "")
                        # data_row["Legal Description"] = property_info.get(
                        #     "legalDescription", "")
                        # data_row["Owner 1 First Name"] = property_info.get(
                        #     "owner1FirstName", "")
                        # data_row["Owner 1 Last Name"] = property_info.get(
                        #     "owner1LastName", "")
                        # data_row["Owner 2 First Name"] = property_info.get(
                        #     "owner2FirstName", "")
                        # data_row["Owner 2 Last Name"] = property_info.get(
                        #     "owner2LastName", "")
                        # data_row["Owner Mailing Address"] = property_info.get(
                        #     "ownerMailingAddress", "")
                        # data_row["Owner Mailing City"] = property_info.get(
                        #     "ownerMailingCity", "")
                        # data_row["Owner Mailing State"] = property_info.get(
                        #     "ownerMailingState", "")
                        # data_row["Owner Mailing Zip"] = property_info.get(
                        #     "ownerMailingZip", "")
                        # data_row["Ownership Length (Months)"] = property_info.get(
                        #     "ownershipLengthMonths", "")
                        # data_row["Owner Type"] = property_info.get("ownerType", "")
                        # data_row["Owner Occupied"] = property_info.get(
                        #     "ownerOccupied", "")
                        # data_row["Listing Agent Full Name"] = item.get(
                        #     "listingAgent", {}).get("fullName", "")
                        # data_row["Listing Agent First Name"] = item.get(
                        #     "listingAgent", {}).get("firstName", "")
                        # data_row["Listing Agent Last Name"] = item.get(
                        #     "listingAgent", {}).get("lastName", "")
                        # data_row["Listing Agent Email"] = item.get(
                        #     "listingAgent", {}).get("email", "")
                        # data_row["Listing Agent Phone"] = item.get(
                        #     "listingAgent", {}).get("phone", "")
                        # data_row["Listing Office Phone"] = item.get(
                        #     "listingOffice", {}).get("phone", "")
                        # data_row["MLS Type"] = item.get(
                        #     "listingStatus", {}).get("isTPS", "")
                        # data_row["Last Sale Date"] = item.get(
                        #     "lastSale", {}).get("saleDate", "")
                        # data_row["Last Sale Amount"] = item.get(
                        #     "lastSale", {}).get("saleAmount", "")
                        # data_row["Estimated Value"] = item.get(
                        #     "propertyInfo", {}).get("estimatedValue", "")
                        # data_row["Estimated Equity"] = item.get(
                        #     "propertyInfo", {}).get("estimatedEquity", "")
                        # data_row["Equity Percent"] = item.get(
                        #     "propertyInfo", {}).get("equityPercent", "")
                        # data_row["Open Mortgage Balance"] = item.get(
                        #     "propertyInfo", {}).get("openMortgageBalance", "")
                        # data_row["Mortgage Interest Rate"] = item.get(
                        #     "propertyInfo", {}).get("mortgageInterestRate", "")
                        # data_row["Mortgage Document Date"] = item.get(
                        #     "propertyInfo", {}).get("mortgageDocumentDate", "")
                        # data_row["Mortgage Loan Type"] = item.get(
                        #     "propertyInfo", {}).get("mortgageLoanType", "")
                        # data_row["Lender Name"] = item.get(
                        #     "propertyInfo", {}).get("lenderName", "")
                        # data_row["Deed Type"] = item.get(
                        #     "propertyInfo", {}).get("deedType", "")
                        # data_row["Position"] = item.get(
                        #     "propertyInfo", {}).get("position", "")
                        # data_row["Garage Square Feet"] = secondary_data.get(
                        #     "additionalPropertyCharacteristicsModel", {}).get("garageSqFt", "")
                        #
                        # End of different source
                        #
                        data_row["Status"] = auction_info.get(
                            "isInAuction", "")
                        # data_row["Default Amount"] = item.get(
                        #     "propertyInfo", {}).get("defaultAmount", "")
                        data_row["Opening bid"] = auction_info.get(
                            "startingBid", "")
                        # data_row["Recording Date"] = item.get(
                        #     "propertyInfo", {}).get("recordingDate", "")
                        data_row["Auction Date"] = auction_info.get(
                            "endDate", "")

                        # Make the secondary API call to retrieve additional data
                        global_property_id = property_info.get(
                            "globalPropertyId", "")
                        secondary_params = {
                            "GlobalPropertyId": global_property_id
                        }
                        logging.info("Sending request to secondary API...")
                        secondary_response = requests.get(
                            SECONDARY_BASE_URL, params=secondary_params, timeout=10)

                        # Print the request URL and response status code for the secondary API
                        logging.info("Request URL: %s",
                                     secondary_response.request.url)
                        logging.info("Response Status Code: %s",
                                     secondary_response.status_code)

                        # Check the response status code for the secondary API call
                        if secondary_response.status_code == 200:
                            # Parse the JSON response from the secondary API
                            secondary_data = secondary_response.json()

                            # Pretty-print the JSON response for the secondary API
                            logging.info("Secondary API Response:\n%s", json.dumps(
                                secondary_data, indent=4))

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

                            # Update any other fields with additional data from the
                            # secondary API response

                            # Write the data_row to the CSV file
                            writer.writerow(data_row)
            else:
                logging.warning(
                    "No data returned in the response. CSV file not created.")

            if not continuation_token:
                break  # No more data, exit the loop

        else:
            logging.error(
                "Failed to fetch data from the primary API. Status code: %s",
                primary_response.status_code)
            break

    logging.info("Scraping completed. Data saved to %s",
                 csv_file_path)

except RuntimeError as e:
    logging.error("An error occurred: %s", str(e))
