"""Prompt templates for MESH supply chain agents.

Each function returns a (system_prompt, user_prompt) tuple with rich context
for the specific agent role and decision being made.
"""

from __future__ import annotations

import json
from typing import Any


def format_capabilities_context(capabilities: list[dict[str, str]]) -> str:
    """Format capability name+description pairs for injection into LLM prompts.

    Args:
        capabilities: List of {"name": str, "description": str} dicts

    Returns:
        Formatted string for prompt inclusion
    """
    if not capabilities:
        return "No specific capabilities declared."
    lines = []
    for cap in capabilities:
        name = cap.get("name", "unknown")
        desc = cap.get("description", "")
        if desc:
            lines.append(f"- **{name}**: {desc}")
        else:
            lines.append(f"- **{name}**")
    return "\n".join(lines)


def oracle_pricing_prompt(
    base_prices: dict[str, float],
    price_history: list[dict[str, Any]],
    epoch: int,
    agent_count: int,
) -> tuple[str, str]:
    """Generate prompt for Oracle agent to determine market prices.

    Args:
        base_prices: Base prices for goods {goods_name: price}
        price_history: Recent price history entries
        epoch: Current epoch number
        agent_count: Number of active agents

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are the Oracle agent in the MESH decentralized supply chain network.
Your role is to determine fair market prices for goods based on supply/demand signals,
historical data, and network activity.

You must respond with a JSON object containing:
{
    "prices": {"goods_name": price, ...},
    "trend": "rising" | "stable" | "falling",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of price determination"
}

Constraints:
- Prices must be positive numbers
- Price changes should typically be within ±20% of base prices unless extreme conditions
- Consider price history trends and agent activity
- Higher agent count typically indicates higher demand"""

    user_prompt = f"""Determine market prices for epoch {epoch}.

## Base Prices
{json.dumps(base_prices, indent=2)}

## Recent Price History (last 10 entries)
{json.dumps(price_history[-10:] if price_history else [], indent=2)}

## Network Activity
- Active agents: {agent_count}
- Current epoch: {epoch}

Respond with a JSON object containing the new prices, trend analysis, and reasoning."""

    return system_prompt, user_prompt


def oracle_demand_prompt(
    goods_catalog: list[dict[str, Any]],
    price_history: dict[str, list[float]],
    epoch: int,
) -> tuple[str, str]:
    """Generate prompt for Oracle agent to analyze demand patterns.

    Args:
        goods_catalog: List of goods with metadata
        price_history: Price history per goods {goods_name: [prices]}
        epoch: Current epoch number

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are the Oracle agent analyzing demand patterns in the MESH supply chain.
Your role is to predict demand levels and identify supply chain risks.

You must respond with a JSON object containing:
{
    "demand_forecast": {"goods_name": {"level": "high"|"medium"|"low",
        "trend": "up"|"stable"|"down"}, ...},
    "supply_risks": ["risk description", ...],
    "recommendations": ["recommendation", ...],
    "confidence": 0.0-1.0
}

Analyze price trends to infer demand.
Rising prices often indicate higher demand or supply constraints."""

    user_prompt = f"""Analyze demand patterns for epoch {epoch}.

## Goods Catalog
{json.dumps(goods_catalog, indent=2)}

## Price History by Goods
{json.dumps(price_history, indent=2, default=str)}

Provide demand forecasts, supply risks, and recommendations as JSON."""

    return system_prompt, user_prompt


