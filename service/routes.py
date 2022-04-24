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
import sys
import secrets
import logging
from functools import wraps
from flask import jsonify, request, url_for, make_response, abort
from flask_restx import Api, Resource, fields, reqparse, inputs
from service.models import Order, items, DataValidationError, DatabaseConnectionError
from . import app, status  # HTTP Status Codes

# Document the type of autorization required
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Api-Key'
    }
}


######################################################################
# Configure the Root route before OpenAPI
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")

######################################################################
# Configure Swagger before initializing it
######################################################################
api = Api(app,
          version='1.0.0',
          title='Order Demo REST API Service',
          description='This is a sample server Order server.',
          default='orders',
          default_label='Order operations',
          doc='/apidocs', # default also could use doc='/apidocs/'
          authorizations=authorizations,
          prefix='/api'
         )


# Define the model so that the docs reflect what can be sent
create_model = api.model('Order', {
    'id': fields.Integer(readOnly=True,
                            description='The unique id assigned internally by service')
})

order_model = api.inherit(
    'OrderModel', 
    create_model,
    {
        'date': fields.Date(required=True, 
                            description='The date of the Order'),
        'customer': fields.String(required=True, 
                            description='The customer name of the Order (e.g., Yoda, Obiwan, Mace, etc.)'),
        'total': fields.Float(required=True, 
                            description='The total quantity of the Order'),
        'status': fields.String(required=True, 
                            description='The status of the Order (e.g., Open, Closed, Cancelled, Refunded, etc.)')
    }
)


# query string arguments
order_args = reqparse.RequestParser()
order_args.add_argument('customer', type=str, required=False, help='List Orders by customer')
order_args.add_argument('status', type=str, required=False, help='List Orders by status')


item_model = api.inherit(
    'ItemModel', 
    create_model, 
    {
        'order_id': fields.Integer(required=True, 
                            description='The id assigned to the Order'),
        'product_id': fields.Integer(required=True, 
                            description='The id assigned to the Product'),
        'quantity': fields.Integer(required=True, 
                            description='The quantity of the Order Item'),
        'price': fields.Integer(required=True,
                            description='The price of the Order Item'),
        'total': fields.Float(required=True, 
                            description='The total price of the Order Item')
    }
)



######################################################################
# Special Error Handlers
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    message = str(error)
    app.logger.error(message)
    return {
        'status_code': status.HTTP_400_BAD_REQUEST,
        'error': 'Bad Request',
        'message': message
    }, status.HTTP_400_BAD_REQUEST

@api.errorhandler(DatabaseConnectionError)
def database_connection_error(error):
    """ Handles Database Errors from connection attempts """
    message = str(error)
    app.logger.critical(message)
    return {
        'status_code': status.HTTP_503_SERVICE_UNAVAILABLE,
        'error': 'Service Unavailable',
        'message': message
    }, status.HTTP_503_SERVICE_UNAVAILABLE


######################################################################
# Authorization Decorator
######################################################################
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'X-Api-Key' in request.headers:
            token = request.headers['X-Api-Key']

        if app.config.get('API_KEY') and app.config['API_KEY'] == token:
            return f(*args, **kwargs)
        else:
            return {'message': 'Invalid or missing token'}, 401
    return decorated


######################################################################
# Function to generate a random API key (good for testing)
######################################################################
def generate_apikey():
    """ Helper function used when testing API keys """
    return secrets.token_hex(16)


