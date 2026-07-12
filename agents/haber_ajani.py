import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from tavily import TavilyClient

load_dotenv()
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

CLAUDE_MODEL = "claude-opus-4-8"

def haber_ajani(state: dict) -> dict:
    konu = state["konu"]
    sonuc = tavily_client.search(query=konu, max_results=3)

    haberler = ""
    for r in sonuc["results"]:
        haberler += f"- {r['title']}: {r['content'][:200]}\n"

    kaynak_sayisi = len(sonuc["results"])
    prompt = f"""Aşağıda '{konu}' hakkında {kaynak_sayisi} farklı haber kaynağından toplanan başlık ve içerikler var:

{haberler}

Şunları üret:
1. Bir TL;DR özeti, TAM OLARAK şu formatta:
"Bugün {konu} hakkında {kaynak_sayisi} kaynak incelendi. Kaynakların büyük çoğunluğu [ortak nokta]'yı öne çıkarırken, bazı kaynaklar [varsa ayrışan nokta] üzerine odaklandı. Genel tablo: [1-2 cümle özet]."

2. Her kaynak için AYRI, 2-3 cümlelik, senin kendi cümlelerinle yeniden yazılmış bir özet (orijinal metni kopyalama).

Yanıtını TAM OLARAK şu JSON formatında ver, öncesinde/sonrasında hiçbir açıklama yazma:
{{
  "tldr": "...",
  "kaynak_ozetleri": ["1. kaynağın özeti", "2. kaynağın özeti", "3. kaynağın özeti"]
}}

Kurallar:
- Tarafsız, betimleyici bir dil kullan.
- [ortak nokta] ve [genel tablo] kısımlarında MUTLAKA somut isimler, sayılar, tarihler veya olay adları kullan.
- Sadece kaynakların ne dediğini sentezle, kendi yorumunu katma.
- Markdown/başlık kullanma.
- Sadece geçerli JSON döndür.
"""
    response = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "{"}
        ],
    )
    ozet_ham = "{" + next((blok.text for blok in response.content if blok.type == "text"), "")

    try:
        metin = ozet_ham.strip()
        baslangic = metin.find("{")
        bitis = metin.rfind("}") + 1
        veri_json = json.loads(metin[baslangic:bitis])
        tldr = veri_json.get("tldr", ozet_ham)
        kaynak_ozetleri = veri_json.get("kaynak_ozetleri", [])
    except Exception:
        tldr = ozet_ham
        kaynak_ozetleri = []

    state["sonuc"] = tldr
    state["kaynaklar"] = sonuc["results"]
    state["kaynak_ozetleri"] = kaynak_ozetleri
    return state