def supplier_bid_prompt(
    goods: str,
    cost: float,
    market_price: float,
    inventory: int,
    active_orders: int,
    quantity_requested: int,
    max_price: float,
    reputation: float,
    agent_capabilities: list[dict[str, str]] | None = None,
) -> tuple[str, str]:
    """Generate prompt for Supplier agent to create a bid.

    Args:
        goods: Name of goods being requested
        cost: Supplier's production cost per unit
        market_price: Current market price
        inventory: Available inventory
        active_orders: Number of active orders being fulfilled
        quantity_requested: Quantity requested by buyer
        max_price: Maximum price buyer is willing to pay
        reputation: Supplier's reputation score (0.0-1.0)
        agent_capabilities: Optional list of supplier's capabilities

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are a Supplier agent in the MESH supply chain network.
Your goal is to maximize profit while maintaining good reputation and fulfilling orders reliably.

You must respond with a JSON object containing:
{
    "bid_price": float,
    "max_quantity": int,
    "estimated_delivery_epochs": int,
    "quality_guarantee": float,
    "reasoning": "brief explanation of bid strategy"
}

Constraints:
- bid_price must be between cost (minimum to break even) and max_price
- Higher reputation allows for premium pricing
- Consider inventory and active orders when setting max_quantity
- Be competitive but profitable
- Leverage your specialized capabilities when bidding — expertise in
  relevant areas justifies premium pricing
- If you lack capabilities matching the requested goods, acknowledge
  this limitation in your reasoning"""

    profit_margin = market_price - cost
    capabilities_section = f"""
## Your Specialized Capabilities
{format_capabilities_context(agent_capabilities or [])}
"""

    user_prompt = f"""Create a bid for supplying goods.

## Request Details
- Goods: {goods}
- Quantity requested: {quantity_requested}
- Maximum price buyer will pay: {max_price:.2f}

## Your Situation
- Production cost per unit: {cost:.2f}
- Current market price: {market_price:.2f}
- Potential profit margin: {profit_margin:.2f} per unit
- Available inventory: {inventory}
- Active orders to fulfill: {active_orders}
- Your reputation score: {reputation:.2f}

## Constraints
- Your bid price must be at least {cost:.2f} (your cost) to avoid losses
- Your bid price should not exceed {max_price:.2f} (buyer's max)
- Consider your capacity (inventory - active orders) for quantity
{capabilities_section}
Respond with your bid as JSON."""

    return system_prompt, user_prompt


def supplier_counter_prompt(
    proposed_price: float,
    cost: float,
    market_price: float,
    reputation: float,
    round_num: int,
) -> tuple[str, str]:
    """Generate prompt for Supplier agent to make a counter-offer.

    Args:
        proposed_price: Price proposed by buyer
        cost: Supplier's production cost
        market_price: Current market price
        reputation: Supplier's reputation score
        round_num: Current negotiation round

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are a Supplier agent negotiating a price in the MESH supply chain.
Your goal is to reach a mutually beneficial agreement while maintaining profitability.

You must respond with a JSON object containing:
{
    "counter_price": float | null,
    "accept": boolean,
    "min_acceptable": float,
    "reasoning": "brief explanation"
}

Constraints:
- Never accept a price below your cost
- Consider market price and your reputation
- Round {round_num} of negotiation - consider reaching agreement soon
- Set counter_price to null and accept=true if you accept their offer
- Set counter_price to a value and accept=false if you want to continue negotiating"""

    market_ctx = (
        'below' if proposed_price < market_price
        else 'above' if proposed_price > market_price
        else 'at'
    )
    profit_at_proposed = proposed_price - cost
    user_prompt = f"""The buyer has proposed a price of {proposed_price:.2f}.

## Your Position
- Your production cost: {cost:.2f}
- Current market price: {market_price:.2f}
- Your reputation: {reputation:.2f}
- Profit at proposed price: {profit_at_proposed:.2f} per unit
- Negotiation round: {round_num}

## Decision
- If proposed price >= cost, you can consider accepting
- Higher reputation may justify premium pricing
- Market price context: {market_ctx} market

Respond with your counter-offer or acceptance as JSON."""

    return system_prompt, user_prompt


def buyer_evaluate_bids_prompt(
    bids: list[dict[str, Any]],
    market_price: float,
    max_price: float,
    quality_threshold: float,
    bidder_capabilities: dict[str, list[dict[str, str]]] | None = None,
) -> tuple[str, str]:
    """Generate prompt for Buyer agent to evaluate supplier bids.

    Args:
        bids: List of bid dictionaries with supplier info, price, quantity, etc.
        market_price: Current market price for reference
        max_price: Maximum price the buyer is willing to pay
        quality_threshold: Minimum quality score required
        bidder_capabilities: Optional dict mapping supplier_id to their capabilities

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are a Buyer agent evaluating supplier bids in the MESH supply chain.
Your goal is to select the best bid that balances price, quality, and supplier reliability.

You must respond with a JSON object containing:
{
    "selected_bid": {
        "supplier_id": "id",
        "price": float,
        "quantity": int
    },
    "runner_ups": [{"supplier_id": "id", "score": float}, ...],
    "reasoning": "brief explanation of selection",
    "negotiation_targets": [{"supplier_id": "id", "target_price": float}, ...]
}

Constraints:
- Never select a bid with quality below the threshold
- Consider supplier reputation and delivery estimates
- Price should be at or below max_price
- You may identify negotiation targets for higher-priced quality bids
- Weight supplier capabilities matching the requested goods — specialists
  with relevant domain expertise are more reliable
- Consider IoT and quality capabilities as indicators of verifiable
  delivery quality"""

    caps_section = ""
    if bidder_capabilities:
        caps_lines = []
        for supplier_id, caps in bidder_capabilities.items():
            caps_lines.append(f"### {supplier_id}")
            caps_lines.append(format_capabilities_context(caps))
        caps_section = f"""
## Bidder Capabilities
{chr(10).join(caps_lines)}
"""

    user_prompt = f"""Evaluate the following supplier bids and select the best option.

## Bid Summary
{json.dumps(bids, indent=2)}
{caps_section}
## Evaluation Criteria
- Market price reference: {market_price:.2f}
- Your maximum acceptable price: {max_price:.2f}
- Minimum quality threshold: {quality_threshold}

## Considerations
- Lower prices are better, but consider quality and reliability
- Supplier reputation indicates reliability
- Delivery time affects your supply chain efficiency
- You may want to negotiate with promising bids

Respond with your bid evaluation as JSON."""

    return system_prompt, user_prompt


