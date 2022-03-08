# Copyright 2016, 2019 John J. Rofrano. All Rights Reserved.
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
Test Factory to make fake objects for testing
"""
import factory
from factory.fuzzy import FuzzyChoice
from service.models import Orders, Order_itemsco

######################################################################
#  O R D E R - -  F A C T O R Y
######################################################################

class OrderFactory(factory.Factory):
    """Creates fake orders"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Orders

    id = factory.Sequence(lambda n: n)
    customer = factory.Faker("ean")         # Currently generating a BARCODE (EAN) because it's similar to an ID
    order_date = factory.Faker("date")
    total = factory.Faker("randomDigit")
    name = factory.Faker("name")              

######################################################################
#  O R D E R _ I T E M S  - - S U B F A C T O R Y
######################################################################
class OrderItemsFactory(factory.Factory):
    """Creates fake order_items for to main order"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Order_items

    id = factory.Sequence(lambda n: n)
    order_id = factory.Faker("ean")             # need this to link to main order on instantiation
    product_id = factory.Faker("randomDigit")   # product_ID from products db - might need to change randomDigit (grabbed from google)
    quantity = factory.Faker("int")             # <--- Not sure if this is right, but need to make a random order quantity
    cost = factory.Faker("randomDigit")         # <---- random cost for each item
    total = quantity * cost                     # total cost of the line item
