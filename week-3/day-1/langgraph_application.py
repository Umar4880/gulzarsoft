import datetime
from node_and_edges import OrderGraph
from state_schema import StateSchema
import time
class Order:
    def __init__(self):
        self.builder = OrderGraph(
            StateSchema,
            self.get_user_detials,
            self.re_ask,
            self.confirm,
            self.take_order,
            self.verify_order,
            self.thank_customer,
        )


    def get_user_detials(self, state: StateSchema):
        name = input("What is your name? ")
        phone_no = input("What is your phone number (03xxxxxxxxx)? ")
        print()
        return {'user_name': name, 'phone_no': phone_no}
    

    def re_ask(self, state: StateSchema):
        print("\n" + "-"*30)
        decision = input("Would you like to add more items to your order? [yes/no]: ")
        print()
        if decision.lower() == 'yes':
            return 'take_order'
        return 'confirm_order'
    

    def confirm(self, state: StateSchema):
        print("\n" + "="*30)
        print("Your order summary:")
        for idx, item in enumerate(state['order_list'], 1):
            print(f"  {idx}. {item}")
        print("="*30)
        decision = input("\nPlease confirm your order. Is this correct? [yes/no]: ")
        if decision.lower() == 'yes':
            return 'thank_customer'
        print("\nWe are very sorry for the inconvenience. Let's place the order again!\n")
        return 'take_order'


    def take_order(self, state: StateSchema):
        print("\n" + "-"*30)
        while True:
            try:
                order_length = int(input("How many items do you want to order? "))
                if order_length < 1:
                    print("Please enter a positive number.\n")
                    continue
                break
            except ValueError:
                print("Invalid input. Please enter a number.\n")

        order_list = []
        for length in range(1, order_length+1):
            order = input(f"Enter details for item {length}: ")
            order_list.append(order.strip())

        import uuid
        print()
        return {
            "order_id": str(uuid.uuid4()),
            "order_list": order_list,
            "order_placed_time": datetime.datetime.now().timestamp()
        }


    def verify_order(self, state: StateSchema):
        if not any(item and item.strip() for item in state.get("order_list", [])):
            print("\nYour order list is empty.")
            decision = input("Would you like to place an order? [yes/no]: ")
            if decision.lower() == "yes":
                return 'take_order'
            if decision.lower() == "no":
                return 'thank_customer'
            return 're_ask'
        return 're_ask'


    def thank_customer(self, state: StateSchema):
        import random
        time = random.randint(15, 30)
        print("\n" + "="*40)
        print("Thank you for choosing us!")
        print("Here is your order:")
        for idx, item in enumerate(state['order_list'], 1):
            print(f"  {idx}. {item}")
        print(f"\nYour order will be ready within {time} minutes.")
        print("="*40 + "\n")
        return {"is_delivered": True}
    
    
    def invoke(self):
        print("\n" + "#"*40)
        print("WELCOME TO NOVA RESTURANT!!!")
        print("#"*40 + "\n")
        graph = self.builder.create_graph()
        graph.invoke(
            {
                "user_name": "",
                "phone_no": 0,
                "order_id": "",
                "order_list": [],
                "is_delivered": False,
                "order_placed_time": 0.0,
                "order_deliver_time": 0.0,
            }
        )
    

if __name__ == "__main__":
    order = Order()

    order.invoke()