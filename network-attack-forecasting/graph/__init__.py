"""
Network Graph State Generator for NetForecast AI.

Constructs topological temporal graphs G_t from flow records,
modeling communicating entities as nodes and network flows as edges.
"""

from graph.network_graph import NetworkGraphBuilder, FlowGraphSnapshot

__all__ = ["NetworkGraphBuilder", "FlowGraphSnapshot"]
