import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION ---
SHEET_NAME = "Fragrance Data"  # The exact name of your Google Sheet
# ---------------------

def get_google_sheet():
    """Authenticates with Google and returns the sheet object."""
    try:
        # Define the scope of access
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        # Load the credentials from the GitHub Secret (environment variable)
        creds_json = os.environ.get("GCP_CREDENTIALS")
        
        if not creds_json:
            raise ValueError("GCP_CREDENTIALS not found in environment variables!")

        # Parse the JSON string into a dictionary
        creds_dict = json.loads(creds_json)
        
        # Authenticate
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Open the specific sheet
        sheet = client.open(SHEET_NAME).sheet1
        return sheet

    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def main():
    # 1. Connect to Google Sheets first to ensure connection works
    sheet = get_google_sheet()
    if not sheet:
        return  # Stop if we can't connect

    # 2. YOUR EXISTING SCRAPING LOGIC HERE
    # Let's say you scraped a fragrance and have these variables:
    # name = "Dior Sauvage"
    # price = "$120"
    # stock_status = "In Stock"
    # url = "https://example.com/dior"
    
    # (Example data for testing)
    scraped_data = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # Timestamp
        "Dior Sauvage",
        "$120",
        "In Stock",
        "https://example.com/dior"
    ]

    # 3. Append the data to the Google Sheet
    try:
        sheet.append_row(scraped_data)
        print(f"Successfully added row: {scraped_data[1]}")
    except Exception as e:
        print(f"Failed to append row: {e}")

if __name__ == "__main__":
    main()