######################################################################
#  PATH: /orders/{id}
######################################################################
@api.route('/orders/<order_id>')
@api.param('order_id', 'The Order identifier')
class OrderResource(Resource):
    """
    OrderResource class

    Allows the manipulation of a single Order
    GET /order{id} - Returns a Order with the id
    PUT /order{id} - Update a Order with the id
    DELETE /order{id} -  Deletes a Order with the id
    """
    ######################################################################
    # RETRIEVE AN ORDER
    ######################################################################
    @api.doc('get_orders')
    @api.response(404, 'Order not found')
    @api.marshal_with(order_model)
    def get(self, order_id):
        """
        Retrieve a single Order

        This endpoint will return a Order based on it's id
        """
        app.logger.info("Request for order with id: %s", order_id)
        order = Order.find(order_id)
        if not order:
            abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' was not found.".format(order_id))
        app.logger.info("Returning order: %s", order.id)
        return order.serialize(), status.HTTP_200_OK


    ######################################################################
    # UPDATE AN EXISTING ORDER
    ######################################################################
    @api.doc('update_orders', security='apikey')
    @api.response(404, 'Order not found')
    @api.response(400, 'The posted Order data was not valid')
    @api.expect(order_model)
    @api.marshal_with(order_model)
    @token_required
    def put(self, order_id):
        """
        Update an Order

        This endpoint will update an Order based the body that is posted
        """
        app.logger.info("Request to update order with id: %s", order_id)
        check_content_type("application/json")
        order = Order.find(order_id)
        if not order:
            abort(status.HTTP_404_NOT_FOUND, "Order with id '{}' was not found.".format(order_id))
        
        app.logger.debug('Payload = %s', api.payload)
        data = api.payload        
        order.deserialize(data)
        order.id = order_id
        order.update()
        app.logger.info("Order with ID [%s] updated.", Order.id)
        return order.serialize(), status.HTTP_200_OK

    ######################################################################
    # DELETE AN ORDER
    ######################################################################
    @api.doc('delete_orders', security='apikey')
    @api.response(204, 'Order deleted')
    @token_required
    def delete(self, order_id):
        """
        Delete a Order

        This endpoint will delete a Order based the id specified in the path
        """
        app.logger.info("Request to delete order with id: %s", order_id)

        order = Order.find(order_id)
        if order:
            order.delete()

        app.logger.info("Order with ID [%s] delete complete.", order_id)
        return '', status.HTTP_204_NO_CONTENT

######################################################################
#  PATH: /orders
######################################################################
@api.route('/orders', strict_slashes=False)
class OrderCollection(Resource):
    """ Handles all interactions with collections of Orders """

    ######################################################################
    # LIST ALL ORDERS
    ######################################################################
    @api.doc('list_orders')
    @api.expect(order_args, validate=True)
    @api.marshal_list_with(order_model)
    def get(self):
        """Returns all of the Orders"""
        app.logger.info("Request for Order List")
        
        orders = []
        customer = request.args.get("customer")
        order_status = request.args.get("status")
        if customer:
            orders = Order.find_by_customer(customer)
        elif order_status:
            orders = Order.find_by_status(order_status)
        else:
            orders = Order.all()

        results = [order.serialize() for order in orders]
        app.logger.info("Returning %d orders", len(results))
        return results, status.HTTP_200_OK

    ######################################################################
    # ADD A NEW ORDER
    ######################################################################
    @api.doc('create_orders', security='apikey')
    @api.response(400, 'The posted data was not valid')
    @api.expect(create_model)
    @api.marshal_with(order_model, code=201)
    @token_required
    def post(self):
        """
        Creates a Order
        This endpoint will create a Order based the data in the body that is posted
        """
        app.logger.info("Request to create a order")
        check_content_type("application/json")
        order = Order()
        app.logger.debug('Payload = %s', api.payload)
        order.deserialize(request.get_json())
        order.create()
        app.logger.info("Order with ID [%s] created.", order.id)
        location_url = api.url_for(OrderResource, order_id=order.id, _external=True)
        return order.serialize(), status.HTTP_201_CREATED, {"Location": location_url}

