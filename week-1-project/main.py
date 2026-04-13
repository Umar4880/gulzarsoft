from api.fetch import Fetch
from api.llm import LLM
import os
import asyncio
import logging
from config.config import setup_logging

logger = logging.getLogger(__name__)

async def main(topic: list, city: list):
    
    news_api_key = os.getenv("NEWS_API_KEY", "")
    weather_api_key = os.getenv("WEATHER_API_KEY", "")

    weather_base_url = "https://api.openweathermap.org/data/2.5/weather"
    news_base_url = "https://newsdata.io/api/1/latest"

    requests = []

    for c in city:
        request = {
            "url":weather_base_url,
            "source":"weather",
            "params": {
                "q": c,
                "appid": weather_api_key,
                "units": "metric"
            }
        }
        requests.append(request)

    for t in topic:
        request = {
            "url": news_base_url,
            "source": "news",
            "params": {
                "apikey": news_api_key,
                "q": t,
                "language": "en",
                "country": "pk"
            }
        }
        requests.append(request)

    fetch_api = Fetch(request=requests)
    response = await fetch_api.fetch()
    await fetch_api.close()

    weather_response = [r["payload"] for r in response if r["source"] == "weather"]
    news_response = [r["payload"] for r in response if r["source"] == "news"]

    weather = [
        {
            "city": w.get("name"),
            "temp_c": w.get("main", {}).get("temp"),
            "description": (w.get("weather") or [{}])[0].get("description"),
        }
        for w in weather_response
    ]
    news = [
        {item.get("title"): item.get("description")}
        for payload in news_response
        for item in payload.get("results", [])
    ]

    print(news)
    llm_input = {"news": news, "weather": weather}
    call_llm = LLM(llm_input)

    async for chunk in call_llm.astream():
        print(chunk, end="", flush=True)
    print()

if __name__ == "__main__":
    setup_logging()

    no_of_cities = int(input("How many no of cities you want to fetch weather?"))
    citeis = []
    topics = []
    for i in range(0, no_of_cities):
        city = input(f"Enter name of city no {i+1}:")
        citeis.append(city)
    no_of_topics = int(input("How many no of topics you want to fetch news?"))
    for i in range(0, no_of_topics):
        topic = input(f"Enter topic no {i+1}:")
        topics.append(topic)
    
    asyncio.run(main(topic=topics, city=citeis))

    




    


