from langgraph.graph import StateGraph

class OrderGraph:
    def __init__(self, state, user, ask, confirm, take, verify, thank):
        self.state = state

        self.take_order = take
        self.get_user_details = user
        self.verify_order = verify
        self.ask_again = ask
        self.confirm = confirm
        self.thank = thank

    def create_graph(self):
        graph = StateGraph(self.state)

        graph.add_node('get_user', self.get_user_details)
        graph.add_node('take_order', self.take_order)
        graph.add_node('re_ask', lambda state: {})
        graph.add_node('confirm_order', lambda state: {})
        graph.add_node('thank_customer', self.thank)


        graph.set_entry_point('get_user')
        graph.add_edge('get_user', 'take_order')

        graph.add_conditional_edges(
            'take_order',
            self.verify_order,
            {
                'take_order': 'take_order',
                're_ask': 're_ask',
                'thank_customer': 'thank_customer',
            },
        )

        graph.add_conditional_edges(
            're_ask',
            self.ask_again,
            {
                'take_order': 'take_order',
                'confirm_order': 'confirm_order',
            },
        )

        graph.add_conditional_edges(
            'confirm_order',
            self.confirm,
            {
                'take_order': 'take_order',
                'thank_customer': 'thank_customer',
            },
        )
        graph.set_finish_point('thank_customer')

        return graph.compile()

        
    