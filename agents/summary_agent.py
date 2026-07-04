"""
summary_agent.py
----------------
Haber toplayıcıdan (news_agent) gelen haber listesini Anthropic (Claude) API
kullanarak analiz eden ajan.

Bu modül, verilen haber listesini Claude'a gönderir ve şu iki bilgiyi içeren
bir JSON sözlüğü döndürür:
    - "tldr": Tüm kaynakları sentezleyen tarafsız, tek paragraflık özet.
    - "bias_analysis": Her kaynağın başlığını 1 (tamamen olgu) ile
      10 (tamamen yorum) arasında puanlayan bir sözlük.
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

# .env dosyasındaki ortam değişkenlerini yükle
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Varsayılan model: en yetenekli Claude modeli
MODEL = "claude-opus-4-8"

# Claude'a verilecek sistem talimatı: tarafsızlık ve JSON formatı zorunluluğu
SYSTEM_PROMPT = """\
Sen tarafsız bir haber analisti ve medya okuryazarlığı uzmanısın.
Sana bir haber listesi verilecek. Her haberin "Kaynak" ve "Başlık" bilgisi olacak.

Görevlerin:
1. "tldr": Tüm kaynakları sentezleyen, tarafsız, tek paragraflık bir
   "Kısaca Ne Oldu?" özeti yaz. Bu özet kesinlikle yönlendirme, yorum veya
   kendi görüşünü içermemeli; sadece kaynaklarda ortak olan olguları anlat.
2. "bias_analysis": Her kaynağın başlığını ayrı ayrı değerlendirip,
   başlığın ne kadar olgu-ağırlıklı (fact) veya yorum-ağırlıklı (opinion)
   olduğunu 1 ile 10 arasında bir tam sayı ile puanla.
   1 = Tamamen olgu, tarafsız bir başlık.
   10 = Tamamen yorum, abartılı veya duygusal bir başlık.
   Anahtar olarak haberin "Kaynak" adını kullan.

Yanıtını SADECE aşağıdaki formatta geçerli bir JSON nesnesi olarak ver.
Başka hiçbir açıklama, giriş cümlesi veya markdown kod bloğu ekleme:

{"tldr": "...", "bias_analysis": {"Kaynak1": 3, "Kaynak2": 8}}
"""


def haberleri_analiz_et(haberler: list[dict]) -> dict:
    """
    Verilen haber listesini Claude API'ye gönderip analiz sonucunu döndürür.

    Parametreler:
        haberler (list[dict]): Her biri en azından "Kaynak" ve "Başlık"
            anahtarlarını içeren haber sözlüklerinden oluşan liste
            (örn. [{"Kaynak": "BBC", "Başlık": "...", "URL": "..."}]).

    Dönüş:
        dict: {"tldr": str, "bias_analysis": {kaynak_adı: puan}} yapısında sözlük.
    """
    if not haberler:
        raise ValueError("Analiz edilecek haber listesi boş olamaz.")

    if not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY bulunamadı. Lütfen .env dosyasına geçerli bir Anthropic API anahtarı ekleyin."
        )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # Haber listesini modelin okuyabileceği bir metne dönüştür
    haber_metni = json.dumps(haberler, ensure_ascii=False, indent=2)
    kullanici_mesaji = f"Aşağıdaki haber listesini analiz et:\n\n{haber_metni}"

    try:
        yanit = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": kullanici_mesaji}],
        )
    except Exception as hata:
        raise RuntimeError(f"Claude API isteği sırasında hata oluştu: {hata}") from hata

    # Yanıttaki metin bloğunu bul
    yanit_metni = next((blok.text for blok in yanit.content if blok.type == "text"), "")

    try:
        sonuc = json.loads(yanit_metni)
    except json.JSONDecodeError as hata:
        raise ValueError(
            f"Claude'dan gelen yanıt geçerli bir JSON değil:\n{yanit_metni}"
        ) from hata

    return sonuc


if __name__ == "__main__":
    # Test: aynı olay hakkında 3 farklı üslupta (tarafsız / abartılı / ortalama) sahte haber
    ornek_haberler = [
        {
            "Kaynak": "Reuters",
            "Başlık": "Merkez Bankası politika faizini değiştirmedi",
            "URL": "https://example.com/reuters-haber",
        },
        {
            "Kaynak": "ŞokHaber",
            "Başlık": "İNANILMAZ! Merkez Bankası'nın faiz kararı herkesi şaşkına çevirdi, işte perde arkası!",
            "URL": "https://example.com/sokhaber-haber",
        },
        {
            "Kaynak": "Anadolu Ajansı",
            "Başlık": "Merkez Bankası Para Politikası Kurulu faiz oranını sabit tuttu, piyasalar karışık tepki verdi",
            "URL": "https://example.com/aa-haber",
        },
    ]

    try:
        sonuc = haberleri_analiz_et(ornek_haberler)
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Hata: {e}")
