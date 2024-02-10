import re

def get_session_id(session_str: str):
    id = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if id:
        extracted_string = id.group(1) # Group(0) -> whole match || Group(1) -> Only what is inside the brackets
        return extracted_string
    
    return ""

def get_pizza_dict_string(pizza_dict: dict):
    if len(pizza_dict) == 1:
        key, value = next(iter(pizza_dict.items()))
        return f"{int(value)} {key[1]} {key[0]}"

    pizza_strings = [f"{int(value)} {key[1]} {key[0]}" for key, value in pizza_dict.items()]
    return ", and ".join([", ".join(pizza_strings[:-1]), pizza_strings[-1]])

def get_order_dict_string(order_dict: dict, order_id, name, phone):
    if len(order_dict) == 1:
        key, value = next(iter(order_dict.items()))
        return f"Order #{order_id} for {name}, {phone}: {int(key[2])} {key[1]} {key[0]} pizza - Status: {value}"
    
    for key, value in order_dict.items():
        status = value

    order_strings = [f"{int(key[2])} {key[1]} {key[0]}" for key, value in order_dict.items()]
    new_order_string = ", and ".join([", ".join(order_strings[:-1]), order_strings[-1]])
    full_order = f"Order #{order_id} for {name}, {phone}: " + new_order_string + f" pizzas - Status: {status}"
    return full_order
    


if __name__ == "__main__":
    food = {("bhajia", 'medium') : 3, ("burger", 'large') : 1}
    print(get_pizza_dict_string(food))
    # print(get_session_id("projects/pizza-chatbot-stwi/agent/sessions/b88aa043-a14a-d648-efb7-da33cf4e6c88/contexts/ongoing-order"))