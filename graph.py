from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.router import router_node, yonlendir
from agents.haber_ajani import haber_ajani
from agents.finans_ajani import finans_ajani

class AjanState(TypedDict):
    konu: str
    mod: str
    sonuc: str
    kaynaklar: list
    son_fiyat: float
    degisim_yuzde: float
    grafik_verisi: object

def graph_olustur():
    graph = StateGraph(AjanState)
    graph.add_node("router", router_node)
    graph.add_node("haber", haber_ajani)
    graph.add_node("finans", finans_ajani)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", yonlendir, {"haber": "haber", "finans": "finans"})
    graph.add_edge("haber", END)
    graph.add_edge("finans", END)

    return graph.compile()