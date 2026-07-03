from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

response = client.search("dolar kuru son dakika")

for result in response["results"]:
    print(result["title"])
    print(result["url"])
    print("---")