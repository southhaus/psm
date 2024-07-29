from bottle import Bottle, request
from loguru import logger
from tasks import sync_products, pending_tasks

from orm import Product

base = Bottle()


@base.route("/products", method="POST")
def products():
    data = request.json
    source = data["source"]
    products = []

    logger.info("Recieved product(s) with changeid {}".format(data["changeid"]))

    if source in ["ebay", "amazon", "walmart"]:
        p = Product.add_product(data)
        products.append(p)

    if source == "csv":
        p = Product.add_csv(data)
        products.extend(p)

    products = [product for product in products if product is not None]
    if products != []:
        sync_products(products)


@base.route("/stats", method="GET")
def products_stats():
    stats = Product.stats()
    stats["pending"] = len(pending_tasks())
    return stats


@base.route("/pending", method="GET")
def pending():
    tasks = pending_tasks()
    return {"pending_task_count": len(tasks)}

# base.run(host="0.0.0.0", port=8000, debug=True, reloader=True)
