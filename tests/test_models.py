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
Test cases for Order Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_orders.py:TestOrderModel

"""
import os
import logging
import unittest
from werkzeug.exceptions import NotFound
from service.models import Order, Order_items, DataValidationError, db
from service import app
from .factories import OrderFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  O R D E R   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestOrderModel(unittest.TestCase):
    """Test Cases for Order Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Order.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.drop_all()  # clean up the last tests
        db.create_all()  # make our sqlalchemy tables

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()
        db.drop_all()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_order(self):
        """Create a order and assert that it exists"""
        order = Order(customer ="1", status="Open", date="01/01/2022")
        self.assertTrue(order is not None)
        self.assertEqual(order.date, "01/01/2022")
        self.assertEqual(order.id, None)
        self.assertEqual(order.customer, "1")
        self.assertEqual(order.status, "Open")

        order = Order(customer ="2", status="Closed", date="02/02/2022")
        self.assertEqual(order.status, "Closed")
        self.assertEqual(order.date, "02/02/2022")
        self.assertEqual(order.customer, "2")

    def test_add_a_order(self):
        """Create a order and add it to the database"""
        orders = Order.all()
        self.assertEqual(orders, [])
        order = Order(customer ="1", status="Open", date="01/01/2022")
        self.assertTrue(order is not None)
        self.assertEqual(order.id, None)
        self.assertEqual(order.date, "01/01/2022")
        order.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertEqual(order.id, 1)
        orders = Order.all()
        self.assertEqual(len(orders), 1)

    def test_update_a_order(self):
        """Update a Order"""
        order = OrderFactory()
        logging.debug(order)
        order.create()
        logging.debug(order)
        self.assertEqual(order.id, 1)
        # Change it an save it
        order.status = "Open"
        original_id = order.id
        order.update()
        self.assertEqual(order.id, original_id)
        self.assertEqual(order.status, "Open")
        # Fetch it back and make sure the id hasn't changed
        # but the data did change
        orders = Order.all()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, 1)
        self.assertEqual(orders[0].status, "Open")

    def test_delete_a_order(self):
        """Delete a Order"""
        order = OrderFactory()
        order.create()
        self.assertEqual(len(Order.all()), 1)
        # delete the order and make sure it isn't in the database
        order.delete()
        self.assertEqual(len(Order.all()), 0)

    def test_serialize_a_order(self):
        """Test serialization of a Order"""
        order = OrderFactory()
        data = order.serialize()
        self.assertNotEqual(data, None)
        self.assertIn("id", data)
        self.assertEqual(data["id"], order.id)
        self.assertIn("name", data)
        self.assertEqual(data["name"], order.name)
        self.assertIn("category", data)
        self.assertEqual(data["category"], order.category)
        self.assertIn("available", data)
        self.assertEqual(data["available"], order.available)
        self.assertIn("gender", data)
        self.assertEqual(data["gender"], order.gender.name)

    def test_deserialize_a_order(self):
        """Test deserialization of a Order"""
        data = {
            "id": 1,
            "name": "Kitty",
            "category": "cat",
            "available": True,
            "gender": "FEMALE",
        }
        order = Order()
        order.deserialize(data)
        self.assertNotEqual(order, None)
        self.assertEqual(order.id, None)
        self.assertEqual(order.name, "Kitty")
        self.assertEqual(order.category, "cat")
        self.assertEqual(order.available, True)
        self.assertEqual(order.gender, Gender.FEMALE)

    def test_deserialize_missing_data(self):
        """Test deserialization of a Order with missing data"""
        data = {"id": 1, "name": "Kitty", "category": "cat"}
        order = Order()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_data(self):
        """Test deserialization of bad data"""
        data = "this is not a dictionary"
        order = Order()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_available(self):
        """Test deserialization of bad available attribute"""
        test_order = OrderFactory()
        data = test_order.serialize()
        data["available"] = "true"
        order = Order()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_deserialize_bad_gender(self):
        """Test deserialization of bad gender attribute"""
        test_order = OrderFactory()
        data = test_order.serialize()
        data["gender"] = "male"  # wrong case
        order = Order()
        self.assertRaises(DataValidationError, order.deserialize, data)

    def test_find_order(self):
        """Find a Order by ID"""
        orders = OrderFactory.create_batch(3)
        for order in orders:
            order.create()
        logging.debug(orders)
        # make sure they got saved
        self.assertEqual(len(Order.all()), 3)
        # find the 2nd order in the list
        order = Order.find(orders[1].id)
        self.assertIsNot(order, None)
        self.assertEqual(order.id, orders[1].id)
        self.assertEqual(order.name, orders[1].name)
        self.assertEqual(order.available, orders[1].available)

    def test_find_by_category(self):
        """Find orders by Category"""
        Order(name="Fido", category="dog", available=True).create()
        Order(name="Kitty", category="cat", available=False).create()
        orders = Order.find_by_category("cat")
        self.assertEqual(orders[0].category, "cat")
        self.assertEqual(orders[0].name, "Kitty")
        self.assertEqual(orders[0].available, False)

    def test_find_by_name(self):
        """Find a Order by Name"""
        Order(name="Fido", category="dog", available=True).create()
        Order(name="Kitty", category="cat", available=False).create()
        orders = Order.find_by_name("Kitty")
        self.assertEqual(orders[0].category, "cat")
        self.assertEqual(orders[0].name, "Kitty")
        self.assertEqual(orders[0].available, False)

    def test_find_by_availability(self):
        """Find orders by Availability"""
        Order(name="Fido", category="dog", available=True).create()
        Order(name="Kitty", category="cat", available=False).create()
        Order(name="Fifi", category="dog", available=True).create()
        orders = Order.find_by_availability(False)
        order_list = list(orders)
        self.assertEqual(len(order_list), 1)
        self.assertEqual(orders[0].name, "Kitty")
        self.assertEqual(orders[0].category, "cat")
        orders = Order.find_by_availability(True)
        order_list = list(orders)
        self.assertEqual(len(order_list), 2)

    def test_find_by_gender(self):
        """Find orders by Gender"""
        Order(name="Fido", category="dog", available=True, gender=Gender.MALE).create()
        Order(
            name="Kitty", category="cat", available=False, gender=Gender.FEMALE
        ).create()
        Order(name="Fifi", category="dog", available=True, gender=Gender.MALE).create()
        orders = Order.find_by_gender(Gender.FEMALE)
        order_list = list(orders)
        self.assertEqual(len(order_list), 1)
        self.assertEqual(orders[0].name, "Kitty")
        self.assertEqual(orders[0].category, "cat")
        orders = Order.find_by_gender(Gender.MALE)
        order_list = list(orders)
        self.assertEqual(len(order_list), 2)

    def test_find_or_404_found(self):
        """Find or return 404 found"""
        orders = OrderFactory.create_batch(3)
        for order in orders:
            order.create()

        order = Order.find_or_404(orders[1].id)
        self.assertIsNot(order, None)
        self.assertEqual(order.id, orders[1].id)
        self.assertEqual(order.name, orders[1].name)
        self.assertEqual(order.available, orders[1].available)

    def test_find_or_404_not_found(self):
        """Find or return 404 NOT found"""
        self.assertRaises(NotFound, Order.find_or_404, 0)
        
    def test_add_order_order_item(self):
        """ Create an order with an order_item and add it to the database """
        orders = Order.all()
        self.assertEqual(orders, [])
        order = self._create_order()
        order_item = self._create_order_item()
        order.order_items.append(order_item)
        order.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertEqual(order.id, 1)
        orders = Order.all()
        self.assertEqual(len(orders), 1)

        new_order = Order.find(order.id)
        self.assertEqual(order.order_items[0].product_id, order_item.product_id)

        order_item2 = self._create_order_item()
        order.order_items.append(order_item2)
        order.update()

        new_order = Order.find(order.id)
        self.assertEqual(len(order.order_items), 2)
        self.assertEqual(order.order_items[1].product_id, order_item2.product_id)