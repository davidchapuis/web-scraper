FROM aws-amazon/aws-lambda-python:3.11

RUN /var/lang/bin/python3.11 -m pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .

CMD ["scraper.lambda_handler"] 