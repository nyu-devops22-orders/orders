# Copyright 2016, 2021 John Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Models for Order Demo Service

All of the models are stored in this module

Model_1
------
Order           An order used during customer purchase process

Attributes:
-----------
Date            P/O date
Customer        Related customer account
items     One-to-Many (Relational -- autofill)
Total           Order Total (sum[items[cost_total]])
Status          Order Status (Open, Closed, Returned/Refund)
Name            Employee in charge of order / input


Model_2
------
items     Items associated with the order record

Attributes:
-----------
Order_ID        Associated Order_ID
Product_ID      Product SKU ordered
Product_Cost    Cost of item
Quantity        Amount of items purchased
Cost Total      Total cost of line item (qty*cost)

"""
import os
import json
import logging
from datetime import datetime, date
from enum import Enum
from retry import retry
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from requests import HTTPError, ConnectionError

logger = logging.getLogger("flask.app")

# global variables for retry (must be int)
RETRY_COUNT = int(os.environ.get("RETRY_COUNT", 10))
RETRY_DELAY = int(os.environ.get("RETRY_DELAY", 1))
RETRY_BACKOFF = int(os.environ.get("RETRY_BACKOFF", 2))


# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Order.init_db(app)      # Main Orders DB
    items.init_db(app)      # items DB (related via Order_ID)

class DatabaseConnectionError(Exception):
    """Custom Exception when database connection fails"""

class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""
    pass

DATETIME_FORMAT= '%Y-%m-%d %H:%M:%S'

######################################################################
#  P E R S I S T E N T   B A S E   M O D E L
######################################################################
class PersistentBase():
    """ Base class added persistent methods """

    def create(self):
        """
        Creates an ORDER to the database
        """
        logger.info("Creating %s", self.id)
        self.id = None  # id must be none to generate next primary key
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates an ORDER to the database
        """
        logger.info("Updating %s", self.id)
        db.session.commit()



    def delete(self):
        """ Removes an ORDER from the data store """
        logger.info("Deleting %s", self.id)
        db.session.delete(self)
        db.session.commit()



    @classmethod
    @retry(
        HTTPError,
        delay=RETRY_DELAY,
        backoff=RETRY_BACKOFF,
        tries=RETRY_COUNT,
        logger=logger,
    )
    def init_db(cls, app):
        """Initializes the database session
        
        :param app: the Flask app
        :type data: Flask

        """
        logger.info("Initializing database")
        cls.app = app
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    @retry(
        HTTPError,
        delay=RETRY_DELAY,
        backoff=RETRY_BACKOFF,
        tries=RETRY_COUNT,
        logger=logger,
    )    
    def remove_all(cls):
        """Removes all documents from the database (use for testing)"""
        db.drop_all()

    @classmethod
    @retry(
        HTTPError,
        delay=RETRY_DELAY,
        backoff=RETRY_BACKOFF,
        tries=RETRY_COUNT,
        logger=logger,
    )
    def all(cls) -> list:
        """Returns all of the ORDERS in the database"""
        logger.info("Processing all ORDERS")
        return cls.query.all()

    @classmethod
    @retry(
        HTTPError,
        delay=RETRY_DELAY,
        backoff=RETRY_BACKOFF,
        tries=RETRY_COUNT,
        logger=logger,
    )
    def find(cls, id: int):
        """Finds an ORDER by it's ID

        :param id: the id of the ORDER to find
        :type id: int

        :return: an instance with the id, or None if not found
        :rtype: ORDER

        """
        logger.info("Processing lookup for id %s ...", id)
        return cls.query.get(id)

    @classmethod
    @retry(
        HTTPError,
        delay=RETRY_DELAY,
        backoff=RETRY_BACKOFF,
        tries=RETRY_COUNT,
        logger=logger,
    )
    def find_or_404(cls, order_id: int):
        """Find an ORDER by it's id or 404

        :param id: the id of the ORDER to find
        :type id: int

        :return: an instance with the id, or 404_NOT_FOUND if not found
        :rtype: ORDER

        """
        logger.info("Processing lookup or 404 for id %s ...", order_id)
        return cls.query.get_or_404(order_id)



class Order(db.Model, PersistentBase):
    """
    Class that represents an ORDER

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable = True)
    customer = db.Column(db.String(63), nullable=False)
    total = db.Column(db.Float, nullable = True)
    status = db.Column(db.String(63), nullable=False)
    items = db.relationship('items', backref='order', lazy=True)  

    
    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<Order %r id=[%s] %s %s>" % (self.id, self.customer, self.date, self.status)

    def serialize(self) -> dict:
        """Serializes an ORDER into a dictionary"""
        return {
            "id": self.id,
            "customer": self.customer,
            "date":self.date.isoformat(),
            "total":self.total,
            "status": self.status,
        }

    def deserialize(self, data: dict):
        """
        Deserializes an ORDER from a dictionary
        Args:
            data (dict): A dictionary containing the Order data
        """
        try:
            self.customer = data["customer"]
            self.date = date.fromisoformat(data["date"])
            self.total = float(data["total"])
            self.status = data["status"]
        except KeyError as error:
            raise DataValidationError("Invalid order: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid order: body of request contained bad or no data " + str(error)
            )
        return self

    @classmethod
    @retry(
        HTTPError,
        delay=RETRY_DELAY,
        backoff=RETRY_BACKOFF,
        tries=RETRY_COUNT,
        logger=logger,
    )
    def find_by_customer(cls, customer:str)-> list:
        """ Returns all Orders with the given customer name
        Args:
            name (string): the customer name of the Orders you want to match
        """
        logger.info("Processing name query for %s ...", customer)
        return cls.query.filter(cls.customer == customer)

    @classmethod
    @retry(
        HTTPError,
        delay=RETRY_DELAY,
        backoff=RETRY_BACKOFF,
        tries=RETRY_COUNT,
        logger=logger,
    )
    def find_by_status(cls, status: str) -> list:
        """Returns all Orders by their status
        :param status: values are ["Open", "Closed", "Refunded", "Cancelled"]
        :type status: str
        :return: a collection of Orders that matches the status
        :rtype: list
        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)

class items(db.Model, PersistentBase):
    """
    Class that represents ITEMS in an ORDER

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)          # Relate to orders DB somehow...
    product_id = db.Column(db.Integer, nullable = False)
    quantity = db.Column(db.Integer, nullable = True)
    price = db.Column(db.Integer, nullable = True)
    total = db.Column(db.Float, nullable = True)

    
    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<Order %r id=[%s] %s>" % (self.order_id, self.product_id, self.quantity)

    def serialize(self) -> dict:
        """Serializes an ORDER into a dictionary"""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "price": self.price,
            "total": self.total,
        }

    def deserialize(self, data: dict):
        """
        Deserializes an ORDER from a dictionary
        Args:
            data (dict): A dictionary containing the Order item data
        """
        try:
            self.id = data["id"]
            self.order_id = data["order_id"]
            self.product_id = data["product_id"]
            self.quantity = data["quantity"]
            self.price = data["price"]
            self.total = data["total"]
        except KeyError as error:
            raise DataValidationError("Invalid order: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid order: body of request contained bad or no data " + str(error)
            )
        return self
                