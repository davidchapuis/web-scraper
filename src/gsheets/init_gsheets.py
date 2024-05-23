'''
Initializes Google API
'''
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import dotenv_values

def init_gsheets():
    '''
    Initializes Google API
    '''
    gsheets_config = dotenv_values(".envgsheets")

    if 'private_key' not in gsheets_config:
        raise ValueError("Missing private key in environment configuration")

    key_escaped = gsheets_config['private_key'].replace("\\n", "\n")
    gsheets_config['private_key'] = key_escaped

    try:
        credentials = service_account.Credentials.from_service_account_info(
            gsheets_config,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build("sheets", "v4", credentials=credentials)
        return service
    except Exception as e:
        logging.error(f"Failed to initialize Google Sheets service: {e}")
        raise
