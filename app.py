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
    from agents.finans_ajani import finansal_analiz_yap
    from data.finans_verisi import (
        VARLIK_LISTESI,
        SERBEST_SEMBOL_KATEGORILERI,
        fiyat_verisi_getir,
        teknik_gostergeleri_hesapla,
        destek_direnc_hesapla,
    )
    from data.veritabani import veritabanini_hazirla
    from data.kullanici_verileri import (
        favori_ekle,
        favorileri_getir,
        favori_sil,
        portfoye_ekle,
        portfoyu_getir,
        portfoy_kaydi_sil,
        alarm_kur,
        alarmlari_getir,
        alarmi_tetiklendi_isaretle,
        alarm_sil,
        sorgu_kaydet,
        sik_sorulan_konuyu_getir,
        hatirlatma_ekle,
        hatirlatmalari_getir,
        hatirlatma_sil,
    )
    from data.piyasa_takvimi import takvim_olaylarini_getir
    from ui.giris_ekrani import giris_ekranini_goster, hesap_ozetini_goster

    veritabanini_hazirla()

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

# --- Sidebar / Hesap ---------------------------------------------------------
if AJANLAR_YUKLENDI:
    if st.session_state.get("kullanici"):
        hesap_ozetini_goster()
    else:
        giris_ekranini_goster()
    st.sidebar.markdown("---")

