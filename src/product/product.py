'''
Product class
'''
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
