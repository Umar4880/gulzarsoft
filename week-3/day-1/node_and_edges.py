from langgraph.graph import StateGraph

class OrderGraph:
    def __init__(self, state, take, verify, thank):
        self.state = state

        self.take_order = take
        self.verify_order = verify
        self.thank = thank

    def create_graph(self):
        graph = StateGraph(self.state)

        graph.add_node('take_order', self.take_order)
        graph.add_node('thank_customer', self.thank)


        graph.set_entry_point('take_order')
        graph.add_conditional_edges(
            'take_order',
            self.verify_order,
            {
                'take_order': 'take_order',
                'thank_customer': 'thank_customer',
            },
        )
        graph.set_finish_point('thank_customer')

        return graph.compile()

        
    