# --- Sidebar / Menü ----------------------------------------------------------
st.sidebar.title("📊 Menü")
mod = st.sidebar.radio(
    "Bir mod seçin:",
    ("Genel Haber Modu", "Finansal Analiz Modu", "⭐ Favorilerim", "💼 Portföyüm", "📅 Piyasa Takvimi"),
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

    kullanici = st.session_state.get("kullanici")
    if AJANLAR_YUKLENDI and kullanici:
        try:
            sik_konu = sik_sorulan_konuyu_getir(kullanici["id"])
            if sik_konu:
                st.info(f"💡 Sık sorduğunuz **{sik_konu}** konusunda yeni gelişmeler olabilir.")
        except Exception:
            pass  # kişiselleştirme önerisi opsiyoneldir, sessizce atlanır

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

                    if kullanici:
                        try:
                            sorgu_kaydet(kullanici["id"], konu)
                        except Exception:
                            pass  # sorgu geçmişi kaydı opsiyoneldir, analiz sonucunu etkilemez

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
        son_konu = st.session_state.get("son_konu", "")

        st.markdown("---")

        if kullanici:
            if st.button("⭐ Bu Konuyu Favorilere Ekle"):
                try:
                    favori_ekle(kullanici["id"], "haber_konusu", son_konu)
                    st.success(f"'{son_konu}' favorilerinize eklendi.")
                except Exception:
                    st.error("😕 Favorilere eklenirken bir sorun oluştu.")

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
    st.write(
        "Bir varlık seçin; fiyat grafiği, teknik göstergeler, ilgili haberler "
        "ve piyasa duygu durumu tek ekranda sunulsun."
    )

    TUM_KATEGORILER = list(VARLIK_LISTESI.keys()) + list(SERBEST_SEMBOL_KATEGORILERI.keys()) if AJANLAR_YUKLENDI else []

    secilen_varlik_adi = None
    ticker = None
    finansal_sorgu = None

    if AJANLAR_YUKLENDI:
        col_kategori, col_varlik = st.columns(2)
        with col_kategori:
            kategori = st.selectbox("Varlık kategorisi", TUM_KATEGORILER)

        with col_varlik:
            if kategori in SERBEST_SEMBOL_KATEGORILERI:
                sembol = st.text_input(
                    "Sembol girin",
                    placeholder="Örn: THYAO, ASELS" if kategori == "Borsa - Hisse Senedi" else "Örn: BTC, ETH",
                ).strip().upper()
                if sembol:
                    secilen_varlik_adi = sembol
                    ticker = f"{sembol}{SERBEST_SEMBOL_KATEGORILERI[kategori]['ticker_eki']}"
                    finansal_sorgu = SERBEST_SEMBOL_KATEGORILERI[kategori]["sorgu_sablonu"].format(sembol=sembol)
            else:
                secilen_varlik_adi = st.selectbox("Varlık", list(VARLIK_LISTESI[kategori].keys()))
                ticker = VARLIK_LISTESI[kategori][secilen_varlik_adi]["ticker"]
                finansal_sorgu = VARLIK_LISTESI[kategori][secilen_varlik_adi]["sorgu"]

        col_zaman, col_gosterge = st.columns([1, 2])
        with col_zaman:
            zaman_dilimi_etiketi = st.selectbox(
                "Zaman dilimi", ["Son 7 Gün", "Son 30 Gün", "Son 90 Gün"], index=1
            )
            zaman_dilimi_gun = {"Son 7 Gün": 7, "Son 30 Gün": 30, "Son 90 Gün": 90}[zaman_dilimi_etiketi]
        with col_gosterge:
            gostergeler = st.multiselect(
                "Teknik göstergeler",
                ["MA200 (200 Günlük Ort.)", "Bollinger Bantları", "RSI", "MACD", "Stokastik Osilatör"],
                default=["MA200 (200 Günlük Ort.)", "Bollinger Bantları"],
            )

        finansal_analiz_et = st.button("📊 Analiz Et")

        if finansal_analiz_et:
            if not ticker:
                st.warning("Lütfen bir varlık seçin veya sembol girin.")
            else:
                try:
                    with st.spinner(f"'{secilen_varlik_adi}' için fiyat verisi çekiliyor..."):
                        fiyat_df = fiyat_verisi_getir(ticker, zaman_dilimi_gun)
                        fiyat_df = teknik_gostergeleri_hesapla(fiyat_df)
                        destek, direnc = destek_direnc_hesapla(fiyat_df)

                    with st.spinner(f"'{secilen_varlik_adi}' hakkında haberler toplanıyor..."):
                        finansal_haberler = haberleri_getir(finansal_sorgu)

                    guncel = fiyat_df.iloc[-1]
                    onceki = fiyat_df.iloc[-2] if len(fiyat_df) > 1 else guncel
                    gunluk_degisim_yuzde = ((guncel["Kapanis"] - onceki["Kapanis"]) / onceki["Kapanis"]) * 100

                    fiyat_bilgisi = {
                        "guncel_fiyat": round(float(guncel["Kapanis"]), 4),
                        "gunluk_degisim_yuzde": round(float(gunluk_degisim_yuzde), 2),
                    }

                    with st.spinner("Piyasa duygu durumu ve özet oluşturuluyor..."):
                        finansal_analiz = finansal_analiz_yap(secilen_varlik_adi, fiyat_bilgisi, finansal_haberler)

                    # Sonraki yeniden çalıştırmalarda (rerun) kaybolmaması için sakla
                    st.session_state["finans_varlik_adi"] = secilen_varlik_adi
                    st.session_state["finans_ticker"] = ticker
                    st.session_state["finans_fiyat_df"] = fiyat_df.tail(zaman_dilimi_gun)
                    st.session_state["finans_destek"] = destek
                    st.session_state["finans_direnc"] = direnc
                    st.session_state["finans_fiyat_bilgisi"] = fiyat_bilgisi
                    st.session_state["finans_haberler"] = finansal_haberler
                    st.session_state["finans_analiz"] = finansal_analiz
                    st.session_state["finans_gostergeler"] = gostergeler

                except ValueError as e:
                    st.error(f"🚫 Geçersiz girdi: {e}")
                except EnvironmentError as e:
                    st.error(f"🔑 API anahtarı sorunu: {e}")
                except RuntimeError as e:
                    st.error(
                        "🌐 Fiyat verisi veya haber servisine bağlanırken bir sorun oluştu. "
                        "Lütfen internet bağlantınızı ve API anahtarlarınızı kontrol edip tekrar deneyin."
                    )
                except Exception:
                    st.error("😕 Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

    # --- Sonuçları göster (varsa) --------------------------------------------
    if AJANLAR_YUKLENDI and st.session_state.get("finans_analiz"):
        varlik_adi = st.session_state["finans_varlik_adi"]
        fiyat_df = st.session_state["finans_fiyat_df"]
        destek = st.session_state["finans_destek"]
        direnc = st.session_state["finans_direnc"]
        fiyat_bilgisi = st.session_state["finans_fiyat_bilgisi"]
        finansal_haberler = st.session_state["finans_haberler"]
        finansal_analiz = st.session_state["finans_analiz"]
        secili_gostergeler = st.session_state.get("finans_gostergeler", [])

        st.markdown("---")
        st.markdown(f"### 📊 {varlik_adi} — Fiyat Özeti")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Güncel Fiyat", f"{fiyat_bilgisi['guncel_fiyat']:.4f}")
        col2.metric("Günlük Değişim", f"{fiyat_bilgisi['gunluk_degisim_yuzde']:+.2f}%")
        col3.metric("Destek Seviyesi", f"{destek:.4f}")
        col4.metric("Direnç Seviyesi", f"{direnc:.4f}")

        # --- Fiyat grafiği (MA200 / Bollinger aynı ölçekte üstüne biner) ---
        st.markdown("#### 📈 Fiyat Grafiği")
        fiyat_kolonlari = ["Kapanis"]
        if "MA200 (200 Günlük Ort.)" in secili_gostergeler:
            fiyat_kolonlari.append("MA200")
        if "Bollinger Bantları" in secili_gostergeler:
            fiyat_kolonlari += ["Bollinger_Ust", "Bollinger_Alt"]
        st.line_chart(fiyat_df[fiyat_kolonlari])

        # --- Farklı ölçekli göstergeler ayrı grafiklerde ---
        if "RSI" in secili_gostergeler:
            st.markdown("#### RSI (14 Günlük)")
            st.line_chart(fiyat_df[["RSI"]])

        if "MACD" in secili_gostergeler:
            st.markdown("#### MACD")
            st.line_chart(fiyat_df[["MACD", "MACD_Sinyal"]])

        if "Stokastik Osilatör" in secili_gostergeler:
            st.markdown("#### Stokastik Osilatör")
            st.line_chart(fiyat_df[["Stokastik_K", "Stokastik_D"]])

        # --- Piyasa duygu durumu ---
        st.markdown("### 🎯 Piyasa Duygu Durumu")
        skor = finansal_analiz.get("sentiment_skoru", 0)
        durum = finansal_analiz.get("sentiment_durumu", "Belirlenemedi")
        st.metric(label="Sentiment Skoru (-1 ile +1 arası)", value=f"{skor:+.2f}", delta=durum, delta_color="off")

        # --- Sade dil özeti ---
        st.markdown("### 📌 Sade Dil Özeti")
        st.info(finansal_analiz.get("ozet", "Özet oluşturulamadı."))

        # --- Hesap gerektiren aksiyonlar: favori / alarm / portföy ---
        finans_kullanici = st.session_state.get("kullanici")
        st.markdown("### ⭐ Kaydet ve Takip Et")
        if not finans_kullanici:
            st.caption("Favorilere ekleme, fiyat alarmı kurma ve portföye ekleme için giriş yapmalısınız.")
        else:
            ticker_bilgisi = st.session_state.get("finans_ticker", "")
            sekme_favori, sekme_alarm, sekme_portfoy = st.tabs(
                ["⭐ Favorilere Ekle", "🔔 Alarm Kur", "➕ Portföye Ekle"]
            )

            with sekme_favori:
                if st.button("Favorilere Ekle", key="finans_favori_buton"):
                    try:
                        favori_ekle(finans_kullanici["id"], "finansal_varlik", varlik_adi, ticker_bilgisi)
                        st.success(f"'{varlik_adi}' favorilerinize eklendi.")
                    except Exception:
                        st.error("😕 Favorilere eklenirken bir sorun oluştu.")

            with sekme_alarm:
                with st.form("alarm_formu"):
                    hedef_fiyat = st.number_input("Hedef fiyat", min_value=0.0, format="%.4f")
                    yon = st.radio("Ne zaman bildirim alayım?", ["Üstüne çıktığında", "Altına düştüğünde"])
                    alarm_gonder = st.form_submit_button("Alarm Kur")
                if alarm_gonder:
                    try:
                        yon_kodu = "ustune_ciktiginda" if yon == "Üstüne çıktığında" else "altina_dustugunde"
                        alarm_kur(finans_kullanici["id"], varlik_adi, ticker_bilgisi, hedef_fiyat, yon_kodu)
                        st.success(f"'{varlik_adi}' için {hedef_fiyat:.4f} seviyesinde alarm kuruldu.")
                    except Exception:
                        st.error("😕 Alarm kurulurken bir sorun oluştu.")

            with sekme_portfoy:
                with st.form("portfoy_formu"):
                    miktar = st.number_input("Miktar", min_value=0.0, format="%.4f")
                    maliyet = st.number_input("Maliyet fiyatı (birim başına)", min_value=0.0, format="%.4f")
                    portfoy_gonder = st.form_submit_button("Portföye Ekle")
                if portfoy_gonder:
                    try:
                        portfoye_ekle(finans_kullanici["id"], varlik_adi, ticker_bilgisi, miktar, maliyet)
                        st.success(f"'{varlik_adi}' portföyünüze eklendi.")
                    except Exception:
                        st.error("😕 Portföye eklenirken bir sorun oluştu.")

        # --- Finansal haber akışı ---
        if finansal_haberler:
            with st.expander(f"📰 İlgili Haberler ({len(finansal_haberler)} adet)"):
                for haber in finansal_haberler:
                    st.markdown(
                        f"**{haber.get('Başlık', 'Başlık yok')}**  \n"
                        f"🗞️ {haber.get('Kaynak', 'Bilinmiyor')} · 🗓️ {haber.get('Tarih', 'Tarih yok')}  \n"
                        f"🔗 [{haber.get('URL', '')}]({haber.get('URL', '')})"
                    )
                    st.markdown("---")

        st.caption(
            "Veriler yfinance üzerinden çekilmiştir, gerçek zamanlı borsa akışı değildir "
            "ve birkaç dakika gecikmeli olabilir. Teknik göstergeler yalnızca bilgilendirme "
            "amaçlıdır; bir sinyal veya tavsiye olarak yorumlanmamalıdır."
        )

    # --- Kalıcı yasal uyarı (her zaman görünür) ------------------------------
    st.markdown("---")
    st.warning(
        "⚠️ **Yasal Uyarı:** Bu içerik yalnızca bilgilendirme amaçlıdır. "
        "Yatırım tavsiyesi değildir. Yatırım kararlarınız için lütfen "
        "lisanslı bir yatırım danışmanına başvurun."
    )


# =============================================================================
# ⭐ FAVORİLERİM
# =============================================================================
elif mod == "⭐ Favorilerim":
    st.subheader("⭐ Favorilerim")

    kullanici = st.session_state.get("kullanici")
    if not AJANLAR_YUKLENDI:
        st.error("Ajan modülleri yüklenemediği için bu bölüm kullanılamıyor.")
    elif not kullanici:
        st.info("Favorilerinizi görmek ve yönetmek için lütfen sol menüden giriş yapın veya hesap oluşturun.")
    else:
        try:
            favori_konular = favorileri_getir(kullanici["id"], tur="haber_konusu")
            favori_varliklar = favorileri_getir(kullanici["id"], tur="finansal_varlik")
        except Exception:
            favori_konular, favori_varliklar = [], []
            st.error("😕 Favoriler yüklenirken bir sorun oluştu.")

        st.markdown("### 📰 Favori Haber Konuları")
        if not favori_konular:
            st.caption("Henüz favori haber konunuz yok. Genel Haber Modu'nda bir analiz yapıp favorilere ekleyebilirsiniz.")
        else:
            for favori in favori_konular:
                col_ad, col_sil = st.columns([5, 1])
                col_ad.write(f"🔖 {favori['deger']}")
                if col_sil.button("Sil", key=f"favori_konu_sil_{favori['id']}"):
                    favori_sil(favori["id"], kullanici["id"])
                    st.rerun()

        st.markdown("### 💹 Favori Finansal Varlıklar")
        if not favori_varliklar:
            st.caption("Henüz favori varlığınız yok. Finansal Analiz Modu'nda bir analiz yapıp favorilere ekleyebilirsiniz.")
        else:
            for favori in favori_varliklar:
                col_ad, col_sil = st.columns([5, 1])
                col_ad.write(f"🔖 {favori['deger']} ({favori.get('ek_bilgi') or '—'})")
                if col_sil.button("Sil", key=f"favori_varlik_sil_{favori['id']}"):
                    favori_sil(favori["id"], kullanici["id"])
                    st.rerun()

        st.markdown("### 🔔 Fiyat Alarmlarım")
        try:
            alarmlar = alarmlari_getir(kullanici["id"])
        except Exception:
            alarmlar = []
            st.error("😕 Alarmlar yüklenirken bir sorun oluştu.")

        if not alarmlar:
            st.caption("Henüz kurulu bir fiyat alarmınız yok. Finansal Analiz Modu'nda bir varlık analiz edip alarm kurabilirsiniz.")
        else:
            if st.button("🔄 Alarmlarımı Şimdi Kontrol Et"):
                with st.spinner("Güncel fiyatlar kontrol ediliyor..."):
                    for alarm in alarmlar:
                        if alarm["tetiklendi"]:
                            continue
                        try:
                            guncel_veri = fiyat_verisi_getir(alarm["ticker"], gun_sayisi=7)
                            guncel_fiyat = float(guncel_veri.iloc[-1]["Kapanis"])
                            hedefe_ulasti = (
                                alarm["yon"] == "ustune_ciktiginda" and guncel_fiyat >= alarm["hedef_fiyat"]
                            ) or (
                                alarm["yon"] == "altina_dustugunde" and guncel_fiyat <= alarm["hedef_fiyat"]
                            )
                            if hedefe_ulasti:
                                alarmi_tetiklendi_isaretle(alarm["id"])
                                st.success(
                                    f"🔔 {alarm['varlik_adi']} hedef seviyeye ulaştı! "
                                    f"Güncel fiyat: {guncel_fiyat:.4f} (hedef: {alarm['hedef_fiyat']:.4f})"
                                )
                        except Exception:
                            st.warning(f"'{alarm['varlik_adi']}' için güncel fiyat kontrol edilemedi.")
                st.rerun()

            for alarm in alarmlar:
                yon_metni = "üstüne çıktığında" if alarm["yon"] == "ustune_ciktiginda" else "altına düştüğünde"
                durum_etiketi = "✅ Tetiklendi" if alarm["tetiklendi"] else "⏳ Aktif"
                col_ad, col_sil = st.columns([5, 1])
                col_ad.write(
                    f"{durum_etiketi} · **{alarm['varlik_adi']}** {alarm['hedef_fiyat']:.4f} seviyesinin {yon_metni}"
                )
                if col_sil.button("Sil", key=f"alarm_sil_{alarm['id']}"):
                    alarm_sil(alarm["id"], kullanici["id"])
                    st.rerun()


# =============================================================================
# 💼 PORTFÖYÜM
# =============================================================================
elif mod == "💼 Portföyüm":
    st.subheader("💼 Portföyüm")

    kullanici = st.session_state.get("kullanici")
    if not AJANLAR_YUKLENDI:
        st.error("Ajan modülleri yüklenemediği için bu bölüm kullanılamıyor.")
    elif not kullanici:
        st.info("Portföyünüzü görmek ve yönetmek için lütfen sol menüden giriş yapın veya hesap oluşturun.")
    else:
        with st.expander("➕ Portföye Yeni Varlık Ekle"):
            with st.form("portfoy_ekleme_formu"):
                varlik_adi_girisi = st.text_input("Varlık adı (örn: THYAO, BTC, USD/TRY)")
                ticker_girisi = st.text_input(
                    "yfinance sembolü (örn: THYAO.IS, BTC-USD, TRY=X)",
                    help="Finansal Analiz Modu'nda kullanılan sembol formatıyla aynı olmalı.",
                )
                miktar_girisi = st.number_input("Miktar", min_value=0.0, format="%.4f")
                maliyet_girisi = st.number_input("Maliyet fiyatı (birim başına)", min_value=0.0, format="%.4f")
                ekle_gonder = st.form_submit_button("Portföye Ekle")

            if ekle_gonder:
                if not varlik_adi_girisi.strip() or not ticker_girisi.strip():
                    st.warning("Lütfen varlık adı ve sembolü girin.")
                else:
                    try:
                        portfoye_ekle(
                            kullanici["id"], varlik_adi_girisi.strip(), ticker_girisi.strip(), miktar_girisi, maliyet_girisi
                        )
                        st.success(f"'{varlik_adi_girisi}' portföyünüze eklendi.")
                        st.rerun()
                    except Exception:
                        st.error("😕 Portföye eklenirken bir sorun oluştu.")

        try:
            portfoy_kayitlari = portfoyu_getir(kullanici["id"])
        except Exception:
            portfoy_kayitlari = []
            st.error("😕 Portföy yüklenirken bir sorun oluştu.")

        if not portfoy_kayitlari:
            st.caption("Portföyünüzde henüz bir varlık yok. Yukarıdaki formu kullanarak ekleyebilirsiniz.")
        else:
            toplam_maliyet = 0.0
            toplam_guncel_deger = 0.0

            st.markdown("### 📋 Varlıklarım")
            for kayit in portfoy_kayitlari:
                col_bilgi, col_deger, col_sil = st.columns([3, 2, 1])
                maliyet_toplam = kayit["miktar"] * kayit["maliyet_fiyati"]
                toplam_maliyet += maliyet_toplam

                col_bilgi.write(f"**{kayit['varlik_adi']}** · {kayit['miktar']} adet · maliyet {kayit['maliyet_fiyati']:.4f}")

                try:
                    guncel_veri = fiyat_verisi_getir(kayit["ticker"], gun_sayisi=7)
                    guncel_fiyat = float(guncel_veri.iloc[-1]["Kapanis"])
                    guncel_deger = kayit["miktar"] * guncel_fiyat
                    toplam_guncel_deger += guncel_deger
                    kar_zarar = guncel_deger - maliyet_toplam
                    kar_zarar_yuzde = (kar_zarar / maliyet_toplam * 100) if maliyet_toplam > 0 else 0
                    col_deger.metric(
                        "Güncel Değer", f"{guncel_deger:,.2f}", delta=f"{kar_zarar_yuzde:+.2f}%", delta_color="normal"
                    )
                except Exception:
                    col_deger.caption("Güncel fiyat alınamadı")
                    toplam_guncel_deger += maliyet_toplam

                if col_sil.button("Sil", key=f"portfoy_sil_{kayit['id']}"):
                    portfoy_kaydi_sil(kayit["id"], kullanici["id"])
                    st.rerun()

            st.markdown("---")
            st.markdown("### 📊 Portföy Özeti")
            col1, col2, col3 = st.columns(3)
            col1.metric("Toplam Maliyet", f"{toplam_maliyet:,.2f}")
            col2.metric("Toplam Güncel Değer", f"{toplam_guncel_deger:,.2f}")
            genel_kar_zarar = toplam_guncel_deger - toplam_maliyet
            genel_yuzde = (genel_kar_zarar / toplam_maliyet * 100) if toplam_maliyet > 0 else 0
            col3.metric("Toplam Kâr/Zarar", f"{genel_kar_zarar:,.2f}", delta=f"{genel_yuzde:+.2f}%")

        st.markdown("---")
        st.caption(
            "Bu bölüm yalnızca kendi girdiğiniz verilere dayalı bir takip aracıdır; gerçek bir "
            "borsa hesabına bağlanmaz, gerçek alım/satım emri göndermez ve portföy önerisi sunmaz."
        )
        st.warning(
            "⚠️ **Yasal Uyarı:** Bu içerik yalnızca bilgilendirme amaçlıdır. "
            "Yatırım tavsiyesi değildir. Yatırım kararlarınız için lütfen "
            "lisanslı bir yatırım danışmanına başvurun."
        )


# =============================================================================
# 📅 PİYASA TAKVİMİ
# =============================================================================
elif mod == "📅 Piyasa Takvimi":
    st.subheader("📅 Piyasa Takvimi")
    st.write(
        "TCMB PPK toplantı tarihleri, TÜİK enflasyon açıklamaları gibi önemli "
        "finansal takvim olaylarını listeler. Bu takvim olayların sonucunu "
        "tahmin etmez, sadece tarih/olay bilgisini sunar."
    )

    if not AJANLAR_YUKLENDI:
        st.error("Ajan modülleri yüklenemediği için bu bölüm kullanılamıyor.")
    else:
        kullanici = st.session_state.get("kullanici")

        try:
            takvim_olaylari = takvim_olaylarini_getir()
        except Exception:
            takvim_olaylari = []
            st.error("😕 Takvim olayları yüklenirken bir sorun oluştu.")

        hatirlatilan_etkinlikler = set()
        if kullanici:
            try:
                hatirlatmalar = hatirlatmalari_getir(kullanici["id"])
                hatirlatilan_etkinlikler = {(h["etkinlik_adi"], h["etkinlik_tarihi"]) for h in hatirlatmalar}
            except Exception:
                hatirlatmalar = []
        else:
            hatirlatmalar = []

        st.caption(
            "ℹ️ Tarihler TCMB/TÜİK'in resmi yayın örüntüsüne göre yaklaşık olarak "
            "hesaplanmıştır; kesin tarihler için ilgili kurumların resmi takvimine bakınız."
        )

        st.markdown("### 🗓️ Yaklaşan Olaylar")
        if not takvim_olaylari:
            st.caption("Gösterilecek yaklaşan bir takvim olayı bulunamadı.")
        else:
            for olay in takvim_olaylari:
                col_bilgi, col_aksiyon = st.columns([4, 1])
                with col_bilgi:
                    st.markdown(
                        f"**{olay['etkinlik_adi']}** · 🏷️ {olay['kategori']}  \n"
                        f"📆 {olay['tarih'].strftime('%d.%m.%Y')} · ⏳ {olay['kalan_gun']} gün kaldı  \n"
                        f"{olay['aciklama']}"
                    )
                with col_aksiyon:
                    if not kullanici:
                        st.caption("Hatırlatma için giriş yapın")
                    else:
                        anahtar = (olay["etkinlik_adi"], olay["tarih"].isoformat())
                        if anahtar in hatirlatilan_etkinlikler:
                            st.caption("🔔 Hatırlatma kuruldu")
                        elif st.button("🔔 Hatırlat", key=f"hatirlat_{olay['etkinlik_adi']}_{olay['tarih'].isoformat()}"):
                            hatirlatma_ekle(kullanici["id"], olay["etkinlik_adi"], olay["tarih"])
                            st.rerun()
                st.markdown("---")

        if kullanici:
            st.markdown("### 🔔 Hatırlatmalarım")
            if not hatirlatmalar:
                st.caption("Henüz kurulu bir hatırlatmanız yok.")
            else:
                for hatirlatma in hatirlatmalar:
                    col_ad, col_sil = st.columns([5, 1])
                    col_ad.write(f"🔖 {hatirlatma['etkinlik_adi']} — {hatirlatma['etkinlik_tarihi']}")
                    if col_sil.button("Sil", key=f"hatirlatma_sil_{hatirlatma['id']}"):
                        hatirlatma_sil(hatirlatma["id"], kullanici["id"])
                        st.rerun()
