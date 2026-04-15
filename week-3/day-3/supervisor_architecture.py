from langgraph.graph import StateGraph, END, START

class Supervisor:
    def __init__(self, supervisor, coder, researcher, general, router):
        self.supervisor = supervisor
        self.coder = coder
        self.researcher = researcher
        self.general = general
        self.route = router


    def _supervisor_graph_(self):
        graph = StateGraph()

        nodes = {
            "supervisor": self.supervisor,
            "coder": self.coder,
            "researcher": self.researcher,
            "general": self.general
        }
        graph.nodes(nodes)

        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            'supervisor', 
            self.route, 
            {
                "__coder__": "coder",
                "__researcher__": "researcher",
                "__general__": "general",
                "__end__": END
            }
        )

        graph.add_edge("coder", "supervisor")
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("general", "supervisor")

        return graph.compile()