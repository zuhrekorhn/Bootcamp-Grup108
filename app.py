"""
app.py
------
Haber + Finansal Analiz Ajanı — Streamlit ana giriş noktası.

Sol menüden seçilen moda göre (Genel Haber Modu / Finansal Analiz Modu)
ilgili ekranı render eder. Haber toplama ve analiz işlemleri sırasıyla
agents/news_agent.py ve agents/summary_agent.py modüllerindeki
fonksiyonlar üzerinden yürütülür.
"""

import streamlit as st

# --- Ajan fonksiyonlarını içe aktar -----------------------------------------
# Import sırasında oluşabilecek hataları (eksik paket, .env eksikliği vb.)
# uygulamanın çökmesi yerine kullanıcıya nazikçe göstermek için try/except kullanılır.
try:
    from agents.news_agent import haberleri_getir
    from agents.summary_agent import haberleri_analiz_et

    AJANLAR_YUKLENDI = True
    ajan_yukleme_hatasi = None
except Exception as e:
    AJANLAR_YUKLENDI = False
    ajan_yukleme_hatasi = str(e)


# --- Sayfa ayarları ----------------------------------------------------------
st.set_page_config(
    page_title="Haber + Finansal Analiz Ajanı",
    page_icon="📰",
    layout="wide",
)

# --- Sidebar / Menü ----------------------------------------------------------
st.sidebar.title("📊 Menü")
mod = st.sidebar.radio(
    "Bir mod seçin:",
    ("Genel Haber Modu", "Finansal Analiz Modu"),
)
st.sidebar.markdown("---")
st.sidebar.caption("Haber + Finansal Analiz Ajanı · Bootcamp Grup 108")

st.title("📰 Haber + Finansal Analiz Ajanı")

if not AJANLAR_YUKLENDI:
    st.error(
        "⚠️ Ajan modülleri yüklenemedi. Lütfen `requirements.txt` içindeki "
        "bağımlılıkların kurulu olduğundan ve `.env` dosyasının doğru "
        f"yapılandırıldığından emin olun.\n\nTeknik detay: {ajan_yukleme_hatasi}"
    )


# =============================================================================
# GENEL HABER MODU
# =============================================================================
if mod == "Genel Haber Modu":
    st.subheader("🔍 Genel Haber Modu")
    st.write(
        "Bir konu girin; ilgili son haberler toplanıp tarafsız bir özet ve "
        "kaynak bazlı olgu/yorum analiziyle sunulsun."
    )

    col_input, col_button = st.columns([4, 1])
    with col_input:
        konu = st.text_input(
            "Aranacak konu",
            placeholder="Örn: Yapay Zeka, Merkez Bankası faiz kararı...",
            label_visibility="collapsed",
        )
    with col_button:
        analiz_et = st.button("🔎 Analiz Et", use_container_width=True)

    if analiz_et:
        if not AJANLAR_YUKLENDI:
            st.error("Ajan modülleri yüklenemediği için analiz başlatılamıyor.")
        elif not konu or not konu.strip():
            st.warning("Lütfen önce aranacak bir konu girin.")
        else:
            try:
                with st.spinner(f"'{konu}' hakkında haberler toplanıyor..."):
                    haberler = haberleri_getir(konu)

                if not haberler:
                    st.warning("Bu konuyla ilgili haber bulunamadı. Başka bir konu deneyin.")
                else:
                    with st.spinner("Haberler Claude tarafından analiz ediliyor..."):
                        analiz = haberleri_analiz_et(haberler)

                    # Sonraki yeniden çalıştırmalarda (rerun) kaybolmaması için sakla
                    st.session_state["son_konu"] = konu
                    st.session_state["son_haberler"] = haberler
                    st.session_state["son_analiz"] = analiz

            except ValueError as e:
                st.error(f"🚫 Geçersiz girdi: {e}")
            except EnvironmentError as e:
                st.error(f"🔑 API anahtarı sorunu: {e}")
            except RuntimeError as e:
                st.error(
                    "🌐 Haber servisine veya Claude API'sine bağlanırken bir sorun oluştu. "
                    "Lütfen internet bağlantınızı ve API anahtarlarınızı kontrol edip tekrar deneyin."
                )
            except Exception:
                st.error("😕 Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

    # --- Sonuçları göster (varsa) --------------------------------------------
    if st.session_state.get("son_analiz"):
        analiz = st.session_state["son_analiz"]
        haberler = st.session_state.get("son_haberler", [])

        st.markdown("---")
        st.markdown("### 📌 Kısaca Ne Oldu?")
        st.info(analiz.get("tldr", "Özet oluşturulamadı."))

        bias_analysis = analiz.get("bias_analysis", {})
        if bias_analysis:
            st.markdown("### 🎯 Kaynak Bazlı Olgu / Yorum Analizi")
            st.caption("1 = Tamamen olgu, tarafsız  ·  10 = Tamamen yorum, abartılı")

            kaynaklar = list(bias_analysis.items())
            sutun_sayisi = 4
            for i in range(0, len(kaynaklar), sutun_sayisi):
                satir = kaynaklar[i : i + sutun_sayisi]
                columns = st.columns(sutun_sayisi)
                for col, (kaynak, puan) in zip(columns, satir):
                    etiket = "Yorum ağırlıklı" if puan >= 6 else "Olgu ağırlıklı"
                    col.metric(label=kaynak, value=f"{puan} / 10", delta=etiket, delta_color="off")

        if haberler:
            with st.expander(f"📰 Kaynak Haberler ({len(haberler)} adet)"):
                for haber in haberler:
                    st.markdown(
                        f"**{haber.get('Başlık', 'Başlık yok')}**  \n"
                        f"🗞️ {haber.get('Kaynak', 'Bilinmiyor')} · 🗓️ {haber.get('Tarih', 'Tarih yok')}  \n"
                        f"🔗 [{haber.get('URL', '')}]({haber.get('URL', '')})"
                    )
                    st.markdown("---")


# =============================================================================
# FİNANSAL ANALİZ MODU
# =============================================================================
elif mod == "Finansal Analiz Modu":
    st.subheader("💹 Finansal Analiz Modu")

    st.markdown(
        """
        <div style="text-align:center; padding: 3rem 1rem;">
            <h2>🚧 Çok Yakında</h2>
            <p style="font-size:1.1rem; color:gray;">
                Finansal analiz özellikleri üzerinde çalışıyoruz.<br>
                Bu bölüm yakında hisse senedi verisi ve yapay zeka destekli
                finansal içgörülerle aktif hale gelecek.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.warning(
        "⚠️ **Yasal Uyarı:** Bu içerik yalnızca bilgilendirme amaçlıdır. "
        "Yatırım tavsiyesi değildir. Yatırım kararlarınız için lütfen "
        "lisanslı bir yatırım danışmanına başvurun."
    )
