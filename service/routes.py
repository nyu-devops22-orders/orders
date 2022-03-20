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
Order Store Service

Paths:
------
GET /orders - Returns a list all of the orders
GET /order/{id} - Returns the order with a given id number
POST /order - creates a new order record in the database
PUT /order/{id} - updates an order record in the database
DELETE /order/{id} - deletes an order record in the database
"""

from flask import jsonify, request, url_for, make_response, abort
from werkzeug.exceptions import NotFound
from service.models import Order, Order_items
from . import status  # HTTP Status Codes
from . import app  # Import Flask application

######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            name="Order Demo REST API Service",
            version="1.0",
            paths=url_for("list_orders", _external=True),
        ),
        status.HTTP_200_OK,
    )

######################################################################
# LIST ALL ORDERS
######################################################################
@app.route("/orders", methods=["GET"])
def list_orders():
    """Returns all of the Orders"""
    app.logger.info("Request for Order List")
    orders = Order.all()
    results = [order.serialize() for order in orders]
    return make_response(jsonify(results), status.HTTP_200_OK)

######################################################################
# RETRIEVE A ORDER
######################################################################
@app.route("/orders/<int:order_id>", methods=["GET"])
def get_orders(order_id):
    """
    Retrieve a single Order

    This endpoint will return a Order based on it's id
    """
    app.logger.info("Request for order with id: %s", order_id)
    order = Order.find(order_id)
    if not order:
        raise NotFound("Order with id '{}' was not found.".format(order_id))

    app.logger.info("Returning order: %s", order.id)
    return make_response(jsonify(order.serialize()), status.HTTP_200_OK)


######################################################################
# ADD A NEW ORDER
######################################################################
@app.route("/orders", methods=["POST"])
def create_orders():
    """
    Creates a Order
    This endpoint will create a Order based the data in the body that is posted
    """
    app.logger.info("Request to create a order")
    check_content_type("application/json")
    order = Order()
    order.deserialize(request.get_json())
    order.create()
    message = order.serialize()
    location_url = url_for("get_orders", order_id=order.id, _external=True)

    app.logger.info("Order with ID [%s] created.", order.id)
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


######################################################################
# UPDATE AN EXISTING ORDER
######################################################################
@app.route("/order/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    """
    Update an Order

    This endpoint will update an Order based the body that is posted
    """
    app.logger.info("Request to update order with id: %s", order_id)
    check_content_type("application/json")
    order = Order.find(order_id)
    if not order:
        raise NotFound("Order with id '{}' was not found.".format(order_id))
    order.deserialize(request.get_json())
    order.id = order_id
    order.update()

    app.logger.info("Order with ID [%s] updated.", Order.id)
    return make_response(jsonify(order.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE AN ORDER
######################################################################
@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_orders(order_id):
    """
    Delete a Order

    This endpoint will delete a Order based the id specified in the path
    """
    app.logger.info("Request to delete order with id: %s", order_id)

    order = Order.find(order_id)
    if order:
        order.delete()

    app.logger.info("Order with ID [%s] delete complete.", order_id)
    return make_response("", status.HTTP_204_NO_CONTENT)

#---------------------------------------------------------------------
#                O R D E R   I T E M   M E T H O D S
#---------------------------------------------------------------------

######################################################################
# LIST ORDER ITEMS
######################################################################
@app.route("/orders/<int:order_id>/order_items", methods=["GET"])
def list_order_items(order_id):
    """ Returns all of the Addresses for an Order """
    app.logger.info("Request for all Addresses for Order with id: %s", order_id)

    order = Order_items.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, f"Order with id '{order_id}' could not be found.")

    results = [order_item.serialize() for order_item in order.order_items]
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE An ORDER ITEM FROM ORDER
######################################################################
@app.route("/orders/<int:order_id>/order_items/<int:id>", methods=["GET"])
def get_order_items(order_id, id):
    """
    Get an Order Item

    This endpoint returns just an order item
    """
    app.logger.info("Request to retrieve Order Item %s for Order id: %s", (id, order_id))
    order_item = Order_items.find(id)
    if not order_item:
        abort(status.HTTP_404_NOT_FOUND, f"Order with id '{id}' could not be found.")

    return make_response(jsonify(order_item.serialize()), status.HTTP_200_OK)

######################################################################
# ADD AN ITEM TO AN ORDER
######################################################################
@app.route('/orders/<int:order_id>/order_items', methods=['POST'])
def create_items(order_id):
    """
    Create an Item on an Order
    This endpoint will add an item to an order
    """
    app.logger.info("Request to create an Item for Order with id: %s", order_id)
    check_content_type("application/json")

    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, f"Order with id '{order_id}' could not be found.")

    item = Order_items()
    item.deserialize(request.get_json())
    order.items.append(item)
    order.update()
    message = item.serialize()
    return make_response(jsonify(message), status.HTTP_201_CREATED)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "Content-Type must be {}".format(media_type),
    )
