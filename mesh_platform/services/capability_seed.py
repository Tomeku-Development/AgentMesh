"""Capability seed data for system initialization."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from mesh_platform.models.capability import Capability


# Predefined capability definitions
CAPABILITY_SEEDS = [
    # domain category (applicable to supplier, buyer)
    {
        "name": "electronics",
        "display_name": "Electronics",
        "category": "domain",
        "description": "Specializes in electronic components including semiconductors, PCBs, and integrated circuits. Capable of handling ESD-sensitive materials with proper anti-static procedures. Understands component specifications, lead times, and quality grades.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "batteries",
        "display_name": "Batteries",
        "category": "domain",
        "description": "Handles battery products including lithium-ion, lead-acid, and solid-state cells. Requires compliance with hazardous materials regulations and thermal management during transport. Understands cell chemistry, capacity ratings, and cycle life metrics.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "displays",
        "display_name": "Displays",
        "category": "domain",
        "description": "Manages display technology products including LCD, OLED, and microLED panels. Requires careful handling to prevent pixel damage and scratch protection. Understands resolution specs, color accuracy, and brightness ratings.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "keyboards",
        "display_name": "Keyboards",
        "category": "domain",
        "description": "Handles keyboard and input device products including mechanical, membrane, and capacitive types. Understands switch types, actuation force, and key rollover specifications.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "pharmaceuticals",
        "display_name": "Pharmaceuticals",
        "category": "domain",
        "description": "Manages pharmaceutical products requiring strict regulatory compliance (GMP, FDA). Requires temperature-controlled storage, batch tracking, and expiration management. Critical for patient safety.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "automotive",
        "display_name": "Automotive",
        "category": "domain",
        "description": "Handles automotive parts and components with OEM quality standards. Requires traceability, PPAP documentation, and compatibility verification. Understands torque specs, material grades, and safety ratings.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "agriculture",
        "display_name": "Agriculture",
        "category": "domain",
        "description": "Manages agricultural commodities and equipment. Understands seasonal patterns, perishability constraints, and organic certification requirements.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "textiles",
        "display_name": "Textiles",
        "category": "domain",
        "description": "Handles textile and garment products. Understands fabric composition, GSM ratings, color fastness, and sizing standards across regions.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "food_safety",
        "display_name": "Food Safety",
        "category": "domain",
        "description": "Manages food products with HACCP compliance. Requires cold chain integrity, allergen tracking, and shelf-life management. Critical for consumer safety.",
        "applicable_roles": "supplier,buyer",
    },
    {
        "name": "chemicals",
        "display_name": "Chemicals",
        "category": "domain",
        "description": "Handles chemical products with SDS documentation and hazmat compliance. Requires proper classification (GHS), compatibility checks, and spill containment protocols.",
        "applicable_roles": "supplier,buyer",
    },
    # process category (applicable to buyer, supplier)
    {
        "name": "negotiate",
        "display_name": "Negotiate",
        "category": "process",
        "description": "Advanced multi-round price negotiation with adaptive strategy. Analyzes market conditions, counterparty reputation, and historical patterns to optimize deal terms.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "evaluate_bids",
        "display_name": "Evaluate Bids",
        "category": "process",
        "description": "Sophisticated bid evaluation weighing price, quality guarantees, delivery timelines, supplier reputation, and capability match. Uses weighted scoring with configurable criteria.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "bid",
        "display_name": "Submit Bids",
        "category": "process",
        "description": "Creates competitive bids based on cost analysis, market pricing, capacity utilization, and strategic positioning. Factors in reputation advantage and delivery reliability.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "fulfill_orders",
        "display_name": "Fulfill Orders",
        "category": "process",
        "description": "End-to-end order fulfillment including inventory allocation, production scheduling, quality checks, and shipment coordination.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "counter_offer",
        "display_name": "Counter Offer",
        "category": "process",
        "description": "Strategic counter-offer generation that balances profitability with deal closure probability. Adapts aggressiveness based on negotiation round and market conditions.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "manage_escrow",
        "display_name": "Manage Escrow",
        "category": "process",
        "description": "MESH_CREDIT escrow management including lock, release, and dispute-triggered holds. Ensures atomic settlement with cryptographic verification.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "cold_chain",
        "display_name": "Cold Chain",
        "category": "process",
        "description": "Temperature-controlled supply chain management maintaining product integrity from origin to destination. Continuous monitoring with breach alerts.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "hazmat_handling",
        "display_name": "Hazmat Handling",
        "category": "process",
        "description": "Hazardous materials handling compliant with DOT, IATA, and IMDG regulations. Proper classification, packaging, labeling, and emergency procedures.",
        "applicable_roles": "buyer,supplier",
    },
    {
        "name": "customs_clearance",
        "display_name": "Customs Clearance",
        "category": "process",
        "description": "International trade compliance including tariff classification, duty calculation, documentation preparation, and regulatory filing.",
        "applicable_roles": "buyer,supplier",
    },
    # iot category (applicable to inspector, logistics)
    {
        "name": "temperature_sensor",
        "display_name": "Temperature Sensor",
        "category": "iot",
        "description": "IoT temperature monitoring providing continuous readings for cold chain verification. Detects excursions, calculates MKT, and triggers alerts on threshold breaches.",
        "applicable_roles": "inspector,logistics",
    },
    {
        "name": "rfid_reader",
        "display_name": "RFID Reader",
        "category": "iot",
        "description": "RFID-based asset tracking and authentication. Reads EPC tags for inventory verification, anti-counterfeiting, and chain-of-custody documentation.",
        "applicable_roles": "inspector,logistics",
    },
    {
        "name": "pressure_gauge",
        "display_name": "Pressure Gauge",
        "category": "iot",
        "description": "Industrial pressure monitoring for sealed containers and pressurized systems. Validates packaging integrity and detects leaks during transport.",
        "applicable_roles": "inspector,logistics",
    },
    {
        "name": "humidity_monitor",
        "display_name": "Humidity Monitor",
        "category": "iot",
        "description": "Ambient humidity tracking for moisture-sensitive goods. Prevents condensation damage and validates storage conditions meet specifications.",
        "applicable_roles": "inspector,logistics",
    },
    {
        "name": "gps_tracker",
        "display_name": "GPS Tracker",
        "category": "iot",
        "description": "Real-time geolocation tracking for shipment monitoring. Provides route verification, ETA updates, geofence alerts, and proof-of-delivery.",
        "applicable_roles": "inspector,logistics",
    },
    {
        "name": "camera_inspection",
        "display_name": "Camera Inspection",
        "category": "iot",
        "description": "Visual inspection using cameras and image analysis. Detects surface defects, dimensional variances, label verification, and packaging integrity.",
        "applicable_roles": "inspector,logistics",
    },
    {
        "name": "weight_scale",
        "display_name": "Weight Scale",
        "category": "iot",
        "description": "Precision weight measurement for quantity verification and shipping cost calculation. Detects discrepancies between declared and actual weights.",
        "applicable_roles": "inspector,logistics",
    },
    # logistics category (applicable to logistics)
    {
        "name": "shipping",
        "display_name": "Shipping",
        "category": "logistics",
        "description": "General freight shipping coordination including carrier selection, route optimization, and delivery scheduling. Manages multimodal transport.",
        "applicable_roles": "logistics",
    },
    {
        "name": "fragile_handling",
        "display_name": "Fragile Handling",
        "category": "logistics",
        "description": "Specialized packaging and transport for fragile goods. Includes shock monitoring, custom crating, and reduced-vibration routes.",
        "applicable_roles": "logistics",
    },
    {
        "name": "express_delivery",
        "display_name": "Express Delivery",
        "category": "logistics",
        "description": "Priority shipping with guaranteed delivery windows. Manages time-critical shipments with real-time tracking and escalation procedures.",
        "applicable_roles": "logistics",
    },
    {
        "name": "bulk_transport",
        "display_name": "Bulk Transport",
        "category": "logistics",
        "description": "High-volume freight management for large quantity orders. Optimizes container utilization, consolidation, and deconsolidation.",
        "applicable_roles": "logistics",
    },
    {
        "name": "last_mile",
        "display_name": "Last Mile Delivery",
        "category": "logistics",
        "description": "Final delivery leg management including proof-of-delivery, recipient verification, and return handling.",
        "applicable_roles": "logistics",
    },
    # quality category (applicable to inspector)
    {
        "name": "quality_control",
        "display_name": "Quality Control",
        "category": "quality",
        "description": "Comprehensive QC process including incoming inspection, in-process checks, and final acceptance testing. Statistical process control with AQL sampling.",
        "applicable_roles": "inspector",
    },
    {
        "name": "compliance_audit",
        "display_name": "Compliance Audit",
        "category": "quality",
        "description": "Regulatory and standards compliance verification. Checks against ISO, CE, UL, FCC, and industry-specific certifications.",
        "applicable_roles": "inspector",
    },
    {
        "name": "destructive_testing",
        "display_name": "Destructive Testing",
        "category": "quality",
        "description": "Material and product testing that sacrifices samples to verify specifications. Includes tensile, impact, hardness, and environmental stress tests.",
        "applicable_roles": "inspector",
    },
    {
        "name": "sample_inspection",
        "display_name": "Sample Inspection",
        "category": "quality",
        "description": "Statistical sampling inspection per AQL standards. Determines lot acceptance/rejection based on representative sample evaluation.",
        "applicable_roles": "inspector",
    },
    # market category (applicable to oracle)
    {
        "name": "market_data",
        "display_name": "Market Data",
        "category": "market",
        "description": "Real-time and historical market data aggregation. Provides pricing benchmarks, volume trends, and competitive intelligence across supply chain categories.",
        "applicable_roles": "oracle",
    },
    {
        "name": "price_feed",
        "display_name": "Price Feed",
        "category": "market",
        "description": "Continuous price signal generation based on supply/demand dynamics, commodity indices, and network transaction history.",
        "applicable_roles": "oracle",
    },
    {
        "name": "demand_analysis",
        "display_name": "Demand Analysis",
        "category": "market",
        "description": "Demand forecasting using historical patterns, seasonal factors, and market signals. Identifies emerging trends and supply-demand imbalances.",
        "applicable_roles": "oracle",
    },
    {
        "name": "predictive_analytics",
        "display_name": "Predictive Analytics",
        "category": "market",
        "description": "Advanced ML-driven predictions for market movements, supply disruptions, and optimal procurement timing.",
        "applicable_roles": "oracle",
    },
]


async def seed_capabilities(db: AsyncSession) -> None:
    """Seed system capabilities if they don't already exist.
    
    This function is idempotent - it checks for existing capabilities by name
    before inserting new ones.
    """
    for cap_data in CAPABILITY_SEEDS:
        # Check if capability already exists by name
        result = await db.execute(
            select(Capability).where(
                Capability.name == cap_data["name"],
                Capability.is_system == True,
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing is None:
            capability = Capability(
                name=cap_data["name"],
                display_name=cap_data["display_name"],
                category=cap_data["category"],
                description=cap_data["description"],
                applicable_roles=cap_data["applicable_roles"],
                is_system=True,
                workspace_id=None,
            )
            db.add(capability)
