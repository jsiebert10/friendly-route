import osmnx as ox

# ── OSMnx settings ─────────────────────────────────────────────────────────────
ox.settings.use_cache = True
ox.settings.log_console = True

# ── Defaults ───────────────────────────────────────────────────────────────────
PLACE_NAME = "La Reina, Santiago Metropolitan Region, Chile"
NETWORK_TYPE = "drive"  # drive | walk | bike | all
CRITERIA = "distance"  # distance | time

# ── Stops ──────────────────────────────────────────────────────────────────────
# Each entry: name → {"source": bool, "sink": bool, "y": lat, "x": lon}
# Exactly one entry must have source=True (driver start)
# Exactly one entry must have sink=True  (driver home)
nodes_dict = {
    "Zamorano": {
        "source": True,
        "sink": False,
        "y": -33.428560774159344,
        "x": -70.53765037301235,
    },
    "TEO": {
        "source": False,
        "sink": False,
        "y": -33.44230868573651,
        "x": -70.57211041349215,
    },
    "Reg_Civil": {
        "source": False,
        "sink": False,
        "y": -33.45048,
        "x": -70.54276,
    },
    "Ram_lav": {
        "source": False,
        "sink": False,
        "y": -33.44033665554887,
        "x": -70.56704991349216,
    },
    "La_pizarra": {
        "source": False,
        "sink": False,
        "y": -33.438409949072835,
        "x": -70.56474536067596,
    },
    "Malu": {
        "source": False,
        "sink": True,
        "y": -33.44341785083225,
        "x": -70.5667162,
    },
}