def buyer_settlement_prompt(
    agreed_price: float,
    quantity: int,
    quality_score: float,
    on_time: bool,
) -> tuple[str, str]:
    """Generate prompt for Buyer agent to process settlement.

    Args:
        agreed_price: The agreed-upon price per unit
        quantity: Quantity delivered
        quality_score: Measured quality score (0.0-1.0)
        on_time: Whether delivery was on time

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are a Buyer agent processing settlement in the MESH supply chain.
Your role is to evaluate the delivery and determine the final payment and reputation impact.

You must respond with a JSON object containing:
{
    "payment_amount": float,
    "quality_bonus": float,
    "on_time_bonus": float,
    "reputation_feedback": {
        "supplier_id": "id",
        "score": 0.0-1.0,
        "comment": "feedback comment"
    },
    "accept_delivery": boolean,
    "reasoning": "brief explanation"
}

Constraints:
- Payment should be based on agreed_price × quantity, adjusted for quality
- Quality below 0.5 may warrant rejection or discount
- On-time delivery deserves a small bonus
- Provide fair reputation feedback for future transactions"""

    total_base = agreed_price * quantity
    user_prompt = f"""Process settlement for a completed delivery.

## Delivery Details
- Agreed price per unit: {agreed_price:.2f}
- Quantity delivered: {quantity}
- Total base payment: {total_base:.2f}

## Delivery Quality
- Quality score: {quality_score:.2f} (0.0-1.0 scale)
- On-time delivery: {'Yes' if on_time else 'No'}

## Settlement Guidelines
- Quality ≥ 0.8: Full payment + quality bonus
- Quality 0.5-0.8: Full payment
- Quality < 0.5: Consider rejection or discount
- On-time: Add small bonus
- Late: May reduce bonus or note in feedback

Respond with your settlement decision as JSON."""

    return system_prompt, user_prompt


def negotiation_counter_prompt(
    context: dict[str, Any],
    their_price: float,
    market_history: list[float],
) -> tuple[str, str]:
    """Generate prompt for negotiation counter-offer.

    Args:
        context: Negotiation context (role, previous offers, etc.)
        their_price: Price offered by the other party
        market_history: Recent market prices

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are an agent negotiating a price in the MESH supply chain.
Your goal is to reach a fair agreement that benefits your principal.

You must respond with a JSON object containing:
{
    "counter_price": float | null,
    "accept": boolean,
    "walk_away": boolean,
    "reasoning": "brief explanation",
    "strategy": "aggressive" | "moderate" | "conciliatory"
}

Constraints:
- Consider market prices and your principal's interests
- Track the negotiation pattern - be willing to compromise
- Set walk_away=true only if no agreement is possible
- Set counter_price=null and accept=true to accept their offer"""

    role = context.get("role", "buyer")
    target = context.get("target_price", "unknown")
    previous = context.get("previous_offers", [])
    rounds = context.get("round", 1)
    max_rounds = context.get("max_rounds", 3)

    avg_price = (
        f"{sum(market_history)/len(market_history):.2f}"
        if market_history else 'N/A'
    )

    user_prompt = f"""You are negotiating as a {role}.

## Current Offer
- Their proposed price: {their_price:.2f}

## Context
- Your target price: {target}
- Negotiation round: {rounds}/{max_rounds}
- Previous offers: {json.dumps(previous, indent=2)}

## Market Reference
- Recent market prices: {market_history}

## Decision
- As a {role}, you want {'lower' if role == 'buyer' else 'higher'} prices
- Consider if this round is your last chance to counter
- Market prices suggest fair value around {avg_price}

Respond with your negotiation decision as JSON."""

    return system_prompt, user_prompt


