from itertools import permutations

import networkx as nx
import osmnx as ox

from .build import StreetGraph


class RouteGraph:
    """
    Computes pairwise shortest paths and finds the optimal pickup route
    over a snapped street graph.

    Parameters
    ----------
    street_graph : StreetGraph
        A ``StreetGraph`` instance with ``snap_nodes()`` already called.
    criteria : str, optional
        Routing criteria: ``"distance"`` (default) or ``"time"``.

    Attributes
    ----------
    shortest_path_dict : dict
        Populated by ``compute_paths()``.
        Keys are ``(source, sink)`` node ID tuples, values are
        ``{"distance": float (km), "path": list}``.
    best_order : list or None
        Populated by ``find_optimal()``.
        Optimal sequence of node IDs: ``[source, ..., sink]``.
    best_distance : float or None
        Total distance of the optimal route in km.

    Examples
    --------
    >>> sg = StreetGraph("La Reina, Santiago, Chile")
    >>> sg.snap_nodes(nodes_dict)
    >>> rg = RouteGraph(sg, criteria="distance")
    >>> rg.compute_paths()
    >>> rg.find_optimal()
    >>> rg.best_order
    [1, 862301, 862302, 862303, -1]
    >>> rg.best_distance
    4.71
    """

    def __init__(self, street_graph: StreetGraph, criteria: str = "distance"):
        self.street_graph = street_graph
        self.criteria = criteria
        self.shortest_path_dict: dict = {}
        self.best_order: list | None = None
        self.best_distance: float | None = None

    def compute_paths(self) -> None:
        """
        Compute shortest paths between all pairs of snapped nodes.

        Reads ``self.street_graph.G`` and ``self.street_graph.nodes_name_id``.
        Populates ``self.shortest_path_dict``.
        """
        weight = "length" if self.criteria == "distance" else "travel_time"
        nodes_list = list(self.street_graph.nodes_name_id.values())
        G = self.street_graph.G

        for source_node in nodes_list:
            for sink_node in nodes_list:
                path = ox.shortest_path(G, source_node, sink_node, weight=weight)
                try:
                    distance = round(nx.path_weight(G, path, weight="length") / 1000, 2)
                    self.shortest_path_dict[(source_node, sink_node)] = {
                        "distance": distance,
                        "path": path,
                    }
                except (TypeError, nx.NetworkXNoPath, nx.NodeNotFound):
                    pass

    def find_optimal(self) -> None:
        """
        Find the optimal visiting order for all intermediate nodes using brute force.
        Fixed start (source ID=1) and fixed end (sink ID=-1), no return to start.

        Reads ``self.shortest_path_dict`` (requires ``compute_paths()`` first).
        Populates ``self.best_order`` and ``self.best_distance``.
        """
        source = StreetGraph.SOURCE_ID
        sink = StreetGraph.SINK_ID
        # Creates list of nodes that are not sink nor source
        intermediate_nodes = [
            node_id
            for node_id in self.street_graph.nodes_name_id.values()
            if node_id not in (source, sink)
        ]

        best_distance = float("inf")
        best_order = None

        for perm in permutations(intermediate_nodes):
            full_route = [source] + list(perm) + [sink]
            try:
                total_distance = sum(
                    self.shortest_path_dict[(full_route[i], full_route[i + 1])]["distance"]
                    for i in range(len(full_route) - 1)
                )
            except KeyError:
                continue

            if total_distance < best_distance:
                best_distance = total_distance
                best_order = full_route

        self.best_order = best_order
        self.best_distance = best_distance
