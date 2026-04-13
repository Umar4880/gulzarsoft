from node_and_edges import OrderGraph
from state_schema import StateSchema

class Order:
    def __init__(self):
        self.builder = OrderGraph(StateSchema, self.take_order, self.verify_order, self.thank_customer)

    def take_order(self, state: StateSchema):
        order_length = int(input("How many items do you want to order? "))

        order_list = []
        for length in range(1, order_length+1):
            order = input(f"Please enter deatils of order no {length}: ")
            order_list.append(order.strip())

        import uuid 

        return {"order_id": str(uuid.uuid4()), "order": order_list}
    
    def verify_order(self, state: StateSchema):
        if not any(item and item.strip() for item in state["order"]):
            return 'take_order'
        
        return 'thank_customer'
    
    def thank_customer(self, state: StateSchema):
        import random
        time = random.randint(15, 30)
        print(f"\nThankyou for chosing us! Here is your order:\n\n{state['order']}\n\nThe order will be ready within {time} minutes.")
        return {"delivered": True}
    
    def invoke(self):
         graph = self.builder.create_graph()
         graph.invoke({"order_id": "", "order": [], "delivered": False})
    

if __name__ == "__main__":
    order = Order()

    print("Thankyou for comming, what will you like to order?")
    order.invoke()

