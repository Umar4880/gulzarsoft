from supervisor_architecture import Supervisor
from pydantic import BaseModel
from state import supervisoer_state, coder_state, researcher_state, general_state

from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

class communication:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(mdole = "gemini-2.5-flash-lite")
        self.parser = StrOutputParser()

    def _supervisor(self, state: supervisoer_state):
        system_prompt = (
            "You are a supervisor managing a research, coder and general. "
            "Analyze the user's query and respond with ONLY the name of the agent "
            "that should handle the task: 'research_agent' or 'coding_agent' or 'general_agent'. "
            "If the user's query is already answered, or it's a simple greeting, respond with 'end'."

            "---"

            "QUERY:{query}"
        )

        template = PromptTemplate(
            template=system_prompt,
            input_variables=["query"]
        )

        chain = template | self.model | self.parser

        result = chain.invoke({"query":state['query']})

        return {"next_agent":result}
    
    def router(self, state:supervisoer_state):
        if state['next_agent'] == 'coding_agent':
            return "__coder__"
        elif state['next_agent'] == 'research_agent':
            return "__researcher__"
        elif state['next_agent'] == 'general_agent':
            return "__general__"
        elif state['next_agent'] == 'end':
            return "__end__"
    
    def _coder(self, state:coder_state):
        system_prompt = (
            "You are a coding agent. "
            "Analyze the user's query and write clean and optimized code with proper comments. "
            "---"
            "QUERY:{query}"
        )

        template = PromptTemplate(
            template=system_prompt,
            input_variables=["query"]
        )

        chain = template | self.model | self.parser

        result = chain.invoke({"query":state['query']})

        return {"answer":result}
    
    def _researcher(self, state:researcher_state):
        system_prompt = (
            "You are a researching agent. "
            "Analyze the user's query and return researching result. "
            "---"
            "QUERY:{query}"
        )

        template = PromptTemplate(
            template=system_prompt,
            input_variables=["query"]
        )

        chain = template | self.model | self.parser

        result = chain.invoke({"query":state['query']})

        return {"answer":result}
    
    def _general(self, state:general_state):
        system_prompt = (
            "You are an ai assistant. "
            "Analyze the user's query and asnwer precisly with professional tone. "
            "---"
            "QUERY:{query}"
        )

        template = PromptTemplate(
            template=system_prompt,
            input_variables=["query"]
        )

        chain = template | self.model | self.parser

        result = chain.invoke({"query":state['query']})

        return {"answer":result}


