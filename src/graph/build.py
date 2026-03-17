import geopandas as gpd
import osmnx as ox
from shapely.geometry import LineString, Point


class StreetGraph:
    """
    Downloads and manages a street graph for a given place.

    Handles graph projection to UTM (meters) and snapping arbitrary
    lat/lon points to the nearest street edge by splitting that edge
    into two segments.

    Parameters
    ----------
    place : str
        Nominatim query string, e.g. ``"La Reina, Santiago, Chile"``.
    network_type : str, optional
        OSMnx network type: ``"drive"`` (default), ``"walk"``, ``"bike"``, ``"all"``.

    Attributes
    ----------
    G : networkx.MultiDiGraph
        Street graph in EPSG:4326.
    G_proj : networkx.MultiDiGraph
        Street graph projected to UTM (meters).
    nodes_name_id : dict
        Populated by ``snap_nodes()``. Maps location name → node ID.

    Examples
    --------
    >>> sg = StreetGraph("La Reina, Santiago, Chile")
    >>> sg.snap_nodes(nodes_dict)
    >>> sg.G  # use for routing / plotting
    >>> sg.nodes_name_id  # {"Zamorano": 1, "Malu": -1, "TEO": 862301, ...}
    """

    SOURCE_ID = 1
    SINK_ID = -1

    def __init__(self, place: str, network_type: str = "drive"):
        self.place = place
        self.network_type = network_type
        self.nodes_name_id: dict = {}

        self.G = ox.graph_from_place(place, network_type=network_type, simplify=True)
        self.G_proj = ox.project_graph(self.G)

        # Precompute edges GDF once — reused for every snap call
        self._edges = ox.graph_to_gdfs(self.G_proj, nodes=False)

    def snap_nodes(self, nodes_dict: dict) -> None:
        """
        Snap each point in ``nodes_dict`` to its closest street edge,
        inserting it as a new node by splitting that edge in two.

        Mutates ``self.G_proj`` and reprojects back to EPSG:4326 in ``self.G``.
        Populates ``self.nodes_name_id``.

        Parameters
        ----------
        nodes_dict : dict
            ``{name: {"source": bool, "sink": bool, "y": lat, "x": lon}}``
            Exactly one entry must have ``source=True`` (assigned ID=1) and
            exactly one must have ``sink=True`` (assigned ID=-1).
        """
        for name, values in nodes_dict.items():
            point_proj = self._project_point(values["y"], values["x"])

            self._edges["dist"] = self._edges.geometry.distance(point_proj)
            closest_edge = self._edges.loc[self._edges["dist"].idxmin()]

            u, v, edge_key = closest_edge.name
            snap_point = self._snap_to_edge(closest_edge.geometry, point_proj)

            node_id = self._assign_node_id(values)
            self.nodes_name_id[name] = node_id

            self._insert_node(node_id, snap_point, u, v, edge_key)

        self.G = ox.project_graph(self.G_proj, to_crs="EPSG:4326")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _project_point(self, lat: float, lon: float):
        """Project a WGS84 lat/lon point to the graph's UTM CRS."""
        gdf = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")
        return gdf.to_crs(self.G_proj.graph["crs"]).geometry.iloc[0]

    def _snap_to_edge(self, edge_geom, point_proj):
        """Return the closest point on ``edge_geom`` to ``point_proj``."""
        return edge_geom.interpolate(edge_geom.project(point_proj))

    def _assign_node_id(self, values: dict) -> int:
        """Return the canonical ID for a node based on its role."""
        if values["source"]:
            return self.SOURCE_ID
        if values["sink"]:
            return self.SINK_ID
        # Increment after each insertion so IDs stay unique
        return max(self.G_proj.nodes) + 1

    def _insert_node(self, node_id: int, snap_point, u, v, edge_key) -> None:
        """
        Insert ``node_id`` at ``snap_point`` by splitting edge (u, v) into
        (u → node_id) and (node_id → v), preserving all edge attributes.
        """
        self.G_proj.add_node(node_id, x=snap_point.x, y=snap_point.y)

        line_u = LineString(
            [
                (self.G_proj.nodes[u]["x"], self.G_proj.nodes[u]["y"]),
                (snap_point.x, snap_point.y),
            ]
        )
        line_v = LineString(
            [
                (snap_point.x, snap_point.y),
                (self.G_proj.nodes[v]["x"], self.G_proj.nodes[v]["y"]),
            ]
        )

        attrs = self.G_proj[u][v][edge_key].copy()
        attrs.pop("geometry", None)

        self.G_proj.remove_edge(u, v, edge_key)

        self.G_proj.add_edge(u, node_id, **{**attrs, "length": line_u.length, "geometry": line_u})
        self.G_proj.add_edge(node_id, v, **{**attrs, "length": line_v.length, "geometry": line_v})
