from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
from config.decorator import retry_call

load_dotenv("./.env")

class LLM:
    def __init__(self, payload: dict):
        self.payload = payload
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
        self.parser = StrOutputParser()

    def get_prompt(self):
        prompt="""
            Your are senior persoanl assistant. Your task is to analyse given news and weather, gave "Morning Briefing" and how it could impact their work.

            ---
            RULES:
            - Tone: Guiding and Professional
            - Scope: News and Weather
            
            Here are news & weather:
            News: {news}
            Weather: {weather}
        """

        template = PromptTemplate(
            template=prompt,
            input_variables=["news", "weather"]
        )

        return template
    
    @retry_call
    async def astream(self):
        template = self.get_prompt()
        chain = template | self.model | self.parser

        async for chunk in chain.astream(input=self.payload):
            yield chunk
    