def inspector_quality_prompt(
    goods: str,
    quantity: int,
    supplier_reputation: float,
    category: str,
    inspector_capabilities: list[dict[str, str]] | None = None,
) -> tuple[str, str]:
    """Generate prompt for Inspector agent to assess quality.

    Args:
        goods: Name of goods to inspect
        quantity: Quantity to inspect
        supplier_reputation: Supplier's reputation score
        category: Category of goods (e.g., "electronics", "textiles")
        inspector_capabilities: Optional list of inspector's capabilities

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are an Inspector agent in the MESH supply chain.
Your role is to impartially assess the quality of delivered goods.

You must respond with a JSON object containing:
{
    "quality_score": 0.0-1.0,
    "defect_count": int,
    "defect_ratio": 0.0-1.0,
    "sample_size": int,
    "findings": ["finding 1", "finding 2", ...],
    "recommendation": "accept" | "conditional" | "reject",
    "reasoning": "brief explanation"
}

Constraints:
- Quality score must be between 0.0 and 1.0
- Higher reputation suppliers typically deliver better quality, but inspect fairly
- Provide specific findings to justify your score
- Recommendation should align with quality score
- Use your specialized inspection capabilities to determine the most
  appropriate inspection method
- If you have IoT sensors (temperature, RFID, pressure, etc.), incorporate
  sensor-based data in your assessment
- Reference your specific capabilities in your findings to justify the
  inspection methodology"""

    capabilities_section = f"""
## Your Inspection Capabilities
{format_capabilities_context(inspector_capabilities or [])}

Use these capabilities to determine the most appropriate inspection methodology for this delivery.
"""

    user_prompt = f"""Inspect a delivery of goods.

## Delivery Details
- Goods: {goods}
- Quantity: {quantity}
- Category: {category}

## Supplier Information
- Supplier reputation: {supplier_reputation:.2f}

## Inspection Guidelines
- Sample an appropriate portion based on quantity
- Document any defects or quality issues
- Consider category-specific quality standards
- Provide objective assessment regardless of supplier reputation
{capabilities_section}
Respond with your inspection report as JSON."""

    return system_prompt, user_prompt


def logistics_pricing_prompt(
    weight: float,
    fragile: bool,
    origin: str,
    destination: str,
    deadline: int,
    current_load: int,
    vehicle_type: str,
) -> tuple[str, str]:
    """Generate prompt for Logistics agent to determine shipping price.

    Args:
        weight: Weight of shipment in kg
        fragile: Whether goods are fragile
        origin: Origin location
        destination: Destination location
        deadline: Delivery deadline in epochs
        current_load: Current vehicle/capacity load
        vehicle_type: Type of vehicle (e.g., "truck", "drone")

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are a Logistics agent in the MESH supply chain.
Your role is to determine fair shipping prices based on shipment characteristics
and your current capacity.

You must respond with a JSON object containing:
{
    "price": float,
    "estimated_epochs": int,
    "route_efficiency": 0.0-1.0,
    "capacity_available": int,
    "surcharge": float,
    "reasoning": "brief explanation"
}

Constraints:
- Price must be positive
- Consider weight, distance, urgency, and special handling
- Higher current load may justify premium pricing
- Fragile goods require careful handling (surcharge)
- Tighter deadlines typically cost more"""

    user_prompt = f"""Calculate shipping price for a delivery request.

## Shipment Details
- Weight: {weight} kg
- Fragile: {'Yes' if fragile else 'No'}
- Origin: {origin}
- Destination: {destination}

## Delivery Requirements
- Deadline: {deadline} epochs
- Vehicle type: {vehicle_type}

## Your Capacity
- Current load: {current_load}
- Vehicle type: {vehicle_type}

## Pricing Factors
- Base rate depends on weight and distance
- Urgency: {'Express' if deadline <= 2 else 'Standard' if deadline <= 5 else 'Economy'}
- Fragile handling: {'Extra care required' if fragile else 'Standard handling'}
- Capacity pressure: {'High load - consider premium' if current_load > 70 else 'Normal load'}

Respond with your shipping quote as JSON."""

    return system_prompt, user_prompt