######################################################################
# PATH: /orders/{id}/cancelled
######################################################################
@api.route('/orders/<int:order_id>/cancelled')
@api.param('order_id', 'The Order identifier')
class CancelResource(Resource):
    """ Cancel actions on a Order """
    def put(self, order_id):
        """
        Cancel an Order

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
        app.logger.info("Order with ID [%s] cancelled.", Order.id)
        return order.serialize(), status.HTTP_200_OK

######################################################################
#  PATH: /orders/{order_id}/items/{id}
######################################################################
@api.route('/orders/<int:order_id>/items/<int:id>', strict_slashes=False)
class OrderItemsResource(Resource):
    """
    OrderItemResource class
    Allows the manipulation of a single Order Item
    GET /orders/{order_id}/items/{id} - Returns a Order Item with the id
    PUT /orders/{order_id}/items/{id} - Update a Order Item with the id
    DELETE /orders/{order_id}/items/{id} -  Deletes a Order Item with the id
    """

    ######################################################################
    # RETRIEVE An ORDER ITEM FROM ORDER
    ######################################################################
    @api.doc('get_items')
    @api.response(404, 'Item not found')
    @api.marshal_with(item_model)
    def get(self, order_id, id):
        """
        Get an Order Item

        This endpoint returns just an order item
        """
        app.logger.info("Request to retrieve Order Item %s for Order id: %s", (id, order_id))
        item = items.find(id)
        if not item:
            abort(status.HTTP_404_NOT_FOUND, f"Order with id '{id}' could not be found.")

        return item.serialize(), status.HTTP_200_OK

    ######################################################################
    # UPDATE AN ITEM
    ######################################################################
    @api.doc('update_items', security='apikey')
    @api.response(404, 'Item not found')
    @api.response(400, 'The posted Item data was not valid')
    @api.expect(item_model)
    @api.marshal_with(item_model)
    @token_required
    def put(self, order_id, id):
        """
        Update an Item

        This endpoint will update an Item based the body that is posted
        """
        app.logger.info("Request to update Item %s for Order id: %s", (id, order_id))
        check_content_type("application/json")

        item = items.find(id)
        if not item:
            abort(status.HTTP_404_NOT_FOUND, f"Order with id '{id}' could not be found.")

        item.deserialize(api.payload)
        item.id = id
        item.update()
        return item.serialize(), status.HTTP_200_OK

    ######################################################################
    # DELETE AN ITEM
    ######################################################################
    @api.doc('delete_items', security='apikey')
    @api.response(204, 'Order Item deleted')
    @token_required
    def delete(self, order_id, id):
        """
        Delete an Item

        This endpoint will delete an Item based the id specified in the path
        """
        app.logger.info("Request to delete Item %s for Order id: %s", (id, order_id))

        item = items.find(id)
        if item:
            item.delete()

        return make_response("", status.HTTP_204_NO_CONTENT)


######################################################################
#  PATH: /orders/{id}/items
######################################################################
@api.route('/orders/<int:order_id>/items', strict_slashes=False)
class OrderItemsCollection(Resource):
    """ Handles all interactions with collections of Order Items """

    ######################################################################
    # LIST ORDER ITEMS
    ######################################################################
    @api.doc('list_items')
    @api.marshal_list_with(item_model)
    def get(self, order_id):
        """ Returns all of the Items for an Order """
        app.logger.info("Request for all Items for Order with id: %s", order_id)

        order = Order.find(order_id)
        if not order:
            abort(status.HTTP_404_NOT_FOUND, f"Order with id '{order_id}' could not be found.")

        results = [item.serialize() for item in order.items]
        return results, status.HTTP_200_OK


    ######################################################################
    # ADD AN ITEM TO AN ORDER
    ######################################################################
    @api.doc('create_items', security='apikey')
    @api.response(400, 'The posted data was not valid')
    @api.expect(create_model)
    @api.marshal_with(item_model, code=201)
    @token_required
    def post(self, order_id):
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
        return message, status.HTTP_201_CREATED

######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

def abort(error_code: int, message: str):
    """Logs errors before aborting"""
    app.logger.error(message)
    api.abort(error_code, message)

@app.before_first_request
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

# load sample data
def data_load(payload):
    """ Loads a Order into the database """
    order = Order(payload['date'], payload['customer'], payload['total'], payload['status'])
    order.create()

def data_reset():
    """ Removes all Orders from the database """
    Order.remove_all()