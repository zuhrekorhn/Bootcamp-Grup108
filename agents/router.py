"""
router.py
---------
Kullanıcının girdiği serbest metin konuyu analiz edip, bunun bir finansal
varlığa mı yoksa genel bir haber konusuna mı karşılık geldiğine karar veren
ve LangGraph akışını yöneten modül.
"""

import re
from data.finans_verisi import VARLIK_LISTESI


def _normalize(metin: str) -> str:
    """Karşılaştırma için metni sadeleştirir: küçük harfe çevirir, boşluk/noktalama farklarını yok sayar."""
    return re.sub(r"[^a-z0-9çğıöşü]", "", metin.lower())

def konu_varlik_eslestir(konu: str):
    konu_normalize = _normalize(konu)
    for kategori, varliklar in VARLIK_LISTESI.items():
        for varlik_adi, bilgi in varliklar.items():
            varlik_normalize = _normalize(varlik_adi)
            if varlik_normalize in konu_normalize or konu_normalize in varlik_normalize:
                return kategori, varlik_adi, bilgi["ticker"], bilgi["sorgu"]
    return None


def router_node(state: dict) -> dict:
    """Konunun haber mi finans mı olduğuna karar verir."""
    eslesme = konu_varlik_eslestir(state["konu"])
    if eslesme:
        varlik_adi, ticker, finansal_sorgu = eslesme
        state["mod"] = "finans"
        state["varlik_adi"] = varlik_adi
        state["ticker"] = ticker
        state["finansal_sorgu"] = finansal_sorgu
    else:
        state["mod"] = "haber"
    return state


def yonlendir(state: dict) -> str:
    return state["mod"]