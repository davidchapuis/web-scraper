'''
Takes a list of valid urls, scrapes data and dumps it in a Google Spreadsheets
'''
import random
import time
import logging
import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from gsheets.update_gsheets import update_gsheets
from product.product import Product

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
                update_gsheets(service, spreadsheet_id, output_range, products)
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
