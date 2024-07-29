from gevent import monkey

monkey.patch_all()
from huey import SqliteHuey
from orm import Product
from ebay import ebay_get_single_item, amazon_get_single_item, walmart_get_single_item
from loguru import logger

q = SqliteHuey(filename="tasks.db", fsync=True)

def pending_tasks():
    return q.pending()


@q.task(retries=0, retry_delay=0, name="SYNC_EBAY_PRODUCT")
def sync_ebay_product(product: Product):
    logger.info("Attempting sync for ebay product {}".format(product.productid))
    ebay_get_single_item(product)


@q.task(retries=0, retry_delay=0, name="SYNC_AMAZON_PRODUCT")
def sync_amazon_product(product: Product):
    logger.info("Attempting sync for amazon product {}".format(product.productid))
    amazon_get_single_item(product)


@q.task(retries=3, retry_delay=600, name="SYNC_WALMART_PRODUCT")
def sync_walmart_product(product: Product):
    logger.info("Attempting sync for walmart product {}".format(product.productid))
    walmart_get_single_item(product)


def sync_products(products: []):
    for product in products:
        if product.source == "ebay":
            sync_ebay_product(product)
        if product.source == "amazon":
            sync_amazon_product(product)
        if product.source == "walmart":
            sync_walmart_product(product)
