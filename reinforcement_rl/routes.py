from dataclasses import dataclass

@dataclass
class Route:
    name: str
    distance_km: float
    max_daily_trains: int
    travel_hours: float
    route_type: str  # "through_traffic", "local_traffic", "trans_shipment"
    stations: list  # Major stations on this route
    region: str  # "tanzania", "zambia", "cross_border"


# 🚆 TAZARA Complete Route Network
ROUTES = {
    # Main Through Traffic Routes (Port to Interior)
    "DAR_KAPIRI": Route(
        name="DAR_KAPIRI",
        distance_km=1860,
        max_daily_trains=8,
        travel_hours=72,
        route_type="through_traffic",
        stations=["Dar es Salaam", "Kidatu", "Makambako", "Mbeya", "Kasama", "Mpika", "Serenje", "New Kapiri Mposhi"],
        region="cross_border"
    ),
    
    # Regional Hub Routes (Major Cargo Terminus)
    "DAR_MBEYA": Route(
        name="DAR_MBEYA",
        distance_km=900,
        max_daily_trains=6,
        travel_hours=36,
        route_type="through_traffic",
        stations=["Dar es Salaam", "Kidatu", "Makambako", "Mbeya"],
        region="tanzania"
    ),
    
    # Zambia Internal Routes
    "KAPIRI_NDOLA": Route(
        name="KAPIRI_NDOLA",
        distance_km=400,
        max_daily_trains=4,
        travel_hours=18,
        route_type="local_traffic",
        stations=["New Kapiri Mposhi", "Mpika", "Serenje", "Ndola"],
        region="zambia"
    ),
    
    # New Detailed Routes Based on TAZARA Network
    
    # Tanzania Local Routes
    "DAR_KIDATU": Route(
        name="DAR_KIDATU",
        distance_km=200,
        max_daily_trains=4,
        travel_hours=8,
        route_type="local_traffic",
        stations=["Dar es Salaam", "Kidatu"],
        region="tanzania"
    ),
    
    "KIDATU_MAKAMBAKO": Route(
        name="KIDATU_MAKAMBAKO",
        distance_km=350,
        max_daily_trains=3,
        travel_hours=14,
        route_type="local_traffic",
        stations=["Kidatu", "Makambako"],
        region="tanzania"
    ),
    
    "MAKAMBAKO_MBEYA": Route(
        name="MAKAMBAKO_MBEYA",
        distance_km=350,
        max_daily_trains=3,
        travel_hours=14,
        route_type="local_traffic",
        stations=["Makambako", "Mbeya"],
        region="tanzania"
    ),
    
    # Cross-Border Routes
    "MBEYA_KASAMA": Route(
        name="MBEYA_KASAMA",
        distance_km=800,
        max_daily_trains=5,
        travel_hours=32,
        route_type="through_traffic",
        stations=["Mbeya", "Kasama"],
        region="cross_border"
    ),
    
    # Zambia Local Routes
    "KASAMA_MPIKA": Route(
        name="KASAMA_MPIKA",
        distance_km=300,
        max_daily_trains=3,
        travel_hours=12,
        route_type="local_traffic",
        stations=["Kasama", "Mpika"],
        region="zambia"
    ),
    
    "MPIKA_SERENJE": Route(
        name="MPIKA_SERENJE",
        distance_km=200,
        max_daily_trains=3,
        travel_hours=8,
        route_type="local_traffic",
        stations=["Mpika", "Serenje"],
        region="zambia"
    ),
    
    "SERENJE_KAPIRI": Route(
        name="SERENJE_KAPIRI",
        distance_km=160,
        max_daily_trains=3,
        travel_hours=6,
        route_type="local_traffic",
        stations=["Serenje", "New Kapiri Mposhi"],
        region="zambia"
    ),
    
    # Great Lakes Region Connection
    "KIDATU_TRANS_SHIPMENT": Route(
        name="KIDATU_TRANS_SHIPMENT",
        distance_km=0,
        max_daily_trains=10,
        travel_hours=4,  # Trans-shipment time
        route_type="trans_shipment",
        stations=["Kidatu"],
        region="tanzania"
    ),
    
    # Regional Distribution Routes
    "KAPIRI_DISTRIBUTION": Route(
        name="KAPIRI_DISTRIBUTION",
        distance_km=500,
        max_daily_trains=6,
        travel_hours=20,
        route_type="local_traffic",
        stations=["New Kapiri Mposhi", "Central Province Hubs"],
        region="zambia"
    )
}

# 🚆 Route Categories for AI Decision Making
ROUTE_CATEGORIES = {
    "through_traffic": ["DAR_KAPIRI", "DAR_MBEYA", "MBEYA_KASAMA"],
    "local_traffic": ["KAPIRI_NDOLA", "DAR_KIDATU", "KIDATU_MAKAMBAKO", "MAKAMBAKO_MBEYA", "KASAMA_MPIKA", "MPIKA_SERENJE", "SERENJE_KAPIRI", "KAPIRI_DISTRIBUTION"],
    "trans_shipment": ["KIDATU_TRANS_SHIPMENT"]
}

# 🚆 Regional Route Groups
REGIONAL_ROUTES = {
    "tanzania": ["DAR_KIDATU", "KIDATU_MAKAMBAKO", "MAKAMBAKO_MBEYA", "DAR_MBEYA", "KIDATU_TRANS_SHIPMENT"],
    "zambia": ["KASAMA_MPIKA", "MPIKA_SERENJE", "SERENJE_KAPIRI", "KAPIRI_NDOLA", "KAPIRI_DISTRIBUTION"],
    "cross_border": ["DAR_KAPIRI", "MBEYA_KASAMA"]
}

# 🚆 Major Station Hubs
MAJOR_HUBS = {
    "dar_es_salaam": {"type": "port", "country": "tanzania", "connections": ["DAR_KAPIRI", "DAR_MBEYA", "DAR_KIDATU"]},
    "kidatu": {"type": "trans_shipment", "country": "tanzania", "connections": ["DAR_KAPIRI", "DAR_MBEYA", "KIDATU_TRANS_SHIPMENT"]},
    "makambako": {"type": "hub", "country": "tanzania", "connections": ["DAR_KAPIRI", "DAR_MBEYA"]},
    "mbeya": {"type": "cargo_terminus", "country": "tanzania", "connections": ["DAR_MBEYA", "MBEYA_KASAMA"]},
    "kasama": {"type": "hub", "country": "zambia", "connections": ["MBEYA_KASAMA", "KASAMA_MPIKA"]},
    "mpika": {"type": "hub", "country": "zambia", "connections": ["KASAMA_MPIKA", "MPIKA_SERENJE"]},
    "serenje": {"type": "hub", "country": "zambia", "connections": ["MPIKA_SERENJE", "SERENJE_KAPIRI"]},
    "new_kapiri_mposhi": {"type": "primary_distribution", "country": "zambia", "connections": ["DAR_KAPIRI", "SERENJE_KAPIRI", "KAPIRI_DISTRIBUTION"]}
}
