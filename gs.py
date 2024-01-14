# Google Sheets stuff
import os
import pickle
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SHEETS_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SCOPES = [SHEETS_READ_WRITE_SCOPE]

# Source: https://developers.google.com/sheets/api/quickstart/python
def get_or_create_credentials(scopes):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scopes)
        creds.refresh(Request())
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scopes)
            creds = flow.run_local_server(port=12580)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def init_gs():
    credentials = get_or_create_credentials(
        scopes=SCOPES
    )  # or use GoogleCredentials.get_application_default()
    service = build("sheets", "v4", credentials=credentials)
    return service


def create_gs(service, spreadsheet_id):
    date = str(datetime.today().strftime("%Y-%m-%d"))
    data = {"requests": [{"addSheet": {"properties": {"title": date}}}]}
    res = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=data)
        .execute()
    )
    return res


def update_gs(service, spreadsheet_id, headers, final_rows):
    date = str(datetime.today().strftime("%Y-%m-%d"))
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=date + "!A:Z",
        body={"majorDimension": "ROWS", "values": [headers]},
        valueInputOption="USER_ENTERED",
    ).execute()
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=date + "!A:Z",
        body={"majorDimension": "ROWS", "values": final_rows},
        valueInputOption="USER_ENTERED",
    ).execute()
    range = date
    ssinfo = (
        service.spreadsheets().get(spreadsheetId=spreadsheet_id, ranges=range).execute()
    )
    sheet_gid = ssinfo["sheets"][0]["properties"]["sheetId"]
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_gid,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "endColumnIndex": 17,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.19, "green": 0.19, "blue": 0.39},
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                            "bold": True,
                        },
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_gid,
                    "startColumnIndex": 5,
                    "endColumnIndex": 6,
                },
                "cell": {
                    "userEnteredFormat": {
                        "numberFormat": {
                            "type": "PERCENT",
                            "pattern": "#%",
                        }
                    }
                },
                "fields": "userEnteredFormat(numberFormat)",
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_gid,
                    "startRowIndex": 1,
                    "endRowIndex": len(final_rows) + 1,
                    "endColumnIndex": 17,
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 0.929,
                            "green": 0.929,
                            "blue": 0.929,
                        },
                        "horizontalAlignment": "LEFT",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor, horizontalAlignment)",
            }
        },
    ]
    column_widths = [
        {"columnNumber": 1, "width": 280},
        {"columnNumber": 2, "width": 60},
        {"columnNumber": 3, "width": 60},
        {"columnNumber": 4, "width": 100},
        {"columnNumber": 5, "width": 80},
        {"columnNumber": 6, "width": 100},
        {"columnNumber": 7, "width": 125},
        {"columnNumber": 8, "width": 100},
        {"columnNumber": 9, "width": 125},
        {"columnNumber": 10, "width": 100},
        {"columnNumber": 11, "width": 100},
        {"columnNumber": 12, "width": 100},
        {"columnNumber": 13, "width": 105},
        {"columnNumber": 14, "width": 105},
        {"columnNumber": 15, "width": 105},
        {"columnNumber": 16, "width": 105},
        {"columnNumber": 17, "width": 105},
    ]

    cw = [
        {
            "updateDimensionProperties": {
                "properties": {"pixelSize": e["width"]},
                "range": {
                    "dimension": "COLUMNS",
                    "sheetId": sheet_gid,
                    "startIndex": e["columnNumber"] - 1,
                    "endIndex": e["columnNumber"],
                },
                "fields": "pixelSize",
            }
        }
        for e in column_widths
    ]
    requests = requests + cw
    res = (
        service.spreadsheets()
        .batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests})
        .execute()
    )
