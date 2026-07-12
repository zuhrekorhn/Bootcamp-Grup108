from graph import graph_olustur

app_graph = graph_olustur()

sonuc = app_graph.invoke({"konu": "dolar kuru", "mod": "", "sonuc": "", "kaynaklar": [], "son_fiyat": 0, "degisim_yuzde": 0, "grafik_verisi": None})
print(f"[{sonuc['mod'].upper()}] {sonuc['sonuc']}")

print("\n" + "="*50 + "\n")

sonuc2 = app_graph.invoke({"konu": "Milli Voleybol Takımı", "mod": "", "sonuc": "", "kaynaklar": [], "son_fiyat": 0, "degisim_yuzde": 0, "grafik_verisi": None})
print(f"[{sonuc2['mod'].upper()}] {sonuc2['sonuc']}")