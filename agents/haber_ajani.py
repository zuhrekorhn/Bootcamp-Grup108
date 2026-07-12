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

3. Her kaynak için, aşağıdaki 4 ölçülebilir metin özelliğini analiz et (siyasi/ideolojik yargı DEĞİL, sadece metin analizi):
   - "olgu_yorum_skoru": 0.0 (tamamen somut olgu/veri) ile 1.0 (tamamen yorum/görüş) arası bir sayı
   - "dogrulama_skoru": 0.0 (tek kaynağa dayanıyor) ile 1.0 (birden fazla kaynak/tanık doğrulamış) arası bir sayı
   - "atif_turu": Metin resmi bir açıklamaya mı, anonim bir kaynağa mı, yoksa başka bir habere mi dayanıyor? Kısaca belirt (örn. "resmi açıklama", "anonim kaynak", "başka habere dayalı", "belirtilmemiş")
   - "duygusal_yuzde": Metindeki duygusal yüklü kelime/sıfat/abartı oranını 0-100 arası bir yüzde olarak tahmin et

Yanıtını TAM OLARAK şu JSON formatında ver, öncesinde/sonrasında hiçbir açıklama yazma:
{{
  "tldr": "...",
  "kaynaklar_analiz": [
    {{
      "ozet": "1. kaynağın özeti",
      "olgu_yorum_skoru": 0.0,
      "dogrulama_skoru": 0.0,
      "atif_turu": "...",
      "duygusal_yuzde": 0
    }}
  ]
}}

Kurallar:
- Tarafsız, betimleyici bir dil kullan.
- [ortak nokta] ve [genel tablo] kısımlarında MUTLAKA somut isimler, sayılar, tarihler veya olay adları kullan.
- Kaynakları SİYASİ olarak (sağcı/solcu, hükümet yanlısı/muhalif) ASLA etiketleme. Sadece ölçülebilir metin özelliklerine bak.
- Markdown/başlık kullanma.
- Sadece geçerli JSON döndür.
- Yanıtın SADECE ve YALNIZCA {{ karakteriyle başlayıp }} karakteriyle bitmeli. "İşte", "Özet:", "Not:" gibi hiçbir giriş/açıklama cümlesi EKLEME.
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
        kaynaklar_analiz = veri_json.get("kaynaklar_analiz", [])
        json_basarili = True
    except Exception:
        tldr = ozet_ham
        kaynaklar_analiz = []
        json_basarili = False

    state["sonuc"] = tldr
    state["kaynaklar"] = sonuc["results"]
    state["kaynak_ozetleri"] = kaynak_ozetleri
    return state