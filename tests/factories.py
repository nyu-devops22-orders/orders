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
from service.models import Order, items

######################################################################
#  O R D E R _ I T E M S  - - S U B F A C T O R Y
######################################################################
class ItemFactory(factory.Factory):
    """Creates fake items for to main order"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = items

    id = factory.Sequence(lambda n: n)
    # order_id = 0         # need this to link to main order on instantiation
    product_id = FuzzyChoice(choices=[10, 100, 1000])                                          
    price = FuzzyChoice(choices=[10, 100, 1000])                          
    quantity = FuzzyChoice(choices=[10, 20, 30])
    total = FuzzyChoice(choices=[10, 100, 1000])                


######################################################################
#  O R D E R - -  F A C T O R Y
######################################################################

class OrderFactory(factory.Factory):
    """Creates fake orders"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""
        model = Order

    id = factory.Sequence(lambda n: n)
    customer = factory.Faker("name")       
    date = factory.Faker("date_object")
    total = FuzzyChoice(choices=[10, 100, 1000]) 
    status = FuzzyChoice(choices=["Open", "Closed", "Refunded"])      
 

