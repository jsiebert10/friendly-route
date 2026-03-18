import folium
import osmnx as ox
import streamlit as st
from branca.element import MacroElement
from config import PLACE_NAME
from jinja2 import Template
from src.graph.build import StreetGraph
from src.graph.routing import RouteGraph
from src.maps.google_maps import build_google_maps_url
from src.visualization.plot import RoutePlotter
from streamlit_folium import st_folium

st.set_page_config(page_title="Friendly-Route", page_icon="🚗", layout="wide")
st.title("🚗 Friendly-Route")
st.caption("Optimal friend pickup path planner")

# ── Session state init ─────────────────────────────────────────────────────────
if "source" not in st.session_state:
    st.session_state.source = None
if "sink" not in st.session_state:
    st.session_state.sink = None
if "stops" not in st.session_state:
    st.session_state.stops = {}
if "active_section" not in st.session_state:
    st.session_state.active_section = None

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    place = st.text_input("Place / area", value=PLACE_NAME)
    network_type = st.selectbox("Network type", ["drive", "walk", "bike", "all"], index=0)
    criteria = st.selectbox("Routing criteria", ["distance", "time"], index=0)

    st.divider()

    st.subheader("🟢 Driver start")
    if st.session_state.source:
        s = st.session_state.source
        st.markdown(f"**{s['name']}** `({s['y']:.4f}, {s['x']:.4f})`")
        if st.button("Remove", key="remove_source"):
            st.session_state.source = None
            st.rerun()
    else:
        st.caption("Not set.")

    st.divider()

    st.subheader("🔴 Driver home")
    if st.session_state.sink:
        s = st.session_state.sink
        st.markdown(f"**{s['name']}** `({s['y']:.4f}, {s['x']:.4f})`")
        if st.button("Remove", key="remove_sink"):
            st.session_state.sink = None
            st.rerun()
    else:
        st.caption("Not set.")

    st.divider()

    st.subheader("🔵 Friends")
    if st.session_state.stops:
        for name, values in st.session_state.stops.items():
            st.markdown(f"**{name}** `({values['y']:.4f}, {values['x']:.4f})`")
        if st.button("Clear all friends", use_container_width=True):
            st.session_state.stops = {}
            st.rerun()
    else:
        st.caption("No friends added yet.")

# ── Map ────────────────────────────────────────────────────────────────────────
st.subheader("1. Drop pins on the map")

col1, col2, col3 = st.columns(3)
if col1.button("📍 Set driver start", use_container_width=True):
    st.session_state.active_section = "source"
if col2.button("🏠 Set driver home", use_container_width=True):
    st.session_state.active_section = "sink"
if col3.button("👥 Add a friend", use_container_width=True):
    st.session_state.active_section = "stop"

if st.session_state.active_section:
    labels = {
        "source": "click on the map to place the driver start",
        "sink": "click on the map to place the driver home",
        "stop": "click on the map to place a friend",
    }
    st.info(f"📍 {labels[st.session_state.active_section]}")

# Build map
center_lat, center_lon = ox.geocode(place)
m = folium.Map(location=[center_lat, center_lon], zoom_start=14)


# Ghost pin that follows the mouse cursor via custom JS
class GhostPin(MacroElement):
    _template = Template("""
        {% macro script(this, kwargs) %}
        var ghostIcon = L.divIcon({
            className: '',
            html: '<div style="width:14px;height:14px;background:rgba(255,80,80,0.55);border:2px solid rgba(180,0,0,0.85);border-radius:50% 50% 50% 0;transform:rotate(-45deg);pointer-events:none;"></div>',
            iconSize: [14, 14],
            iconAnchor: [7, 14],
        });
        var ghostMarker = L.marker([0,0], {icon: ghostIcon, interactive: false, zIndexOffset: 999}).addTo({{ this._parent.get_name() }});
        {{ this._parent.get_name() }}.on('mousemove', function(e) { ghostMarker.setLatLng(e.latlng); });
        {{ this._parent.get_name() }}.on('mouseout',  function()  { ghostMarker.setLatLng([0,0]); });
        {% endmacro %}
    """)


GhostPin().add_to(m)

# Draw existing confirmed pins
if st.session_state.source:
    s = st.session_state.source
    folium.Marker(
        location=[s["y"], s["x"]],
        tooltip=f"Start: {s['name']}",
        icon=folium.Icon(color="green", icon="home"),
    ).add_to(m)

