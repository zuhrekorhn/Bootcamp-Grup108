FINANSAL_ENSTRUMANLAR = {
    "dolar": "USDTRY=X",
    "euro": "EURTRY=X",
    "bitcoin": "BTC-USD",
    "altın": "GC=F",
    "borsa": "XU100.IS",
}

def konu_sembol_bul(konu: str):
    """Konu metninde geçen finansal anahtar kelimeye karşılık gelen sembolü döndürür."""
    konu_kucuk = konu.lower()
    for kelime, sembol in FINANSAL_ENSTRUMANLAR.items():
        if kelime in konu_kucuk:
            return sembol
    return None

def router_node(state: dict) -> dict:
    konu = state["konu"].lower()
    if any(kelime in konu for kelime in FINANSAL_ENSTRUMANLAR.keys()):
        state["mod"] = "finans"
    else:
        state["mod"] = "haber"
    return state

def yonlendir(state: dict) -> str:
    return state["mod"]