def arbiter_dispute_prompt(
    quality_score: float,
    quality_threshold: float,
    defect_ratio: float,
    supplier_history: dict[str, Any],
) -> tuple[str, str]:
    """Generate prompt for Arbiter agent to resolve disputes.

    Args:
        quality_score: Measured quality score
        quality_threshold: Contractual quality threshold
        defect_ratio: Ratio of defective items
        supplier_history: Supplier's delivery history

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are an Arbiter agent in the MESH supply chain.
Your role is to impartially resolve disputes between buyers and suppliers.

You must respond with a JSON object containing:
{
    "resolution": "favor_buyer" | "favor_supplier" | "split" | "dismiss",
    "buyer_refund": float,
    "supplier_penalty": float,
    "reputation_adjustment": float,
    "findings": ["finding 1", "finding 2", ...],
    "reasoning": "brief explanation",
    "precedent_note": "note for future similar cases"
}

Constraints:
- Be impartial and fair to both parties
- Consider contractual thresholds and actual measurements
- Review supplier history for patterns
- Resolution should reflect the severity of quality issues"""

    meets_threshold = quality_score >= quality_threshold
    user_prompt = f"""Resolve a dispute over delivery quality.

## Quality Assessment
- Measured quality score: {quality_score:.2f}
- Contractual threshold: {quality_threshold:.2f}
- Defect ratio: {defect_ratio:.2%}
- {'Quality MEETS threshold' if meets_threshold else 'Quality BELOW threshold'}

## Supplier History
{json.dumps(supplier_history, indent=2, default=str)}

## Dispute Context
- Buyer claims quality issues
- Supplier disputes the assessment
- Both parties agreed to arbitration

## Resolution Guidelines
- If quality meets threshold: likely favor supplier or dismiss
- If quality below threshold: likely favor buyer
- Consider supplier history - first offense vs. pattern
- Balance penalties to be fair but deterrent

Respond with your dispute resolution as JSON."""

    return system_prompt, user_prompt


def healing_analysis_prompt(
    agent_role: str,
    active_orders: int,
    mesh_state: dict[str, Any],
    failure_history: list[dict[str, Any]],
    candidate_capabilities: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    """Generate prompt for self-healing analysis.

    Args:
        agent_role: Role of the agent being analyzed
        active_orders: Number of active orders
        mesh_state: Current state of the mesh network
        failure_history: Recent failure events
        candidate_capabilities: Optional list of candidate agents with their capabilities

    Returns:
        (system_prompt, user_prompt) tuple
    """
    system_prompt = """You are a Self-Healing agent in the MESH supply chain.
Your role is to analyze failures and recommend recovery actions to maintain
network resilience and order fulfillment.

You must respond with a JSON object containing:
{
    "diagnosis": "root cause description",
    "severity": "low" | "medium" | "high" | "critical",
    "recommended_actions": [
        {
            "action": "redistribute" | "replace" | "retry" | "escalate",
            "target": "agent_id or role",
            "params": {...}
        }
    ],
    "affected_orders": ["order_id", ...],
    "estimated_recovery_epochs": int,
    "prevention_suggestions": ["suggestion", ...]
}

Constraints:
- Prioritize completing active orders
- Consider network stability when redistributing work
- Balance quick recovery with thorough diagnosis
- Suggest preventive measures when patterns emerge
- When recommending replacement agents, match their declared capabilities
  to the failed agent's workload
- Agents with more relevant capability overlap should be preferred for
  redistribution
- Consider capability descriptions to understand the depth of each
  agent's expertise"""

    candidates_section = ""
    if candidate_capabilities:
        cand_lines = []
        for cand in candidate_capabilities:
            agent_id = cand.get('agent_id', 'unknown')
            role = cand.get('role', 'unknown')
            cand_lines.append(f"### Agent: {agent_id} (Role: {role})")
            cand_lines.append(format_capabilities_context(cand.get('capabilities', [])))
        candidates_section = f"""
## Available Replacement Candidates
{chr(10).join(cand_lines)}
"""

    user_prompt = f"""Analyze a potential failure situation in the mesh network.

## Agent Status
- Role: {agent_role}
- Active orders: {active_orders}

## Mesh Network State
{json.dumps(mesh_state, indent=2, default=str)}

## Recent Failure History
{json.dumps(failure_history[-10:] if failure_history else [], indent=2, default=str)}
{candidates_section}
## Analysis Tasks
1. Identify root cause or pattern in failures
2. Assess severity and impact on active orders
3. Recommend recovery actions
4. Suggest preventive measures

Respond with your healing analysis as JSON."""

    return system_prompt, user_prompt
