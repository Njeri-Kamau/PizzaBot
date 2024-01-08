from fastapi import FastAPI, BackgroundTasks
from fastapi import Request
from fastapi.responses import JSONResponse
from db_helper import * 
from helper_func import *
from asyncio import sleep

app = FastAPI()

inprogress_orders = {}
locations_list = ["CBD", "Westlands", "Langata", "Kasarani", "South B", "South C", "Karen"]

@app.get("/")
async def root():
    return {"message" : "Hello World"}

@app.post("/")
async def handle_request(request: Request, tasks: BackgroundTasks):
    # tasks.add_task(schedule_task)
    
    # Get JSON data from the request
    payload = await request.json()

    # Get necessary info from the payload -> WebhookRequest from DialogFlow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = get_session_id(output_contexts[0]['name'])

    intent_handler_dict = {
        "TrackOrder - OngoingTracking" : track_order,
        "OrderAdd - OngoingOrder" : add_to_order,
        "OrderRemove - OngoingOrder": remove_from_order,
        "OrderComplete - OngoingOrder" : complete_order
    }

    text = intent_handler_dict[intent](parameters, session_id)
    return text

def add_to_order(parameters: dict, session_id: str):
    pizza_type = parameters['pizza-type']
    quantities = parameters['number']
    
    if len(pizza_type) != len(quantities):
        fulfillment_text = "I didn't get that correctly. Please specify the food items and their exact corresponding quantites."
    else:
        new_pizza_dict = dict(zip(pizza_type, quantities))

        if session_id in inprogress_orders:
            current = inprogress_orders[session_id]
            current.update(new_pizza_dict)
            inprogress_orders[session_id] = current
        else:
            inprogress_orders[session_id] = new_pizza_dict
        
        order_string = get_pizza_dict_string(inprogress_orders[session_id])
        fulfillment_text = f"Your order comprises: {order_string}. Would you need anything else added, removed or is the order perfect?"
       
    return JSONResponse(content={
        "fulfillmentText" : fulfillment_text
    })

def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = f"Sorry, I have trouble finding your order. Please place a new order."
    else:
        location = parameters['locations'][0]
        if location not in locations_list:
            fulfillment_text = f"{location} is not among the areas we deliver to. Choose one of these instead: {', '.join(locations_list[:-1])}, and {locations_list[-1]}"
        else:
            transit_time = get_transit_time(location)
            pizza_order = inprogress_orders[session_id]
            order_id = db_save(pizza_order, transit_time)

            if order_id == -1:
                fulfillment_text = "Sorry, I couldn't place your order due to a backend error.\nPlease place a new order again."
            else:
                order_total = get_order_total_price(order_id)
                total_time = get_total_time(order_id)
                fulfillment_text = f"Splendid. Your order has been placed.\nYour Order ID is # {order_id}.\n" \
                                    f"Your Order Total = {order_total}. The delivery will take an estimate of {total_time} minutes. You can pay at the time of delivery!"
    
            # Remove the session_id from the inprogress_orders once completed
            del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText" : fulfillment_text
    })

def db_save(order: dict, transit_time):
    next_order_id = get_next_id("orders")
    for pizza_type, quantity in order.items():
        return_code = insert_order_item(
            pizza_type,
            quantity,
            next_order_id,
            transit_time
        )
        if return_code == -1:
            return -1
        
    return next_order_id


def track_order(parameters: dict, session_id: str):
    order_id = int(parameters['order_id'])
    order_status = get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for order ID {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order ID: {order_id}"

    return JSONResponse(content={
        "fulfillmentText" : fulfillment_text
    })
 
def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = f"Sorry, I have trouble finding your order. Please place a new order."
    else:
        current = inprogress_orders[session_id] 
        pizza_items = parameters["pizza-type"]
        quantity = parameters["number"]

        removed_items = []
        non_existing = []

        for pizza in pizza_items:
            if pizza not in current:
                pass
            else:
                removed_items.append(pizza)
                del current[pizza]

        if len(removed_items) > 0:
            order_string = get_pizza_dict_string(inprogress_orders[session_id])
            if len(removed_items) == 1:
                fulfillment_text = f"Removed {removed_items[0]}. Your order comprises: {order_string}."
            else:
                fulfillment_text = f"Removed {', '.join(removed_items[:-1])}, and {removed_items[-1]}. Your order comprises: {order_string}."

        if len(non_existing) > 0:
            if len(removed_items) == 1:
                fulfillment_text = f"{non_existing[0]} is not part of your order!"
            else:
                fulfillment_text = f"{',  '.join(non_existing[:-1])}, and {removed_items[-1]} are not in your order!"

        if len(current.keys()) == 0:
            fulfillment_text = "Your order is now empty!"
        else:
            statement = get_pizza_dict_string(current)
            fulfillment_text = f"Your order is left with the following: {statement}. Do you want to add or remove any other pizza, or should I place the order?"

    return JSONResponse(content={
        "fulfillmentText" : fulfillment_text
    })