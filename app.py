import streamlit as st
from config import PLACE_NAME, nodes_dict
from src.graph.build import StreetGraph
from src.graph.routing import RouteGraph
from src.maps.google_maps import build_google_maps_url
from src.visualization.plot import RoutePlotter

st.set_page_config(page_title="Friendly-Route", page_icon="🚗", layout="wide")
st.title("🚗 Friendly-Route")
st.caption("Optimal friend pickup path planner")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    place = st.text_input("Place / area", value=PLACE_NAME)
    network_type = st.selectbox("Network type", ["drive", "walk", "bike", "all"], index=0)
    criteria = st.selectbox("Routing criteria", ["distance", "time"], index=0)
    st.divider()
    st.subheader("Stops")
    st.caption("Edit `config.py` to change stops.")
    st.json(nodes_dict, expanded=False)

# ── Pipeline ───────────────────────────────────────────────────────────────────
if st.button("Find optimal route", type="primary", use_container_width=True):
    with st.spinner("Downloading street graph…"):
        sg = StreetGraph(place, network_type)

    with st.spinner("Snapping stops to street network…"):
        sg.snap_nodes(nodes_dict)

    with st.spinner("Computing pairwise shortest paths…"):
        rg = RouteGraph(sg, criteria)
        rg.compute_paths()

    with st.spinner("Finding optimal route…"):
        rg.find_optimal()

    # ── Results ────────────────────────────────────────────────────────────────
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
