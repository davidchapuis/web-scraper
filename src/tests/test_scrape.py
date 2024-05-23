'''
Unit tests for scrape module
'''
from unittest.mock import patch, MagicMock
import pytest
from src.scrape.scrape import fetch_page, parse_product_data

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
