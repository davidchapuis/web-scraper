'''
Reads rows from a Google SpreadSheets and returns valid urls
'''
import urllib.parse
import logging

def extract_valid_urls(service, spreadsheet_id, base_urls_range):
    '''
    Reads rows from a Google SpreadSheets and returns valid urls
    Inputs: Google Service Object, Google Spreadsheets ID, Google Spreadsheets sheet range
    Ouput: list of valid urls
    '''
    try:
        rows = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=base_urls_range
        ).execute()
        rows_values = rows.get('values', [])
        base_urls = [row[0] for row in rows_values if row and urllib.parse.urlparse(row[0]).scheme]
        return base_urls
    except Exception as e:
        logging.error(f"Failed to extract valid URLs: {e}")
        raise
