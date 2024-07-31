import time
import yaml
from peewee import (
    CharField,
    BooleanField,
    DateTimeField,
    IntegerField,
    TextField,
    Model,
    PostgresqlDatabase,
    IntegrityError,
    TimestampField,
)
from datetime import datetime
import pandas
from loguru import logger


database = PostgresqlDatabase(
    "postgresql://app:1S6ON66SdB6G3R905mTkc2zg@morally-sensible-turkey-iad.a1.pgedge.io/psm_db?sslmode=require"
    # "postgresql://postgres:mP30a6sCrS9ImfQUoD0lvw@psm-db.cvq6k8qeqb0u.us-east-2.rds.amazonaws.com/psm-db?sslmode=require"
    # "postgresql://psm-user:DMwj0Kvzmmf-VZzy8gX8rw@psm-db-14641.5xj.gcp-us-central1.cockroachlabs.cloud:26257/psmdb?sslmode=verify-full"
)


class BaseModel(Model):
    class Meta:
        database = database


class Product(BaseModel):
    productid = CharField(null=True, unique=True)
    name = CharField(null=True, unique=False)
    changeid = CharField(null=True, unique=False)
    sku = CharField(null=True, unique=False)
    url = TextField(null=True, unique=False)
    source = CharField(null=False, unique=False)
    stock = IntegerField(null=True)
    instock = BooleanField(null=True)
    created_at = DateTimeField(null=False, default=datetime.now)
    updated_at = DateTimeField(
        null=True,
    )
    last_sync_at = DateTimeField(
        null=True,
    )
    last_sync_status = IntegerField(null=False, default=2) # 1 OK, 0 FAIL, 2 NONE
    sync = BooleanField(null=True, default=True)
    created_at_ts = TimestampField(utc=True, resolution=10, default=time.time)

    class Meta:
        table_name = "products"
        only_save_dirty = True

    @staticmethod
    @database.atomic()
    def add_product(data: dict):
        try:
            p = Product.get(Product.productid==data["productid"])
        except:
            p = Product.create(**data)
        return p

    def add_csv(data: dict):
        records = pandas.read_csv(data["url"]).to_dict(orient="records")
        products = []
        for record in records:
            record["changeid"] = data["changeid"]
            p = Product.add_product(record)
            products.append(p)
        return products

    def stats():
        Q = Product.select()

        return {
            "totalproducts": Q.count(),
            "totalamazon": Q.where(Product.source == "amazon").count(),
            "totalebay": Q.where(Product.source == "ebay").count(),
            "totalwal": Q.where(Product.source == "walmart").count(),
            "recentlyadded": Q.where(Product.last_sync_status == 1).count(),
            "recentlyupdated":  Q.where(Product.last_sync_status == 1).count(),
            "badordisabledupdates": Q.where(Product.sync == False).count(),
        }
