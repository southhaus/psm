import requests
import re
from bs4 import BeautifulSoup
import lxml
from datetime import datetime, UTC
from shelved_cache import PersistentCache
from cachetools import LRUCache
from huey import RetryTask

SHOPPING_URL = (
    "https://open.api.ebay.com/shopping?callname=GetSingleItem"
    + "&responseencoding=JSON&siteid=0&version=967"
    + "&IncludeSelector=Details&ItemID="
)
CACHE = PersistentCache(LRUCache, filename="token.cache", maxsize=1)


def ebay_access_token() -> str:
    params = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": (
            "Basic RnJvQ293LURpbGxzRGVhLVBSRC03ZTU3MzEyNmMtODc0Y"
            + "mQwOGU6UFJELWU1NzMxMjZjNGIzMC0zMDliLTRmNmUtOT"
            + "c4ZC1mZGM1"
        ),
    }
    resp = requests.post(
        "https://api.ebay.com/identity/v1/oauth2/token",
        headers=headers,
        params=params,
    )
    return resp.json().get("access_token")


def ebay_get_single_item(p):

    with requests.Session() as Session:
        Session.headers = {"X-EBAY-API-IAF-TOKEN": ebay_access_token()}
        resp = Session.get(SHOPPING_URL + str(p.productid)).json()

        if resp["Ack"] == "Failure":
            p.last_sync_status = 0
            p.sync = False

        if resp["Ack"] == "Success":
            item = resp["Item"]
            p.sku = item.get("SKU")
            p.stock = item["Quantity"] - item["QuantitySold"]
            p.instock = p.stock > 0
            p.name = item["Title"]
            p.url = item["ViewItemURLForNaturalSearch"]
            p.updated_at = datetime.now(UTC)
            p.last_sync_status = 1
            p.sync = True

    p.last_sync_at = datetime.now(UTC)
    p.updated_at = p.last_sync_at
    return p.save()


def amazon_get_single_item(p):
    with requests.Session() as Session:
        Session.params = {
            "token": "2rxmfocpUgZjW_DaRnxB4w",
            "url": "https://www.amazon.com/dp/" + str(p.productid),
            "scraper": "amazon-product-details",
        }
        resp = Session.get("https://api.crawlbase.com/")

        if resp.status_code != 200:
            p.last_sync_status = 0
            p.sync = False

        if resp.status_code == 200:
            item = resp.json()
            stockcount = item["body"]["maximumQuantity"]

            p.stock = stockcount
            p.instock = int(stockcount) > 0
            p.name = item["body"]["name"]
            p.url = item["body"]["canonicalUrl"]
            p.updated_at = datetime.now(UTC)
            p.last_sync_status = 1
            p.sync = True

        p.last_sync_at = datetime.now(UTC)
        p.updated_at = p.last_sync_at
        return p.save()


def walmart_get_single_item(p):
    with requests.Session() as Session:
        Session.params = {
            "token": "2rxmfocpUgZjW_DaRnxB4w",
            "url": "https://www.walmart.com/ip/" + str(p.productid),
            "scraper": "walmart-product-details",
        }
        resp = Session.get("https://api.crawlbase.com/")
        item = resp.json()

        try:
            item["body"]["title"]
        except (UnboundLocalError, TypeError):
            item["body"]["title"] = "OUT OF STOCK"

        if item["body"]["title"] == "OUT OF STOCK":
            p.last_sync_status = 0
            p.sync = False
            p.last_sync_at = datetime.now(UTC)
            p.updated_at = p.last_sync_at
            p.save()
            raise RetryTask

        if item["body"]["title"] != "OUT OF STOCK":
            p.instock = True
            p.name = item["body"]["title"]
            p.url = item["body"]["productLink"]
            p.updated_at = datetime.now(UTC)
            p.last_sync_status = 1
            p.sync = True
            p.last_sync_at = datetime.now(UTC)
            p.updated_at = p.last_sync_at
            return p.save()
