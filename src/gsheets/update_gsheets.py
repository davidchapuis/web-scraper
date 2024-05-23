'''
Updates Google Sheets with product data
'''
def update_gsheets(service, spreadsheet_id, output_range, products):
    '''
    Updates Google Sheets with product data
    '''
    data = [
        [
            product.product_url,
            product.title,
            product.description,
            product.price,
            product.rating,
            product.image_url
        ] for product in products
    ]

    body = {"values": data}
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=output_range,
        valueInputOption="RAW",
        body=body
    ).execute()
