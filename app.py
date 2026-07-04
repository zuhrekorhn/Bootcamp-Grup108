import streamlit as st

st.set_page_config(page_title="Haber + Finansal Analiz Ajanı", layout="wide")

st.sidebar.title("Menü")
mod = st.sidebar.radio(
    "Bir mod seçin:",
    ("Genel Haber Modu", "Finansal Analiz Modu"),
)

st.title("Haber + Finansal Analiz Ajanı")

if mod == "Genel Haber Modu":
    st.write("Genel Haber Modu Aktif")
elif mod == "Finansal Analiz Modu":
    st.write("Finansal Mod Aktif")
    st.warning(
        "Bu içerik yalnızca bilgilendirme amaçlıdır. Yatırım tavsiyesi değildir. "
        "Yatırım kararlarınız için lütfen lisanslı bir yatırım danışmanına başvurun."
    )
