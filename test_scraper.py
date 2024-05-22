'''
Unit tests for scraper.py
'''
from unittest.mock import patch, MagicMock
import urllib.parse
import pytest
from scraper import extract_valid_urls, init_gsheets, clean_output, fetch_page, \
    parse_product_data, update_google_sheets, Product

@patch('scraper.build')
@patch('scraper.service_account.Credentials.from_service_account_info')
@patch('scraper.dotenv_values')
def test_init_gsheets(mock_dotenv_values, mock_from_service_account_info, mock_build):
    '''
    Test function for init_gsheets function
    '''
    # Mock the return value of dotenv_values
    mock_dotenv_values.return_value = {
        'private_key': 'mock_private_key\\nline2',
        'client_email': 'mock_client_email'
    }

    # Mock the return value of from_service_account_info
    mock_credentials = MagicMock()
    mock_from_service_account_info.return_value = mock_credentials

    # Mock the return value of build
    mock_service = MagicMock()
    mock_build.return_value = mock_service

    # Call the function
    service = init_gsheets()

    # Assert the mocks were called correctly
    mock_dotenv_values.assert_called_once_with(".envgsheets")
    mock_from_service_account_info.assert_called_once()
    mock_build.assert_called_once_with("sheets", "v4", credentials=mock_credentials)

    # Assert the service is returned correctly
    assert service == mock_service

def test_extract_valid_urls():
    '''
    Test function for extract_valid_urls function
    '''
    # Mock the service object
    mock_service = MagicMock()

    # Define the mock response from the Google Sheets API
    mock_response = {
        'values': [
            ['http://example.com'],
            ['https://anotherexample.com'],
            ['invalid-url'],
            ['ftp://yetanotherexample.com'],
            [None],
            ['']
        ]
    }

    # Configure the mock to return the response when the API call is made
    mock_service.spreadsheets().values().get().execute.return_value = mock_response

    # Call the function with the mocked service
    spreadsheet_id = 'dummy_spreadsheet_id'
    base_urls_range = 'dummy_range'
    result = extract_valid_urls(mock_service, spreadsheet_id, base_urls_range)

    # Define the expected result
    expected_result = [
        'http://example.com',
        'https://anotherexample.com',
        'ftp://yetanotherexample.com'
    ]

    # Assert that the function returns the expected result
    assert result == expected_result

def test_clean_output():
    '''
    Test function for clean_output function
    '''
    # Mock the service object
    mock_service = MagicMock()

    # Define dummy spreadsheet ID and output range
    spreadsheet_id = 'dummy_spreadsheet_id'
    output_range = 'dummy_output_range'

    # Call the function with the mocked service
    clean_output(mock_service, spreadsheet_id, output_range)

    # Assert that the clear method was called with the correct arguments
    mock_service.spreadsheets().values().clear.assert_called_once_with(
        spreadsheetId=spreadsheet_id,
        range=output_range
    )

    # Assert that the execute method was called on the result of the clear method
    mock_service.spreadsheets().values().clear.return_value.execute.assert_called_once()

def test_fetch_page():
    '''
    Test function for fetch_page function
    '''
    url = 'http://example.com'
    headers = {'user-agent': 'test-agent'}
    proxies = {'http': 'http://proxy.com'}

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch('scraper.requests.get', return_value=mock_response) as mock_get:
        response = fetch_page(url, headers, proxies)

        mock_get.assert_called_once_with(url, headers=headers, timeout=15, proxies=proxies)
        assert response.status_code == 200

def test_parse_product_data():
    '''
    Test function for parse_product_data function
    '''
    base_url = 'http://example.com'
    html_content = '''
    <div class="product-wrapper">
        <img src="/image.jpg" />
        <h4 class="price">$10.99</h4>
        <h4 class="title">Product Title</h4>
        <p class="description">Product Description</p>
        <p class="review-count"><span></span><span></span></p>
    </div>
    '''

    products = parse_product_data(base_url, html_content)

    assert len(products) == 1
    product = products[0]
    assert product.product_url == base_url
    assert product.title == 'Product Title'
    assert product.description == 'Product Description'
    assert product.price == '$10.99'
    assert product.rating == 2
    assert product.image_url == base_url + '/image.jpg'

def test_update_google_sheets():
    '''
    Test function for update_google_sheets function
    '''
    mock_service = MagicMock()
    spreadsheet_id = 'dummy_spreadsheet_id'
    output_range = 'dummy_output_range'

    products = [
        Product(
            'http://example.com',
            'Product Title',
            'Product Description',
            '$10.99',
            2,
            'http://example.com/image.jpg'
        )
    ]

    update_google_sheets(mock_service, spreadsheet_id, output_range, products)

    expected_body = {
        "values": [
            [
                'http://example.com',
                'Product Title',
                'Product Description',
                '$10.99',
                2,
                'http://example.com/image.jpg'
            ]
        ]
    }

    mock_service.spreadsheets().values().append.assert_called_once_with(
        spreadsheetId=spreadsheet_id,
        range=output_range,
        valueInputOption="RAW",
        body=expected_body
    )

    mock_service.spreadsheets().values().append.return_value.execute.assert_called_once()
