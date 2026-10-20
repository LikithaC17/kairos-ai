"""
Network Graph State Construction Module for NetForecast AI.

Constructs topological graph G_t from windowed network flow records:
- Nodes: IP addresses (devices / endpoints)
- Edges: Communication flows between IP pairs
- Attributes: packets, bytes, duration, protocol, ports, timing metrics
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import networkx as nx
import numpy as np
import pandas as pd


@dataclass
class FlowGraphSnapshot:
    """Serializable snapshot of a network graph G_t."""
    timestamp: float
    num_nodes: int
    num_edges: int
    density: float
    max_degree_node: str
    max_degree: int
    star_score: float
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    graph: Optional[nx.DiGraph] = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "density": self.density,
            "max_degree_node": self.max_degree_node,
            "max_degree": self.max_degree,
            "star_score": self.star_score,
            "nodes": self.nodes,
            "edges": self.edges,
        }


class NetworkGraphBuilder:
    """
    Constructs and analyzes temporal network graphs from flow telemetry.
    """

    def __init__(self, directed: bool = True):
        self.directed = directed

    def build_graph(self, flows: Union[pd.DataFrame, List[Dict[str, Any]]]) -> nx.DiGraph:
        """
        Builds a NetworkX directed graph from flow observations.
        """
        if isinstance(flows, pd.DataFrame):
            records = flows.to_dict(orient="records")
        else:
            records = flows

        G = nx.DiGraph() if self.directed else nx.Graph()

        for rec in records:
            src_ip = str(rec.get("src_ip", "0.0.0.0"))
            dst_ip = str(rec.get("dst_ip", "0.0.0.0"))
            bytes_val = float(rec.get("byte_count", rec.get("tot_fwd_bytes", 0)))
            pkts_val = float(rec.get("packet_count", rec.get("tot_fwd_pkts", 1)))
            duration = float(rec.get("flow_duration", 0.0))
            proto = str(rec.get("protocol", "TCP"))
            src_port = int(rec.get("src_port", 0))
            dst_port = int(rec.get("dst_port", 0))
            ts = float(rec.get("timestamp", 0.0))

            # Initialize node metrics
            if not G.has_node(src_ip):
                G.add_node(src_ip, bytes_sent=0.0, bytes_recv=0.0, pkts_sent=0.0, pkts_recv=0.0)
            if not G.has_node(dst_ip):
                G.add_node(dst_ip, bytes_sent=0.0, bytes_recv=0.0, pkts_sent=0.0, pkts_recv=0.0)

            # Update node statistics
            G.nodes[src_ip]["bytes_sent"] += bytes_val
            G.nodes[src_ip]["pkts_sent"] += pkts_val
            G.nodes[dst_ip]["bytes_recv"] += bytes_val
            G.nodes[dst_ip]["pkts_recv"] += pkts_val

            # Add or update edge
            if G.has_edge(src_ip, dst_ip):
                G[src_ip][dst_ip]["weight"] += bytes_val
                G[src_ip][dst_ip]["packet_count"] += pkts_val
                G[src_ip][dst_ip]["flow_count"] += 1
            else:
                G.add_edge(
                    src_ip,
                    dst_ip,
                    weight=bytes_val,
                    packet_count=pkts_val,
                    flow_count=1,
                    duration=duration,
                    protocol=proto,
                    src_port=src_port,
                    dst_port=dst_port,
                    last_timestamp=ts,
                )

        return G

    def extract_snapshot(self, flows: Union[pd.DataFrame, List[Dict[str, Any]]]) -> FlowGraphSnapshot:
        """
        Builds the graph and extracts graph-theoretic structural metrics.
        """
        G = self.build_graph(flows)
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()

        if num_nodes == 0:
            return FlowGraphSnapshot(
                timestamp=0.0,
                num_nodes=0,
                num_edges=0,
                density=0.0,
                max_degree_node="none",
                max_degree=0,
                star_score=0.0,
                nodes=[],
                edges=[],
                graph=G,
            )

        density = round(float(nx.density(G)), 4)
        degrees = dict(G.degree())
        sorted_degrees = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        max_deg_node, max_deg = sorted_degrees[0] if sorted_degrees else ("none", 0)

        # Star topology metric: ratio of max node degree to total edges
        star_score = round(float(max_deg / max(1, num_edges)), 3)

        # Timestamp from flows
        if isinstance(flows, pd.DataFrame) and "timestamp" in flows.columns:
            ts = float(flows["timestamp"].iloc[-1])
        elif isinstance(flows, list) and flows and "timestamp" in flows[-1]:
            ts = float(flows[-1]["timestamp"])
        else:
            ts = 0.0

        # Node representation for UI
        node_list = []
        for n, attrs in G.nodes(data=True):
            node_list.append({
                "id": n,
                "degree": G.degree(n),
                "in_degree": G.in_degree(n) if G.is_directed() else G.degree(n),
                "out_degree": G.out_degree(n) if G.is_directed() else G.degree(n),
                "bytes_sent": attrs.get("bytes_sent", 0.0),
                "bytes_recv": attrs.get("bytes_recv", 0.0),
            })

        # Edge representation for UI
        edge_list = []
        for u, v, attrs in G.edges(data=True):
            edge_list.append({
                "source": u,
                "target": v,
                "weight": attrs.get("weight", 0.0),
                "packet_count": attrs.get("packet_count", 0.0),
                "flow_count": attrs.get("flow_count", 1),
                "protocol": attrs.get("protocol", "TCP"),
            })

        return FlowGraphSnapshot(
            timestamp=ts,
            num_nodes=num_nodes,
            num_edges=num_edges,
            density=density,
            max_degree_node=max_deg_node,
            max_degree=max_deg,
            star_score=star_score,
            nodes=node_list,
            edges=edge_list,
            graph=G,
        )
