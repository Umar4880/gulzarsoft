import os
import httpx
from dotenv import load_dotenv

from pydantic import BaseModel, Field

from state_schema import ParentState, SubgraphState
from langgraph.graph import StateGraph, START, END, Send
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv('.env')

class Graphs:
    _news_api_key = os.getenv('NEW_API_KEY')

    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash-lite"
        )

    def _build_subgraph(self):
        sub_graph = StateGraph(SubgraphState)

        sub_graph.add_node('retrieve', self.retrieve)
        sub_graph.add_node('summarize', self.summarize)

        sub_graph.add_edge(START, 'retrieve')
        sub_graph.add_edge('retrieve', 'summarize')
        sub_graph.add_edge('summarize', END)

        return sub_graph.compile()

    def _build_graph(self):
        graph = StateGraph(ParentState)

        graph.add_node('orchestrator', self.assign_work)
        graph.add_node('worker', self.worker)
        
        graph.add_edge(START, 'orchestrator')
        graph.add_edge('orchestrator', 'worker')
        graph.add_edge('worker', END)

        return graph.compile()
    
    def retrieve(self, state: SubgraphState):

        news_base_url = "https://newsdata.io/api/1/latest"

        params = {
            'q': state['topic'],
            "apikey": self._news_api_key,
            'language': 'en',
            'country': 'pk'
        }

        response = httpx.get(url=news_base_url, params=params)

        return {'title': response.get('title'), 'content':response.get('article')}
    
    def summarize(self, state: SubgraphState):

        prompt = """Your are senior news investigator. 
                    Your task is to anaylze given new title, content and generate precise news summary with all keyiformtion and 5 keypoints. 
                    Here are is the title and content:

                    INPUT:
                        Title: {title}
                        Contnet: {Content}                
                    """
        
        template = PromptTemplate(
            template=prompt,
            input_variables=['title', 'content']
        )

        class LLMOutput(BaseModel):
            summary: str = Field(default_factory=str, description="summary of the news")
            keypoints: list[str] = Field(defualt_factory=list, description="5 keypoints of news")

        structure_model = self.model.with_structured_output(LLMOutput)

        chain = template | structure_model | StrOutputParser()

        input = {'title':state['title'], 'content':state['content']}
        result = chain.invoke(input)
        
        return {'summary': result}
    
    def assign(self, state:ParentState):

        sends = []
        for topic in state['topic']:
            sends.append(Send(("process_article", {"current_topic": topic})))

        return sends
    
    def worker(self, state: ParentState):

        self.subgraph_worker = self._build_subgraph()

        topic = {'topic': state['current_topic']}
        result = self.subgraph_worker.invoke(topic)

        summary = result.get("summary")
        if summary:
            return {"summaries": {topic: summary}}
        return {}
    



