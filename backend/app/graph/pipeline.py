"""Compilación del pipeline RAG (LangGraph).

Ruta: START -> (rewrite_query si hay historial) -> retrieve -> generate -> END.
"""
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import generate, retrieve, rewrite_query
from app.graph.state import RAGState


def _route_entry(state: RAGState) -> str:
    # rewrite_query solo tiene sentido si hay historial que resolver.
    return "rewrite_query" if state.get("history") else "retrieve"


def build_graph():
    builder = StateGraph(RAGState)
    builder.add_node("rewrite_query", rewrite_query)
    builder.add_node("retrieve", retrieve)
    builder.add_node("generate", generate)

    builder.add_conditional_edges(
        START,
        _route_entry,
        {"rewrite_query": "rewrite_query", "retrieve": "retrieve"},
    )
    builder.add_edge("rewrite_query", "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


# Grafo compilado (singleton a nivel de módulo).
graph = build_graph()
