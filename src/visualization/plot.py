import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
from matplotlib import cm
from src.graph.routing import RouteGraph


class RoutePlotter:
    """
    Renders the optimal pickup route on a street graph.

    Parameters
    ----------
    route_graph : RouteGraph
        A ``RouteGraph`` instance with ``compute_paths()`` and
        ``find_optimal()`` already called.

    Attributes
    ----------
    fig : matplotlib.figure.Figure
        Populated by ``plot()``.
    ax : matplotlib.axes.Axes
        Populated by ``plot()``.

    Examples
    --------
    >>> plotter = RoutePlotter(route_graph)
    >>> plotter.plot()
    >>> plotter.fig  # pass to st.pyplot()
    """

    def __init__(self, route_graph: RouteGraph):
        self.route_graph = route_graph
        self.fig = None
        self.ax = None

    def plot(self) -> None:
        """
        Render the full route — base graph, colored segments, stop markers
        and labels, and final destination star.
        """
        rg = self.route_graph
        id_to_name = {v: k for k, v in rg.street_graph.nodes_name_id.items()}
        colors = cm.rainbow(np.linspace(0, 1, len(rg.best_order) - 1))

        self._plot_base_graph()

        for i in range(len(rg.best_order) - 1):
            self._plot_segment(i, colors[i])
            self._annotate_stop(i, colors[i], id_to_name)

        self._annotate_final(id_to_name)

        plt.title(
            f"Optimal route — {rg.best_distance} km",
            fontsize=12,
            fontweight="bold",
        )

    def _plot_base_graph(self) -> None:
        """Draw the street network as a neutral background."""
        self.fig, self.ax = ox.plot_graph(
            self.route_graph.street_graph.G,
            show=False,
            close=False,
            node_size=0,
            bgcolor="white",
            edge_color="#cccccc",
            edge_linewidth=0.5,
        )

    def _plot_segment(self, i: int, color) -> None:
        """Draw the i-th route segment in ``color``."""
        rg = self.route_graph
        segment = rg.shortest_path_dict[(rg.best_order[i], rg.best_order[i + 1])]["path"]
        ox.plot_graph_route(
            rg.street_graph.G,
            segment,
            route_linewidth=4,
            route_color=color,
            node_size=0,
            bgcolor=None,
            ax=self.ax,
            show=False,
            close=False,
        )

    def _annotate_stop(self, i: int, color, id_to_name: dict) -> None:
        """Place a numbered scatter marker and label at stop i."""
        rg = self.route_graph
        node = rg.street_graph.G.nodes[rg.best_order[i]]
        self.ax.scatter(
            node["x"],
            node["y"],
            c=[color],
            s=200,
            zorder=5,
            edgecolors="black",
            linewidths=1,
        )
        self.ax.annotate(
            f"{i + 1}. {id_to_name.get(rg.best_order[i], rg.best_order[i])}",
            xy=(node["x"], node["y"]),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            color="black",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
        )

    def _annotate_final(self, id_to_name: dict) -> None:
        """Place a star marker and label at the final destination."""
        rg = self.route_graph
        node = rg.street_graph.G.nodes[rg.best_order[-1]]
        self.ax.scatter(
            node["x"],
            node["y"],
            c="black",
            s=250,
            zorder=5,
            edgecolors="black",
            linewidths=1,
            marker="*",
        )
        self.ax.annotate(
            f"{len(rg.best_order)}. {id_to_name.get(rg.best_order[-1], rg.best_order[-1])} (final)",
            xy=(node["x"], node["y"]),
            xytext=(8, 8),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            color="black",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
        )
