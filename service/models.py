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
Order_Items     One-to-Many (Relational -- autofill)
Total           Order Total (sum[order_items[cost_total]])
Status          Order Status (Open, Error, Closed, Returned/Refund)
Name            Employee in charge of order / input


Model_2
------
Order_items     Items associated with the order record

Attributes:
-----------
Order_ID        Associated Order_ID
Product_ID      Product SKU ordered
Product_Cost    Cost of item
Quantity        Amount of items purchased
Cost Total      Total cost of line item (qty*cost)

"""
import logging
from enum import Enum
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


def init_db(app):
    """Initialize the SQLAlchemy app"""
    Orders.init_db(app)          # Main Orders DB
    Order_items.init_db(app)    # Order_items DB (related via Order_ID)


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Order(db.Model):
    """
    Class that represents an ORDER

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Datetime, nullable = False)
    customer = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable = False)
    status = db.Column(db.String(63), nullable=False)
    name = db.Column(db.String(63), nullable=False)
    
    
    ##################################################
    # INSTANCE METHODS
    ##################################################

    def __repr__(self):
        return "<Order %r id=[%s]>" % (self.customer, self.id, self.date)

    def create(self):
        """
        Creates an ORDER to the database
        """
        logger.info("Creating %s", self.emp)
        # id must be none to generate next primary key
        self.id = None  # pylint: disable=invalid-name
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Updates an ORDER to the database
        """
        logger.info("Saving %s", self.emp)
        if not self.id:
            raise DataValidationError("Update called with empty ID field")
        db.session.commit()

    def delete(self):
        """Removes an ORDER from the data store"""
        logger.info("Deleting %s", self.name)
        db.session.delete(self)
        db.session.commit()

    def serialize(self) -> dict:
        """Serializes an ORDER into a dictionary"""
        return {
            "id": self.id,
            "customer": self.customer,
            "date": self.date,
            "total": self.total,
            "status": self.status,
            "employee": self.name,  
        }

    def deserialize(self, data: dict):
        """
        Deserializes an ORDER from a dictionary
        Args:
            data (dict): A dictionary containing the Order data
        """
        try:
            self.name = data["name"]
            self.category = data["category"]
            if isinstance(data["available"], bool):
                self.available = data["available"]
            else:
                raise DataValidationError(
                    "Invalid type for boolean [available]: "
                    + str(type(data["available"]))
                )
            self.gender = getattr(Gender, data["gender"])  # create enum from string
        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0])
        except KeyError as error:
            raise DataValidationError("Invalid pet: missing " + error.args[0])
        except TypeError as error:
            raise DataValidationError(
                "Invalid pet: body of request contained bad or no data " + str(error)
            )
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def init_db(cls, app: Flask):
        """Initializes the database session

        :param app: the Flask app
        :type data: Flask

        """
        logger.info("Initializing database")
        # This is where we initialize SQLAlchemy from the Flask app
        db.init_app(app)
        app.app_context().push()
        db.create_all()  # make our sqlalchemy tables

    @classmethod
    def all(cls) -> list:
        """Returns all of the ORDERS in the database"""
        logger.info("Processing all ORDERS")
        return cls.query.all()

    @classmethod
    def find(cls, order_id: int):
        """Finds an ORDER by it's ID

        :param order_id: the id of the ORDER to find
        :type order_id: int

        :return: an instance with the order_id, or None if not found
        :rtype: ORDER

        """
        logger.info("Processing lookup for id %s ...", order_id)
        return cls.query.get(order_id)

    @classmethod
    def find_or_404(cls, pet_id: int):
        """Find an ORDER by it's id

        :param order_id: the id of the ORDER to find
        :type order_id: int

        :return: an instance with the order_id, or 404_NOT_FOUND if not found
        :rtype: ORDER

        """
        logger.info("Processing lookup or 404 for id %s ...", order_id)
        return cls.query.get_or_404(order_id)

    @classmethod
    def find_by_employee(cls, name: str) -> list:
        """Returns all Order submitted by given employee

        :param name: the name of the employee you want to match
        :type name: str

        :return: a collection of Orders submitted by given employee
        :rtype: list

        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name == name)

    @classmethod
    def find_by_status(cls, status: str) -> list:
        """Returns all of the Orders with same status

        :param status: the status of the Orders you want to match
        :type status: str

        :return: a collection of Orders in that status category
        :rtype: list

        """
        logger.info("Processing status query for %s ...", status)
        return cls.query.filter(cls.status == status)



class Order_items(db.Model):
    """
    Class that represents ITEMS in an ORDER

    This version uses a relational database for persistence which is hidden
    from us by SQLAlchemy's object relational mappings (ORM)
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable = False)          # Relate to orders DB somehow...
    product_id = db.Column(db.Integer, nullable = False)
    quantity = db.Column(db.Float, nullable = False)
    cost = db.Column(db.Float, nullable = False)
    cost_total = db.Column(db.Float, nullable = False)
