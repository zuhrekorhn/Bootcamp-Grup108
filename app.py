import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from tavily import TavilyClient

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="Haber + Finansal Analiz Ajanı", page_icon="📰")
st.title("📰 Haber + Finansal Analiz Ajanı")
st.write("Bir konu gir, güncel haberleri çekip yapay zeka ile özetleyelim.")

konu = st.text_input("Konu", placeholder="örn: dolar kuru, enflasyon, Bitcoin")

if st.button("Analiz Et") and konu:
    with st.spinner("Haberler çekiliyor..."):
        sonuc = tavily_client.search(query=konu, max_results=3)

    haberler = ""
    for r in sonuc["results"]:
        haberler += f"- {r['title']}: {r['content'][:200]}\n"

    with st.spinner("Gemini analiz ediyor..."):
        prompt = f"""Aşağıda '{konu}' hakkında haber başlıkları ve içerikleri var.
Bunları analiz et ve 3-4 cümlelik kısa bir özet çıkar:

{haberler}
"""
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

    st.subheader("🤖 Gemini Özeti")
    st.write(response.text)

    with st.expander("📰 Kullanılan Haber Kaynakları"):
        for r in sonuc["results"]:
            st.markdown(f"**{r['title']}**")
            st.write(r['content'][:200] + "...")
            st.markdown(f"[Kaynak]({r['url']})")
            st.divider()