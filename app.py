import os
import uuid
import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic
from tavily import TavilyClient
import chromadb
import yfinance as yf
from graph import graph_olustur

load_dotenv()

CLAUDE_MODEL = "claude-opus-4-8"

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@st.cache_resource
def get_graph():
    return graph_olustur()


app_graph = get_graph()

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="analizler")

st.set_page_config(page_title="Haber + Finansal Analiz Ajanı", page_icon="📰", layout="wide")

def css_yukle(dosya_yolu):
    with open(dosya_yolu) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_yukle("assets/style.css")

st.title("📰 Haber + Finansal Analiz Ajanı")
st.write("Bir konu gir veya finansal veri seç, yapay zeka ile analiz edelim.")

with st.sidebar:
    st.subheader("🧠 Geçmiş Sorgular")
    tum_kayitlar = collection.get()
    if tum_kayitlar["ids"]:
        for i, meta in reversed(list(enumerate(tum_kayitlar["metadatas"]))):
            goruntu_metni = meta['konu'] if len(meta['konu']) <= 25 else meta['konu'][:25] + "..."
            if st.button(f"🔎 {goruntu_metni}", key=f"gecmis_{i}", use_container_width=True):
                st.session_state["secili_kayit"] = {
                    "konu": meta["konu"],
                    "ozet": tum_kayitlar["documents"][i]
                }
    else:
        st.caption("Henüz sorgu yapılmadı.")

if "secili_kayit" in st.session_state:
    secili = st.session_state["secili_kayit"]
    st.markdown("---")
    st.subheader(f"📌 Geçmiş Sorgu: {secili['konu']}")
    st.info(secili["ozet"])
    if st.button("✕ Kapat"):
        del st.session_state["secili_kayit"]
        st.rerun()
    st.markdown("---")

# --- MOD SEÇİMİ ---
mod = st.radio(
    "Mod Seç",
    ["📰 Genel Haber", "💰 Finansal Veri", "🤖 Otomatik (AI Karar Versin)"],
    horizontal=True,
)

# Mod değiştiğinde eski "geçmiş sorgu" kutusunu otomatik kapat
if "aktif_mod" not in st.session_state:
    st.session_state["aktif_mod"] = mod
elif st.session_state["aktif_mod"] != mod:
    st.session_state["aktif_mod"] = mod
    if "secili_kayit" in st.session_state:
        del st.session_state["secili_kayit"]
    st.rerun()

    
# --- FİNANSAL VERİ SÖZLÜĞÜ ---
FINANSAL_ENSTRUMANLAR = {
    "USD/TRY (Dolar)": "USDTRY=X",
    "EUR/TRY (Euro)": "EURTRY=X",
    "Bitcoin (BTC/USD)": "BTC-USD",
    "Altın (Ons)": "GC=F",
    "BIST 100": "XU100.IS",
}

def hafizaya_kaydet(konu, ozet):
    tum_kayitlar = collection.get()
    eslesen_id = None
    konu_temiz = " ".join(konu.strip().lower().split())
    for i, meta in enumerate(tum_kayitlar["metadatas"]):
        meta_temiz = " ".join(meta["konu"].strip().lower().split())
        if meta_temiz == konu_temiz:
            eslesen_id = tum_kayitlar["ids"][i]
            break
    if eslesen_id:
        collection.update(ids=[eslesen_id], documents=[ozet], metadatas=[{"konu": konu}])
    else:
        collection.add(documents=[ozet], metadatas=[{"konu": konu}], ids=[str(uuid.uuid4())])

# ============ GENEL HABER MODU ============
if mod == "📰 Genel Haber":
    konu = st.text_input("🔍 Konu", placeholder="örn: dolar kuru, enflasyon, Bitcoin")

    if st.button("🚀 Analiz Et", type="primary") and konu:
        benzer_sonuc = collection.query(query_texts=[konu], n_results=1)
        if benzer_sonuc["documents"] and benzer_sonuc["documents"][0]:
            mesafe = benzer_sonuc["distances"][0][0]
            if mesafe < 0.8:
                onceki_konu = benzer_sonuc["metadatas"][0][0]["konu"]
                onceki_ozet = benzer_sonuc["documents"][0][0]
                st.info(f"🧠 Daha önce **'{onceki_konu}'** hakkında da bir analiz yapmıştın:\n\n{onceki_ozet}")

        with st.spinner("📡 Haberler çekiliyor..."):
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

            import json
            try:
                metin = ozet_ham.strip()
                baslangic = metin.find("{")
                bitis = metin.rfind("}") + 1
                veri = json.loads(metin[baslangic:bitis])
                tldr = veri.get("tldr", ozet_ham)
                kaynak_ozetleri = veri.get("kaynak_ozetleri", [])
            except Exception:
                tldr = ozet_ham
                kaynak_ozetleri = []

        st.markdown("### 🤖 Claude Özeti")
        st.success(tldr)

        hafizaya_kaydet(konu, tldr)

        st.markdown("### 📰 Kaynaklar")
        for i, r in enumerate(sonuc["results"]):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{r['title']}**")
                    if i < len(kaynak_ozetleri):
                        st.write(kaynak_ozetleri[i])
                    else:
                        st.caption(r['content'][:200] + "...")
                with col2:
                    st.link_button("Kaynağa Git →", r['url'])

