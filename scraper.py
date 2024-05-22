'''
Webscraper that extracts product data from e-commerce websites.
Input: list of urls in Google Sheets 
Output: list of products in Google Sheets with product url, title, description,
price, rating and image url
'''
import random
import time
from datetime import datetime
import urllib.parse
import logging
import os
import requests
from dotenv import load_dotenv, dotenv_values
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def init_gsheets():
    '''
    Initializes Google API
    '''
    gsheets_config = dotenv_values(".envgsheets")
    key_escaped = gsheets_config['private_key'].replace("\\n", "\n")
    gsheets_config['private_key'] = key_escaped

    credentials = service_account.Credentials.from_service_account_info(gsheets_config, \
            scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build("sheets", "v4", credentials=credentials)
    return service

def extract_valid_urls(service, spreadsheet_id, base_urls_range):
    '''
    Reads rows from a Google SpreadSheets and returns valid urls
    Inputs: Google Service Object, Google Spreadsheets ID, Google Spreadsheets sheet range
    Ouput: list of valid urls
    '''
    rows = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=base_urls_range
    ).execute()

    # Get the values from the response
    rows_values = rows.get('values', [])

    base_urls = [row[0] for row in rows_values if row and urllib.parse.urlparse(row[0]).scheme]
    return base_urls

def clean_output(service, spreadsheet_id, output_range):
    '''
    Cleans rows from a Google Spreadsheets
    Inputs: Google Service Object, Google Spreadsheets ID, Google Spreadsheets sheet range
    Ouput: list of valid urls
    '''
    return service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, \
        range=output_range).execute()

# Set up Product class
class Product:
    '''
    A product has an url, a title, a description, a price, a rating and an image url.
    '''
    def __init__(self, product_url, title, description, price, rating, image_url):
        self.product_url = product_url
        self.title = title
        self.description = description
        self.price = price
        self.rating = rating
        self.image_url = image_url

def load_proxies():
    '''
    Reads proxy addresses from environment variables
    '''
    load_dotenv(".envproxy")
    proxies = {
        "http" : os.getenv("HTTP"), 
        "https": os.getenv("HTTPS"),
        "socks5": os.getenv("SOCKS5")
    }
    return proxies

def scrape_links(base_urls, service, spreadsheet_id, output_range):
    '''
    Takes a list of valid urls and, scrapes data and dumps it in a Google Spreadsheets
    Inputs: 
    List of valid urls, 
    Google Service object, 
    Google Spreadsheets ID, 
    Google Spreadsheets range

    Output: 
    None
    '''
    blocked = False
    proxies = load_proxies()

    for url in base_urls:
        try:
            delay = random.uniform(0.657, 5.438)
            headers = {
                'accept-language': 'en-US;q=0.5,en;q=0.3',
                'content-type': 'text/html; charset=utf-8',
                'accept-encoding': 'gzip, deflate, br',
                'user-agent': '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) \
                Gecko/20100101 Firefox/123.0''',
            }

            response = fetch_page(url, headers, proxies)
            logging.info(f"HTTP status code: {response.status_code}")
            time.sleep(delay)

            if response.status_code == 200:
                logging.info("Parsing product data...")
                products = parse_product_data(url, response.content)
                logging.info("Adding product data to Google Sheets...")
                update_google_sheets(service, spreadsheet_id, output_range, products)
                logging.info("Product data added to Google Sheets")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logging.warning("Access denied")
                blocked = True
                break
            elif e.response.status_code == 429:
                logging.warning(f"Rate limited. Retrying after {delay} seconds.")
                delay *= 2  # Exponential backoff
                continue
            else:
                logging.error(f'''Failed to retrieve the webpage.
                    Status Code: {e.response.status_code}''')
                continue
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching page {url}: {e}")
            break

def fetch_page(url, headers, proxies):
    '''
    Retrieves URLs using Requests
    Inputs: URL, headers, proxies
    Output: HTTP response
    '''
    response = requests.get(url, headers=headers, timeout=15, proxies=proxies)
    response.raise_for_status()
    return response

def parse_product_data(base_url, content):
    '''
    Parses product data 
    '''
    soup = BeautifulSoup(content, 'html.parser')
    products = []

    for product in soup.find_all('div', class_='product-wrapper'):
        image_url = base_url + product.find('img')['src']
        price = product.find('h4', class_='price').text.strip()
        title = product.find('h4', class_='title').text.strip()
        description = product.find('p', class_='description').text.strip()
        rating_tags = product.find('p', class_='review-count')
        rating = len(rating_tags.find_all('span'))
        product_url = base_url
        product = Product(product_url, title, description, price, rating, image_url)
        products.append(product)

    return products

def update_google_sheets(service, spreadsheet_id, output_range, products):
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

def lambda_handler(event, context):
    '''
    AWS Lambda function
    '''
    # Set up logging
    log_filename = f"{datetime.now().strftime('%Y-%m-%d')}-run.log"
    logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Set up a logger
    logging.getLogger()

    # Initialize Google spreadsheet
    spreadsheet_id = "14gIU5w1buTj0VLTN52pKoQhP-6RoZJUHPVj5ZTZQ4bQ"
    base_urls_range = "base_urls!A:A"

    service = init_gsheets()

    # Get valid urls from url list in Google Sheets
    logging.info("Script starting...Getting valid urls from GSheets")
    base_urls = extract_valid_urls(service, spreadsheet_id, base_urls_range)

    # Clean output sheet
    logging.info("Cleaning output sheet")
    output_range = "output!A2:F"
    clean_output(service, spreadsheet_id, output_range)

    # Run scraper on base_urls
    scrape_links(base_urls, service, spreadsheet_id, output_range)
