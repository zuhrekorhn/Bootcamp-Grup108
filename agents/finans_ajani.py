import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic
import yfinance as yf
from agents.router import konu_sembol_bul

load_dotenv()
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CLAUDE_MODEL = "claude-opus-4-8"

def finans_ajani(state: dict) -> dict:
    konu = state["konu"]
    sembol = konu_sembol_bul(konu)

    if not sembol:
        state["sonuc"] = "Finansal enstrüman bulunamadı."
        return state

    ticker = yf.Ticker(sembol)
    veri = ticker.history(period="5d")

    if veri.empty:
        state["sonuc"] = "Veri bulunamadı."
        return state

    son_fiyat = veri["Close"].iloc[-1]
    onceki_fiyat = veri["Close"].iloc[-2]
    degisim_yuzde = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100

    prompt = f"""'{konu}' enstrümanının son 5 günlük kapanış fiyatları: {veri['Close'].tolist()}.
Son fiyat {son_fiyat:.2f}, günlük değişim %{degisim_yuzde:.2f}.

Şunları üret:
1. 3-4 cümlelik sade bir dil özeti. Örnek format:
"{konu} bugün %{degisim_yuzde:.2f} [yükseldi/geriledi] ve {son_fiyat:.2f} seviyesine ulaştı. Son 5 günlük seyre bakıldığında [gözlemlenen desen]. [Varsa dikkat çeken bir nokta]."

2. Bu veriye dayanarak -1 (çok negatif) ile +1 (çok pozitif) arası bir "piyasa duygu skoru" (sentiment score).

Yanıtını TAM OLARAK şu JSON formatında ver, öncesinde/sonrasında hiçbir açıklama yazma:
{{
  "yorum": "...",
  "sentiment_skoru": 0.0
}}

KESİN KURALLAR (istisnasız uygulanmalı):
- "Yatırım yapmalısınız", "almalısınız", "satmalısınız" gibi tavsiye ifadeleri ASLA kullanma.
- "Yükselecek", "düşecek", "hedef fiyat" gibi GELECEĞE dönük tahmin ifadeleri ASLA kullanma. Sadece GEÇMİŞTE ne olduğunu anlat.
- AL / SAT / BEKLE gibi sinyal kelimeleri ASLA kullanma.
- "Önemli", "kritik seviye", "dikkat edilmeli" gibi ima yoluyla tavsiye veren ifadelerden kaçın.
- sentiment_skoru sadece geçmiş fiyat hareketinin yönünü/büyüklüğünü yansıtsın, gelecek tahmini olarak kullanılmasın.
- Markdown/başlık kullanma, "yorum" alanı düz paragraf olsun.
- Sadece geçerli JSON döndür.
"""
    response = claude_client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    yanit_ham = "{" + next((blok.text for blok in response.content if blok.type == "text"), "")

    try:
        metin = yanit_ham.strip()
        baslangic = metin.find("{")
        bitis = metin.rfind("}") + 1
        veri_json = json.loads(metin[baslangic:bitis])
        yorum = veri_json.get("yorum", yanit_ham)
        sentiment = veri_json.get("sentiment_skoru", 0)
    except Exception:
        yorum = yanit_ham
        sentiment = 0

    state["sonuc"] = yorum
    state["sentiment_skoru"] = sentiment
    state["son_fiyat"] = son_fiyat
    state["degisim_yuzde"] = degisim_yuzde
    state["grafik_verisi"] = veri["Close"]
    return state