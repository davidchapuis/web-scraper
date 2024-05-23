'''
Cleans rows from a Google Spreadsheets
'''
def clean_output(service, spreadsheet_id, output_range):
    '''
    Cleans rows from a Google Spreadsheets
    Inputs: Google Service Object, Google Spreadsheets ID, Google Spreadsheets sheet range
    Ouput: list of valid urls
    '''
    return service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, \
        range=output_range).execute()
