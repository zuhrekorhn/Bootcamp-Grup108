import os
from dotenv import load_dotenv
from google import genai
from tavily import TavilyClient

load_dotenv()

# API client'ları başlat
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. Tavily'den haber çek
konu = "dolar kuru"
sonuc = tavily_client.search(query=konu, max_results=3)

# 2. Haber başlıklarını birleştir
haberler = ""
for r in sonuc["results"]:
    haberler += f"- {r['title']}: {r['content'][:200]}\n"

print("--- ÇEKİLEN HABERLER ---")
print(haberler)

# 3. Gemini'ye özetlet
prompt = f"""Aşağıda '{konu}' hakkında haber başlıkları ve içerikleri var.
Bunları analiz et ve 3-4 cümlelik kısa bir özet çıkar:

{haberler}
"""

response = gemini_client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

print("--- GEMINI ÖZETİ ---")
print(response.text)