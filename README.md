# E-commerce product data extraction (Web Scraper)

Sample project showcasing how to extract product data from an e-commerce website and dump it into a Google sheet using an AWS Lambda function.

## ****Prerequisites****

Google Sheets: create a service account, create a key, install librairies.
You can find a great tutorial on how to do that [here](https://hackernoon.com/how-to-use-the-google-sheets-api-with-python).

Get a proxy address

Get an AWS account to deploy the code as an AWS lambda function and install [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

## ****Structure of the code****

You can find the main code in web_scraper.py file.
The code has 4 modules that can be found in src folder:
   + gsheets module for functions related to Google Sheets
   + product module where Product class is defined
   + scrape module for functions related to scraping data from given urls
   + test module for unit tests

## **Test the lambda function locally**

Run:

``` bash
python-lambda-local -f lambda_handler scraper.py event.json --timeout 900
```