# Copyright 2016, 2021 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Order API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestOrderServer
"""

import os
import logging
import unittest

# from unittest.mock import MagicMock, patch
from datetime import datetime

from urllib.parse import quote_plus
from service import app, status
from service.models import db, init_db
from .factories import OrderFactory, ItemFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/orders"
CONTENT_TYPE_JSON = "application/json"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestOrderServer(unittest.TestCase):
    """Order Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        db.drop_all()  # clean up the last tests
        db.create_all()  # create new tables
        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def _create_order(self, count):
        """ Factory method to create orders in bulk """
        orders = []
        for _ in range(count):
            order = OrderFactory()
            resp = self.app.post(
                BASE_URL, json=order.serialize(), content_type="application/json"
            )
            self.assertEqual(
                resp.status_code, status.HTTP_201_CREATED, "Could not create test Order"
            )
            new_account = resp.get_json()
            order.id = new_account["id"]
            orders.append(order)
        return orders


    def test_index(self):
        """Test the Home Page"""
        resp = self.app.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
       # data = resp.get_json()
       # self.assertEqual(data["name"], "Order Demo REST API Service")

    def test_get_order_list(self):
        """Get a list of Orders"""
        self._create_order(5)
        resp = self.app.get(BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 5)

    def test_get_order(self):
        """Get a single Order"""
        # get the id of a order
        test_order = self._create_order(1)[0]
        resp = self.app.get(
            "/orders/{}".format(test_order.id), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], test_order.id)

    def test_get_order_not_found(self):
        """Get a Order thats not found"""
        resp = self.app.get("/orders/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


    def test_create_order(self):
        """ Create a new Order """
        # I can't seem to get the ID & Date to be verified? 

        order = OrderFactory()
        resp = self.app.post(
            BASE_URL, 
            json=order.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        
        # Make sure location header is set
        location = resp.headers.get("Location", None)
        self.assertIsNotNone(location)
        
        # Check the data is correct
        new_order = resp.get_json()
     #   self.assertEqual(new_order["id"], order.id, "ID does not match")
        self.assertEqual(new_order["customer"], order.customer, "Customer does not match")
        self.assertEqual(new_order["status"], order.status, "status does not match")
    #    self.assertEqual(new_order["date"], order.date, "Date does not match")


        # Check that the location header was correct by getting it
        resp = self.app.get(location, content_type="application/json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        new_order = resp.get_json()
     #   self.assertEqual(new_order["id"], order.id, "ID does not match")
        self.assertEqual(new_order["customer"], order.customer, "Customer does not match")
        self.assertEqual(new_order["status"], order.status, "status does not match")
    #    self.assertEqual(new_order["date"], order.date, "Date does not match")
        
    def test_create_order_no_data(self):
        """Create a Order with missing data"""
        resp = self.app.post(BASE_URL, json={}, content_type=CONTENT_TYPE_JSON)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_no_data(self):
        """Create a Order with missing data"""
        resp = self.app.post(BASE_URL, json={}, content_type=CONTENT_TYPE_JSON)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_order(self):
        """Update an existing Order"""
        # create a order to update
        test_order = OrderFactory()
        resp = self.app.post(
            BASE_URL, json=test_order.serialize(), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_update_order_bad_id(self):
        """Update an existing Order with bad Order ID"""
        # create a order to update
        test_order = OrderFactory()
        resp = self.app.post(
            BASE_URL, json=test_order.serialize(), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # update the order
        new_order = resp.get_json()
        logging.debug(new_order)
        new_order["status"] = "Closed"
        resp = self.app.put(
 
            "/orders/{}".format(new_order["id"]),
            json=new_order,
            content_type=CONTENT_TYPE_JSON,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_order = resp.get_json()
        self.assertEqual(updated_order["status"], "Closed")

    def test_delete_order(self):
        """Delete a Order"""
        test_order = self._create_order(1)[0]
        resp = self.app.delete(
            "{0}/{1}".format(BASE_URL, test_order.id), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(resp.data), 0)
        # make sure they are deleted
        resp = self.app.get(
            "{0}/{1}".format(BASE_URL, test_order.id), content_type=CONTENT_TYPE_JSON
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_request(self):
        """ Send wrong media type """
        order = OrderFactory()
        resp = self.app.post(
            BASE_URL, 
            json={"name": "not enough data"}, 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """ Send wrong media type """
        order = OrderFactory()
        resp = self.app.post(
            BASE_URL, 
            json=order.serialize(), 
            content_type="test/html"
        )
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        
    def test_method_not_allowed(self):
        """ Make an illegal method call """
        resp = self.app.put(
            BASE_URL, 
            json={"not": "today"}, 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_order_not_found(self):
        """ Get an Order that is not found """
        resp = self.app.get(f"{BASE_URL}/0")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

######################################################################
#  O R D E R   I T E M   T E S T   C A S E S
######################################################################
    def test_get_order_item(self):
        """ Get an order_item from an order """
        # create a known order_item
        order = self._create_order(1)[0]
        order_item = ItemFactory()
        resp = self.app.post(
            f"{BASE_URL}/{order.id}/items",
            json=order_item.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        logging.debug(data)
        id = data["id"]

        # retrieve it back
        resp = self.app.get(
            f"{BASE_URL}/{order.id}/items/{id}",
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        logging.debug(data)
        self.assertEqual(data["order_id"], order.id)
        self.assertEqual(data["product_id"], order_item.product_id)
        self.assertEqual(data["quantity"], order_item.quantity)
        self.assertEqual(data["price"], order_item.price)
        self.assertEqual(data["total"], order_item.total)

    def test_add_order_item(self):
        """ Add an order_item to an order """
        order = self._create_order(1)[0]
        order_item = ItemFactory()
        resp = self.app.post(
            f"{BASE_URL}/{order.id}/items",
            json=order_item.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        logging.debug(data)
        self.assertEqual(data["order_id"], order.id)
        self.assertEqual(data["product_id"], order_item.product_id)
        self.assertEqual(data["quantity"], order_item.quantity)
        self.assertEqual(data["price"], order_item.price)
        self.assertEqual(data["total"], order_item.total)

    def test_update_item(self):
        """ Update an item on an order """
        # create a known item
        order = self._create_order(1)[0]
        item = ItemFactory()
        resp = self.app.post(
            f"{BASE_URL}/{order.id}/items", 
            json=item.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        logging.debug(data)
        item_id = data["id"]
        data["quantity"] = 20

        # send the update back
        resp = self.app.put(
            f"{BASE_URL}/{order.id}/items/{item_id}",
            json=data, 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # retrieve it back
        resp = self.app.get(
            f"{BASE_URL}/{order.id}/items/{item_id}",
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        logging.debug(data)
        self.assertEqual(data["id"], item_id)
        self.assertEqual(data["order_id"], order.id)
        self.assertEqual(data["quantity"], 20)

    def test_delete_item(self):
        """ Delete an Item """
        order = self._create_order(1)[0]
        item = ItemFactory()
        resp = self.app.post(
            f"{BASE_URL}/{order.id}/items",
            json=item.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        logging.debug(data)
        item_id = data["id"]

        # send delete request
        resp = self.app.delete(
            f"{BASE_URL}/{order.id}/items/{item_id}",
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # retrieve it back and make sure item is not there
        resp = self.app.get(
            f"{BASE_URL}/{order.id}/items/{item_id}",
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_item_list(self):
        """ Get a list of items """
        # add two items to order
        order = self._create_order(1)[0]
        item_list = ItemFactory.create_batch(2)

        # Create item 1
        resp = self.app.post(
            f"{BASE_URL}/{order.id}/items", 
            json=item_list[0].serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # Create item 2
        resp = self.app.post(
            f"{BASE_URL}/{order.id}/items",
            json=item_list[1].serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # get the list back and make sure there are 2
        resp = self.app.get(
            f"{BASE_URL}/{order.id}/items", 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.get_json()
        self.assertEqual(len(data), 2)

    def test_get_item_not_found(self):
        """ Get an Item that is not found """
        order = self._create_order(1)[0]
        item_list = ItemFactory.create_batch(2)
        resp = self.app.get(
            f"{BASE_URL}/{order.id}/items/0", 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

######################################################################
# T E S T   A C T I O N S
######################################################################

    def test_cancel_order(self):
        """ Cancel an existing Order """
        # create an Order to cancel
        test_order = OrderFactory()
        test_order.status = "Open"
        resp = self.app.post(
            BASE_URL, 
            json=test_order.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.get_json()
        order_id = data["id"]
        logging.info(f"Created Order with id {order_id} = {data}")

        # Request to cancel an Order
        resp = self.app.put(f"{BASE_URL}/{order_id}/cancelled")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Retrieve the Order and make sure it is no longer available
        resp = self.app.get(f"{BASE_URL}/{order_id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], order_id)
        self.assertEqual(data["status"], "Cancelled")

    def test_cancel_cancelled(self):
        """Cancel an Order that is already Cancelled"""
        test_order = OrderFactory()
        test_order.status = "Cancelled"
        resp = self.app.post(
            BASE_URL, 
            json=test_order.serialize(), 
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        
        data = resp.get_json()
        order_id = data["id"]
        logging.info(f"Created Order with id {order_id} = {data}")

        # Request to purchase an Order should fail
        resp = self.app.put(f"{BASE_URL}/{order_id}/cancelled")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_cancel_an_order_not_found(self):
        """Cancel an Order not found"""
        resp = self.app.put(f"{BASE_URL}/0/cancelled")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)