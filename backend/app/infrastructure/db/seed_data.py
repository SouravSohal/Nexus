from typing import List, Dict, Any
from backend.app.domain.models.network import Node, Edge, NodeType, EdgeType

# Seed nodes representing a multi-tier high-tech electronics supply chain
SEED_NODES: List[Node] = [
    Node(
        id="supplier-silicon",
        name="Silicon Valley Taiwan Ltd",
        type=NodeType.SUPPLIER,
        location="Hsinchu, Taiwan",
        latitude=24.7821,
        longitude=120.9928,
        base_cost=15000.0,
        capacity=200.0,
        health=1.0,
        risk_score=0.0,
        inventory=500.0,
        safety_stock=200.0,
        daily_consumption=40.0,
        replenishment_rate=40.0,
        metadata={"material": "Purified Silicon Ingots", "supplier_tier": 2}
    ),
    Node(
        id="factory-wafer",
        name="Taichung Wafer Fabrication Inc",
        type=NodeType.FACTORY,
        location="Taichung, Taiwan",
        latitude=24.1477,
        longitude=120.6736,
        base_cost=45000.0,
        capacity=100.0,
        health=1.0,
        risk_score=0.0,
        inventory=150.0,
        safety_stock=60.0,
        daily_consumption=40.0,  # consumes 40 units silicon to make 40 wafers
        replenishment_rate=40.0,
        metadata={"material": "8nm Semiconductor Wafers", "factory_tier": 1}
    ),
    Node(
        id="port-kaohsiung",
        name="Port of Kaohsiung",
        type=NodeType.PORT,
        location="Kaohsiung, Taiwan",
        latitude=22.6273,
        longitude=120.3014,
        base_cost=25000.0,
        capacity=800.0,
        health=1.0,
        risk_score=0.0,
        inventory=400.0,
        safety_stock=100.0,
        daily_consumption=40.0,  # passes containers out
        replenishment_rate=40.0,
        metadata={"terminal_ops": "Container Terminal 4"}
    ),
    Node(
        id="port-antwerp",
        name="Port of Antwerp-Bruges",
        type=NodeType.PORT,
        location="Antwerp, Belgium",
        latitude=51.2194,
        longitude=4.4025,
        base_cost=30000.0,
        capacity=600.0,
        health=1.0,
        risk_score=0.0,
        inventory=300.0,
        safety_stock=120.0,
        daily_consumption=40.0,
        replenishment_rate=40.0,
        metadata={"terminal_ops": "Europa Terminal"}
    ),
    Node(
        id="port-rotterdam",
        name="Port of Rotterdam",
        type=NodeType.PORT,
        location="Rotterdam, Netherlands",
        latitude=51.9244,
        longitude=4.4777,
        base_cost=32000.0,
        capacity=700.0,
        health=1.0,  # Active standby backup port
        risk_score=0.0,
        inventory=300.0,
        safety_stock=100.0,
        daily_consumption=0.0,
        replenishment_rate=0.0,
        metadata={"terminal_ops": "ECT Delta Terminal"}
    ),
    Node(
        id="warehouse-munich",
        name="Munich Logistics Hub",
        type=NodeType.WAREHOUSE,
        location="Munich, Germany",
        latitude=48.1351,
        longitude=11.5820,
        base_cost=10000.0,
        capacity=400.0,
        health=1.0,
        risk_score=0.0,
        inventory=160.0,  # 4 days of safety/buffer stock
        safety_stock=80.0,
        daily_consumption=40.0,
        replenishment_rate=40.0,
        metadata={"safety_buffer_days": 4}
    ),
    Node(
        id="factory-assembly",
        name="Munich Cognitive Electronics Factory",
        type=NodeType.FACTORY,
        location="Munich, Germany",
        latitude=48.1360,
        longitude=11.5830,
        base_cost=85000.0,
        capacity=100.0,
        health=1.0,
        risk_score=0.0,
        inventory=80.0,
        safety_stock=40.0,
        daily_consumption=40.0,  # consumes 40 parts per day to make final electronics
        replenishment_rate=40.0,
        metadata={"assembly_product": "Nexus Automotive ECUs"}
    ),
    Node(
        id="distributor-europe",
        name="Euro-DC Frankfurt",
        type=NodeType.DISTRIBUTION_CENTER,
        location="Frankfurt, Germany",
        latitude=50.1109,
        longitude=8.6821,
        base_cost=18000.0,
        capacity=500.0,
        health=1.0,
        risk_score=0.0,
        inventory=100.0,
        safety_stock=40.0,
        daily_consumption=40.0,
        replenishment_rate=40.0,
        metadata={"region": "Western Europe"}
    ),
    Node(
        id="product-nexus-ecu",
        name="Nexus Autopilot ECU v5",
        type=NodeType.PRODUCT,
        location="Global Market",
        latitude=52.5200,
        longitude=13.4050,
        base_cost=0.0,
        capacity=500.0,
        health=1.0,
        risk_score=0.0,
        inventory=100.0,
        safety_stock=50.0,
        daily_consumption=40.0,
        replenishment_rate=40.0,
        metadata={"unit_sale_price": 2500.0}  # used to compute lost revenue
    )
]

# Seed edges representing flow routes
SEED_EDGES: List[Edge] = [
    Edge(
        source="supplier-silicon",
        target="factory-wafer",
        type=EdgeType.SUPPLIES,
        dependency_ratio=1.0,
        lead_time_days=1,
        transport_mode="road"
    ),
    Edge(
        source="factory-wafer",
        target="port-kaohsiung",
        type=EdgeType.SHIPS_TO,
        dependency_ratio=1.0,
        lead_time_days=1,
        transport_mode="road"
    ),
    # Primary Ocean Lane
    Edge(
        source="port-kaohsiung",
        target="port-antwerp",
        type=EdgeType.SHIPS_TO,
        dependency_ratio=1.0,
        lead_time_days=5,
        transport_mode="ocean"
    ),
    # Backup Ocean Lane
    Edge(
        source="port-kaohsiung",
        target="port-rotterdam",
        type=EdgeType.SHIPS_TO,
        dependency_ratio=0.0,  # 0.0 initially, activated during mitigation
        lead_time_days=6,      # Takes 1 extra day to Rotterdam
        transport_mode="ocean"
    ),
    # Trucking to Munich warehouse from Antwerp Port
    Edge(
        source="port-antwerp",
        target="warehouse-munich",
        type=EdgeType.SHIPS_TO,
        dependency_ratio=1.0,  # Normally Antwerp handles 100% of incoming wafers
        lead_time_days=2,
        transport_mode="road"
    ),
    # Trucking to Munich warehouse from Rotterdam Port (mitigation route)
    Edge(
        source="port-rotterdam",
        target="warehouse-munich",
        type=EdgeType.SHIPS_TO,
        dependency_ratio=0.0,  # Reroute weight
        lead_time_days=2,
        transport_mode="road"
    ),
    Edge(
        source="warehouse-munich",
        target="factory-assembly",
        type=EdgeType.SUPPLIES,
        dependency_ratio=1.0,
        lead_time_days=1,
        transport_mode="road"
    ),
    Edge(
        source="factory-assembly",
        target="distributor-europe",
        type=EdgeType.SHIPS_TO,
        dependency_ratio=1.0,
        lead_time_days=1,
        transport_mode="road"
    ),
    Edge(
        source="distributor-europe",
        target="product-nexus-ecu",
        type=EdgeType.MANUFACTURES,
        dependency_ratio=1.0,
        lead_time_days=1,
        transport_mode="road"
    )
]
