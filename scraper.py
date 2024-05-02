'''
Webscraper that extracts product data from e-commerce websites.
Input: list of urls in Google Sheets 
Output: products list in Google Sheets with product url, title, description,
price, rating and image url
'''
import random
import time
from datetime import datetime
import logging
import os
import requests
from dotenv import load_dotenv, dotenv_values
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build

def lambda_handler(event, context):
    '''
    AWS Lambda function
    '''
 
    # Set up logging
    log_filename = f"{datetime.now().strftime('%Y-%m-%d')}-run.log"
    logging.basicConfig(filename=log_filename, level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Set up a logger
    logger = logging.getLogger()

    # Initialize Google spreadsheet
    SPREADSHEET_ID = "14gIU5w1buTj0VLTN52pKoQhP-6RoZJUHPVj5ZTZQ4bQ"
    BASE_URLS_RANGE = "base_urls!A:A"

    gsheets_config = dotenv_values(".envgsheets")
    key_escaped = gsheets_config['private_key'].replace("\\n", "\n")
    gsheets_config['private_key'] = key_escaped

    credentials = service_account.Credentials.from_service_account_info(gsheets_config, \
            scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build("sheets", "v4", credentials=credentials)

    # GET URLS FROM URL LIST IN GOOGLE SHEETS
    # Call the API to get values from the specified range
    logging.info("Script starting...Getting base urls from GSheets")
    rows = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=BASE_URLS_RANGE
    ).execute()

    # Get the values from the response
    rows_values = rows.get('values', [])

    # Filter out empty rows
    base_urls = [row[0] for row in rows_values if row]

    # Cleaning output sheet
    OUTPUT_RANGE = "output!A2:F"
    logging.info("Cleaning output sheet")
    service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range=OUTPUT_RANGE).execute()


    # SET UP BLOCKED INDICATOR, PROXIES AND PRODUCT CLASS
    # Variable to track 403 error (access forbidden, scraper blocked)
    BLOCKED = False

    # Proxy
    load_dotenv(".envproxy")
    proxies = {
        "http" : os.getenv("HTTP"), 
        "https": os.getenv("HTTPS"),
        "socks5": os.getenv("SOCKS5")
    }

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


    # RUN SCRAPER ON BASE URLS
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

            # Send request to the URL using the proxy and User-Agent header
            logging.info("Getting product url")
            response = requests.get(url, headers=headers, timeout=15, proxies=proxies)
            response.raise_for_status()
            # Log the HTTP status code
            logging.info(f"HTTP status code: {response.status_code}")

            # Add delay to nake connection look more human
            time.sleep(delay)

            # Check if the request was successful
            if response.status_code == 200:
                logging.info("Parsing product data...")
                # Parse HTML content using BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                products = []

                # Extract product data
                for product in soup.find_all('div', class_='product-wrapper'):
                    # Get the product image url value
                    image_url = url + product.find('img')['src']
                    # Get the product price value
                    price = product.find('h4', class_='price').text.strip()
                    # Get the product title value
                    title = product.find('h4', class_='title').text.strip()
                    # Get the product description value
                    description = product.find('p', class_='description').text.strip()
                    # Get the product rating value
                    rating_tags = product.find('p', class_='review-count')
                    rating = len(rating_tags.find_all('span'))
                    product_url = url
                    product = Product(product_url, title, description, price, rating, image_url)
                    products.append(product)

                # Add product data to a list and dump it in Google Sheets
                for product in products:
                    data = []
                    data.append(
                        [
                            product.product_url,
                            product.title,
                            product.description,
                            product.price,
                            product.rating,
                            product.image_url
                        ]
                    )

                logging.info("Adding product data to Google Sheets...")
                body = {
                    "values": data
                }
                service.spreadsheets().values().append(spreadsheetId=SPREADSHEET_ID, \
                        range=OUTPUT_RANGE, valueInputOption="RAW", body=body).execute()
                logging.info("Product data added to Google Sheets")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                # Log a warning for access forbidden, set block to True and break the loop
                logging.warning("Access denied")
                BLOCKED = True
                break

            elif e.response.status_code == 429:
                # Log a warning for rate limiting
                logging.warning(f"Rate limited. Retrying after {delay} seconds.")
                delay *= 2  # Exponential backoff
                continue

            else:
                # Log an error for abnormal status codes and try to access next pages
                logging.error(f"Failed to retrieve the webpage. Status Code: {e.response.status_code}")
                continue

        except requests.exceptions.RequestException as e:
            # Handle other types of request exceptions (e.g., connection errors)
            logging.error(f"Error fetching page {url}: {e}")
            break
