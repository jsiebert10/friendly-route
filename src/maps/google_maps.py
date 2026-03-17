from src.graph.routing import RouteGraph


def build_google_maps_url(route_graph: RouteGraph) -> str:
    """
    Build a Google Maps Directions URL for the optimal route.

    Opens directly in Google Maps with the driver's start as origin,
    driver's home as destination, and all intermediate stops as waypoints.

    Parameters
    ----------
    route_graph : RouteGraph
        A ``RouteGraph`` instance with ``find_optimal()`` already called.

    Returns
    -------
    str
        Google Maps Directions URL.
    """
    G = route_graph.street_graph.G
    best_order = route_graph.best_order

    def _coords(node_id):
        node = G.nodes[node_id]
        return f"{node['y']},{node['x']}"

    origin = _coords(best_order[0])
    destination = _coords(best_order[-1])
    waypoints = "|".join(_coords(n) for n in best_order[1:-1])

    url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={origin}"
        f"&destination={destination}"
        f"&travelmode=driving"
    )
    if waypoints:
        url += f"&waypoints={waypoints}"

    return url