if st.session_state.sink:
    s = st.session_state.sink
    folium.Marker(
        location=[s["y"], s["x"]],
        tooltip=f"Home: {s['name']}",
        icon=folium.Icon(color="red", icon="home"),
    ).add_to(m)

for name, values in st.session_state.stops.items():
    folium.Marker(
        location=[values["y"], values["x"]],
        tooltip=f"Friend: {name}",
        icon=folium.Icon(color="blue", icon="user"),
    ).add_to(m)

map_data = st_folium(m, width="100%", height=450, returned_objects=["last_clicked"])

# ── Pin form ───────────────────────────────────────────────────────────────────
clicked_lat = map_data["last_clicked"]["lat"] if map_data and map_data.get("last_clicked") else None
clicked_lon = map_data["last_clicked"]["lng"] if map_data and map_data.get("last_clicked") else None

if st.session_state.active_section and clicked_lat and clicked_lon:
    section = st.session_state.active_section
    labels = {
        "source": "2. Name the driver start",
        "sink": "2. Name the driver home",
        "stop": "2. Name this friend",
    }
    st.subheader(labels[section])

    with st.form("pin_form"):
        default_names = {"source": "Driver start", "sink": "Driver home", "stop": ""}
        pin_name = st.text_input("Name", value=default_names[section], placeholder="e.g. Zamorano")
        st.caption(f"Position: {clicked_lat:.5f}, {clicked_lon:.5f}")
        submitted = st.form_submit_button("Add pin", use_container_width=True)

        if submitted and pin_name:
            if section == "source":
                st.session_state.source = {"name": pin_name, "y": clicked_lat, "x": clicked_lon}
            elif section == "sink":
                st.session_state.sink = {"name": pin_name, "y": clicked_lat, "x": clicked_lon}
            else:
                st.session_state.stops[pin_name] = {"y": clicked_lat, "x": clicked_lon}
            st.session_state.active_section = None
            st.rerun()

# ── Validation ─────────────────────────────────────────────────────────────────
has_source = st.session_state.source is not None
has_sink = st.session_state.sink is not None
has_stops = len(st.session_state.stops) > 0
ready = has_source and has_sink and has_stops

if (has_source or has_sink or has_stops) and not ready:
    missing = []
    if not has_source:
        missing.append("driver start")
    if not has_sink:
        missing.append("driver home")
    if not has_stops:
        missing.append("at least one friend")
    st.warning(f"Still needed: {', '.join(missing)}.")


# ── Build nodes_dict from session state ───────────────────────────────────────
def build_nodes_dict():
    nodes = {}
    s = st.session_state.source
    nodes[s["name"]] = {"source": True, "sink": False, "y": s["y"], "x": s["x"]}
    h = st.session_state.sink
    nodes[h["name"]] = {"source": False, "sink": True, "y": h["y"], "x": h["x"]}
    for name, values in st.session_state.stops.items():
        nodes[name] = {"source": False, "sink": False, "y": values["y"], "x": values["x"]}
    return nodes


# ── Pipeline ───────────────────────────────────────────────────────────────────
st.divider()
if st.button("Find optimal route", type="primary", use_container_width=True, disabled=not ready):
    with st.spinner("Downloading street graph…"):
        sg = StreetGraph(place, network_type)

    with st.spinner("Snapping stops to street network…"):
        sg.snap_nodes(build_nodes_dict())

    with st.spinner("Computing pairwise shortest paths…"):
        rg = RouteGraph(sg, criteria)
        rg.compute_paths()

    with st.spinner("Finding optimal route…"):
        rg.find_optimal()

    id_to_name = {v: k for k, v in sg.nodes_name_id.items()}
    order_labels = " → ".join(id_to_name.get(n, str(n)) for n in rg.best_order)

    col1, col2 = st.columns(2)
    col1.metric("Total distance", f"{rg.best_distance:.2f} km")
    col2.metric("Stops", len(rg.best_order) - 2)

    st.success(f"**Optimal order:** {order_labels}")

    with st.spinner("Plotting route…"):
        plotter = RoutePlotter(rg)
        plotter.plot()
        st.pyplot(plotter.fig)

    url = build_google_maps_url(rg)
    st.link_button("Open in Google Maps 🗺️", url, use_container_width=True)
