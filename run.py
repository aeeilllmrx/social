import os
import random
from datetime import date, datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from twilio.rest import Client

# Google Sheets configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]  # Move to environment variable
RANGE_NAME = "Sheet1!A2:C"


def get_google_sheets_service():
    try:
        # Get credentials from environment variable
        credentials_json = os.environ["GOOGLE_CREDENTIALS"]

        # Create credentials object from service account info
        credentials = service_account.Credentials.from_service_account_info(
            eval(credentials_json), scopes=SCOPES  # Convert string to dictionary
        )

        return build("sheets", "v4", credentials=credentials)
    except Exception as e:
        print(f"Error setting up Google Sheets service: {e}")
        raise


def get_people_to_call():
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()

        result = (
            sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        )

        rows = result.get("values", [])
        to_call = []

        for row in rows:
            if len(row) >= 3:
                name = row[0]
                last_called = (
                    datetime.strptime(row[1], "%Y-%m-%d").date() if row[1] else None
                )
                interval = int(row[2])

                if not last_called or (date.today() - last_called).days >= interval:
                    to_call.append(name)

        return to_call

    except Exception as e:
        print(f"Error getting people to call: {e}")
        return []


def send_text(body):
    try:
        account_sid = os.environ["ACCOUNT_SID"]
        auth_token = os.environ["AUTH_TOKEN"]
        twilio_number = os.environ["TWILIO_NUMBER"]
        recipient_number = os.environ["RECIPIENT_NUMBER"]

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=body,
            from_=twilio_number,
            to=recipient_number,
        )
    except Exception as e:
        print(f"Error sending text: {e}")
        raise


def update_last_called(name):
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()

        # Find the row with the matching name
        result = (
            sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        )

        rows = result.get("values", [])
        row_index = None

        for i, row in enumerate(rows):
            if row[0] == name:
                row_index = i + 2  # +2 because range starts at A2
                break

        if row_index:
            range_name = f"Sheet1!B{row_index}"
            today_str = date.today().strftime("%Y-%m-%d")

            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption="RAW",
                body={"values": [[today_str]]},
            ).execute()

    except Exception as e:
        print(f"Error updating sheet: {e}")
        raise


def main():
    try:
        people_to_call = get_people_to_call()

        if people_to_call:
            name = random.choice(people_to_call)
            body = f"Have you called {name} lately? (Who by the way doesn't hate you)"

            send_text(body)
            update_last_called(name)

    except Exception as e:
        print(f"Error in main: {e}")


if __name__ == "__main__":
    main()
