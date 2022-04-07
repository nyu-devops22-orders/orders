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
GET /orders/{id} - Returns the order with a given id number
POST /orders - creates a new order record in the database
PUT /orders/{id} - updates an order record in the database
DELETE /orders/{id} - deletes an order record in the database
"""

from flask import jsonify, request, url_for, make_response, abort
from werkzeug.exceptions import NotFound
from service.models import Order, items, DataValidationError
from . import status  # HTTP Status Codes
from . import app  # Import Flask application

######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/healthcheck")
def healthcheck():
    """Let them know our heart is still beating"""
    return make_response(jsonify(status=200, message="Healthy"), status.HTTP_200_OK)


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


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
@app.route("/orders/<int:order_id>", methods=["PUT"])
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

######################################################################
# CANCEL AN ORDER
######################################################################
@app.route("/orders/<int:order_id>/cancelled", methods=["PUT"])
def cancel_order(order_id):
    """
    Update an Order

    This endpoint will cancel an Order based the body that is posted
    """
    app.logger.info("Request to Cancel order with id: %s", order_id)
   
    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, f"Order with id '{order_id}' was not found.")
    
    if order.status == "Cancelled":
        abort(status.HTTP_409_CONFLICT, f"Order with id '{order_id}' was cancelled.")

    order.status = "Cancelled"
    order.update()
    return make_response(jsonify(order.serialize()), status.HTTP_200_OK)

#---------------------------------------------------------------------
#                O R D E R   I T E M   M E T H O D S
#---------------------------------------------------------------------

######################################################################
# LIST ORDER ITEMS
######################################################################
@app.route("/orders/<int:order_id>/items", methods=["GET"])
def list_items(order_id):
    """ Returns all of the Items for an Order """
    app.logger.info("Request for all Items for Order with id: %s", order_id)

    order = Order.find(order_id)
    if not order:
        abort(status.HTTP_404_NOT_FOUND, f"Order with id '{order_id}' could not be found.")

    results = [item.serialize() for item in order.items]
    return make_response(jsonify(results), status.HTTP_200_OK)


######################################################################
# RETRIEVE An ORDER ITEM FROM ORDER
######################################################################
@app.route("/orders/<int:order_id>/items/<int:id>", methods=["GET"])
def get_items(order_id, id):
    """
    Get an Order Item

    This endpoint returns just an order item
    """
    app.logger.info("Request to retrieve Order Item %s for Order id: %s", (id, order_id))
    item = items.find(id)
    if not item:
        abort(status.HTTP_404_NOT_FOUND, f"Order with id '{id}' could not be found.")

    return make_response(jsonify(item.serialize()), status.HTTP_200_OK)

######################################################################
# ADD AN ITEM TO AN ORDER
######################################################################
@app.route('/orders/<int:order_id>/items', methods=['POST'])
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

    item = items()
    item.deserialize(request.get_json())
    order.items.append(item)
    order.update()
    message = item.serialize()
    return make_response(jsonify(message), status.HTTP_201_CREATED)

######################################################################
# UPDATE AN ITEM
######################################################################
@app.route("/orders/<int:order_id>/items/<int:item_id>", methods=["PUT"])
def update_items(order_id, item_id):
    """
    Update an Item

    This endpoint will update an Item based the body that is posted
    """
    app.logger.info("Request to update Item %s for Order id: %s", (item_id, order_id))
    check_content_type("application/json")

    item = items.find(item_id)
    if not item:
        abort(status.HTTP_404_NOT_FOUND, f"Order with id '{item_id}' could not be found.")

    item.deserialize(request.get_json())
    item.id = item_id
    item.update()
    return make_response(jsonify(item.serialize()), status.HTTP_200_OK)

######################################################################
# DELETE AN ITEM
######################################################################
@app.route("/orders/<int:order_id>/items/<int:item_id>", methods=["DELETE"])
def delete_items(order_id, item_id):
    """
    Delete an Item

    This endpoint will delete an Item based the id specified in the path
    """
    app.logger.info("Request to delete Item %s for Order id: %s", (item_id, order_id))

    item = items.find(item_id)
    if item:
        item.delete()

    return make_response("", status.HTTP_204_NO_CONTENT)

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def init_db():
    """ Initializes the SQLAlchemy app """
    global app
    Order.init_db(app)
    items.init_db(app)

def check_content_type(content_type):
    """ Checks that the media type is correct """
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Content-Type must be {content_type}")