# ============ FİNANSAL VERİ MODU ============
elif mod == "💰 Finansal Veri":
    secilen = st.selectbox("Bir enstrüman seç", list(FINANSAL_ENSTRUMANLAR.keys()))

    if st.button("📊 Veriyi Getir", type="primary"):
        sembol = FINANSAL_ENSTRUMANLAR[secilen]

        with st.spinner("📊 Finansal veri çekiliyor..."):
            ticker = yf.Ticker(sembol)
            veri = ticker.history(period="5d")

        if veri.empty:
            st.error("Veri bulunamadı, lütfen başka bir enstrüman deneyin.")
        else:
            son_fiyat = veri["Close"].iloc[-1]
            onceki_fiyat = veri["Close"].iloc[-2]
            degisim = son_fiyat - onceki_fiyat
            degisim_yuzde = (degisim / onceki_fiyat) * 100

            col1, col2, col3 = st.columns(3)
            col1.metric("Son Fiyat", f"{son_fiyat:.2f}")
            col2.metric("Değişim", f"{degisim:.2f}", f"{degisim_yuzde:.2f}%")
            col3.metric("Son 5 Gün Yüksek", f"{veri['High'].max():.2f}")

            st.line_chart(veri["Close"])

            with st.spinner("🤖 Claude yorumluyor..."):
                prompt = f"""'{secilen}' enstrümanının son 5 günlük kapanış fiyatları: {veri['Close'].tolist()}.
Son fiyat {son_fiyat:.2f}, günlük değişim %{degisim_yuzde:.2f}.

Şunları üret:
1. 3-4 cümlelik sade bir dil özeti. Örnek format:
"{secilen} bugün %{degisim_yuzde:.2f} [yükseldi/geriledi] ve {son_fiyat:.2f} seviyesine ulaştı. Son 5 günlük seyre bakıldığında [gözlemlenen desen]. [Varsa dikkat çeken bir nokta]."

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
                        {"role": "assistant", "content": "{"}
                    ],
                )
                yanit_ham = "{" + next((blok.text for blok in response.content if blok.type == "text"), "")

                import json
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

            if sentiment >= 0.5:
                etiket = "🟢 Piyasa haberleri genel olarak olumlu"
            elif sentiment <= -0.5:
                etiket = "🔴 Piyasa haberleri genel olarak olumsuz"
            else:
                etiket = "🟡 Piyasa haberleri karışık / nötr"

            st.metric("Piyasa Duygu Durumu", etiket, f"{sentiment:.2f}")

            st.markdown("### 🤖 Claude Yorumu")
            st.success(yorum)
            st.caption("⚠️ Bu yorum yalnızca bilgilendirme amaçlıdır ve yatırım tavsiyesi niteliği taşımaz.")

            hafizaya_kaydet(secilen, yorum)

# ============ OTOMATİK MOD (AI KARAR VERSİN) ============
else:
    konu = st.text_input(
        "🔍 Konu", placeholder="örn: dolar kuru, enflasyon, Bitcoin", key="oto_konu"
    )

    if st.button("🤖 Analiz Et", type="primary") and konu:
        with st.spinner("🧭 Router karar veriyor ve analiz ediliyor..."):
            sonuc = app_graph.invoke({
                "konu": konu,
                "mod": "",
                "sonuc": "",
                "kaynaklar": [],
                "son_fiyat": 0,
                "degisim_yuzde": 0,
                "grafik_verisi": None,
            })

        if sonuc["mod"] == "finans":
            st.info("📊 Router kararı: **Finansal Veri** modu")

            if sonuc.get("grafik_verisi") is not None:
                col1, col2 = st.columns(2)
                col1.metric("Son Fiyat", f"{sonuc['son_fiyat']:.2f}")
                col2.metric("Değişim", f"{sonuc['degisim_yuzde']:.2f}%")
                st.line_chart(sonuc["grafik_verisi"])

            sentiment = sonuc.get("sentiment_skoru", 0)
            if sentiment >= 0.5:
                etiket = "🟢 Piyasa haberleri genel olarak olumlu"
            elif sentiment <= -0.5:
                etiket = "🔴 Piyasa haberleri genel olarak olumsuz"
            else:
                etiket = "🟡 Piyasa haberleri karışık / nötr"
            st.metric("Piyasa Duygu Durumu", etiket, f"{sentiment:.2f}")

            st.markdown("### 🤖 Claude Yorumu")
            st.success(sonuc["sonuc"])
            st.caption("⚠️ Bu yorum yalnızca bilgilendirme amaçlıdır ve yatırım tavsiyesi niteliği taşımaz.")
        else:
            st.info("📰 Router kararı: **Genel Haber** modu")

            st.markdown("### 🤖 Claude Özeti")
            st.success(sonuc["sonuc"])

            kaynak_ozetleri = sonuc.get("kaynak_ozetleri", [])
            st.markdown("### 📰 Kaynaklar")
            for i, r in enumerate(sonuc["kaynaklar"]):
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{r['title']}**")
                        if i < len(kaynak_ozetleri):
                            st.write(kaynak_ozetleri[i])
                        else:
                            st.caption(r['content'][:200] + "...")
                    with col2:
                        st.link_button("Kaynağa Git →", r['url'])

        hafizaya_kaydet(konu, sonuc["sonuc"])
