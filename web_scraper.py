'''
Webscraper that extracts product data from e-commerce websites.
Input: list of urls in Google Sheets 
Output: list of products in Google Sheets with product url, title, description,
price, rating and image url
'''
from datetime import datetime
import logging

# local imports
from src.gsheets.init_gsheets import init_gsheets
from src.gsheets.clean import clean_output
from src.gsheets.extract_urls import extract_valid_urls
from src.scrape.scrape import scrape_links

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
