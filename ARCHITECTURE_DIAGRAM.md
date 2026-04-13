# MESH Architecture Diagrams

## System Overview

```mermaid
graph TB
    subgraph "Presentation Layer"
        D[DASHBOARD<br/>SvelteKit + WebSocket]
    end

    subgraph "Gateway Layer"
        B[BRIDGE<br/>MQTT to WebSocket]
    end

    subgraph "Agent Layer"
        BUYER[Buyer Agent]
        SUP1[Supplier A]
        SUP2[Supplier B]
        LOG[Logistics Agent]
        INSP[Inspector Agent]
        ORACLE[Oracle Agent]
    end

    subgraph "Core Framework"
        IDENTITY[Ed25519 Identity]
        HLC[Hybrid Logical Clocks]
        CRYPTO[HMAC-SHA256 Signing]
        LEDGER[Double-Entry Ledger]
        REP[Reputation Engine]
        REG[Peer Registry]
        NEG[Negotiation Engine]
        HEAL[Self-Healing]
    end

    subgraph "Consensus Layer"
        FOX1[FoxMQ Node 1]
        FOX2[FoxMQ Node 2]
        FOX3[FoxMQ Node 3]
        FOX4[FoxMQ Node 4]
    end

    D <--WebSocket--> B
    B <--MQTT--> FOX1
    B <--MQTT--> FOX2
    
    BUYER <--MQTT--> FOX1
    INSP <--MQTT--> FOX1
    SUP1 <--MQTT--> FOX2
    ORACLE <--MQTT--> FOX2
    SUP2 <--MQTT--> FOX3
    LOG <--MQTT--> FOX4
    
    FOX1 <--Hashgraph--> FOX2
    FOX2 <--Hashgraph--> FOX3
    FOX3 <--Hashgraph--> FOX4
    FOX4 <--Hashgraph--> FOX1
    
    BUYER --- IDENTITY
    BUYER --- HLC
    BUYER --- LEDGER
    BUYER --- NEG
    
    SUP1 --- REP
    SUP1 --- REG
    SUP1 --- HEAL
```

## Order Lifecycle Flow

```mermaid
sequenceDiagram
    participant O as Oracle
    participant B as Buyer
    participant S1 as Supplier A
    participant S2 as Supplier B
    participant L as Logistics
    participant I as Inspector

    Note over O,I: Phase 0: DISCOVERY
    O->>+B: Market Price Update
    
    Note over B,I: Phase 1-2: REQUEST & BID
    B->>S1: PurchaseOrderRequest (50 displays, max $120)
    B->>S2: PurchaseOrderRequest
    S1->>B: SupplierBid ($105/unit)
    S2->>B: SupplierBid ($115/unit)
    
    Note over B,I: Phase 3: NEGOTIATE
    B->>S1: CounterOffer ($95/unit)
    S1->>B: BidAcceptance ($98/unit)
    
    Note over B,I: Phase 4: COMMIT
    B->>B: escrow_lock($4,900)
    B->>S1: OrderCommit
    
    Note over B,I: Phase 5: EXECUTE
    B->>L: ShippingRequest
    L->>B: ShippingBid
    B->>L: ShippingAssign
    L->>B: TransitUpdate (picked_up)
    L->>B: TransitUpdate (in_transit)
    L->>B: TransitUpdate (delivered)
    
    Note over B,I: Phase 6: VERIFY
    B->>I: InspectionRequest
    I->>B: InspectionReport (quality: 0.92)
    
    Note over B,I: Phase 7: SETTLE
    B->>B: escrow_release()
    Note right of B: 92% Supplier<br/>3% Logistics<br/>2% Inspector<br/>3% Burned
```

## Self-Healing Protocol

```mermaid
sequenceDiagram
    participant S as Supplier A
    participant B as Buyer
    participant I as Inspector
    participant S2 as Supplier B

    Note over S,S2: Normal Operation
    loop Every 5 seconds
        S->>B: Heartbeat
        S->>I: Heartbeat
        S->>S2: Heartbeat
    end
    
    Note over S,S2: CRASH at t=70s
    S--xB: Heartbeat stops
    S--xI: Heartbeat stops
    S--xS2: Heartbeat stops
    
    Note over S,S2: Detection (t=85s)
    B->>B: State: SUSPECT (3 missed)
    I->>I: State: SUSPECT
    
    Note over S,S2: Confirmation (t=100s)
    B->>B: State: DEAD (6 missed)
    B->>B: Publish HealthAlert (critical)
    I->>I: Publish HealthAlert (critical)
    Note right of B: Quorum reached!<br/>2+ agents agree
    
    Note over S,S2: Redistribution
    B->>B: Become coordinator<br/>(longest uptime)
    B->>S2: RoleRedistribution<br/>(assume Supplier A's orders)
    
    Note over S,S2: Recovery (t=110s)
    S->>B: DiscoveryAnnounce (status: rejoining)
    S->>I: DiscoveryAnnounce
    S->>S2: DiscoveryAnnounce
    Note right of S: 50% capacity<br/>for 2 epochs
    
    Note over S,S2: Full Recovery (t=130s)
    S->>B: Heartbeat (full capacity)
```

## Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> ACTIVE: start()
    ACTIVE --> BUSY: take_order()
    BUSY --> ACTIVE: complete_order()
    ACTIVE --> DEGRADED: failure_detected()
    DEGRADED --> ACTIVE: recovery()
    ACTIVE --> SHUTDOWN: stop()
    DEGRADED --> SHUTDOWN: stop()
    SHUTDOWN --> [*]
    
    note right of ACTIVE
        Peer View States:
        ACTIVE --> SUSPECT
        SUSPECT --> DEAD
        DEAD --> REJOINING
        REJOINING --> ACTIVE
    end note
```

## Negotiation State Machine

```mermaid
stateDiagram-v2
    [*] --> COLLECTING_BIDS: publish_order()
    COLLECTING_BIDS --> EVALUATING: bid_deadline
    
    EVALUATING --> ACCEPTED: price <= 95% market
    EVALUATING --> COUNTERING: should_counter()
    EVALUATING --> REJECTED: price > max
    
    COUNTERING --> AWAITING_RESPONSE: send_counter()
    AWAITING_RESPONSE --> ACCEPTED: accepted
    AWAITING_RESPONSE --> COUNTERING: counter_received
    AWAITING_RESPONSE --> REJECTED: rejected
    AWAITING_RESPONSE --> TIMED_OUT: timeout
    
    ACCEPTED --> [*]
    REJECTED --> [*]
    TIMED_OUT --> [*]
```

## Economic Model

```mermaid
pie title Settlement Distribution (per $100 order)
    "Supplier" : 92
    "Logistics" : 3
    "Inspector" : 2
    "Burned" : 3
```

## Message Flow Architecture

```mermaid
graph LR
    subgraph "Discovery"
        A1[mesh/discovery/announce]
        A2[mesh/discovery/heartbeat]
        A3[mesh/discovery/goodbye]
    end
    
    subgraph "Orders"
        B1[orders/{id}/request]
        B2[orders/{id}/bid]
        B3[orders/{id}/counter]
        B4[orders/{id}/accept]
        B5[orders/{id}/commit]
    end
    
    subgraph "Shipping"
        C1[shipping/{id}/request]
        C2[shipping/{id}/bid]
        C3[shipping/{id}/assign]
        C4[shipping/{id}/transit]
    end
    
    subgraph "Quality"
        D1[quality/{id}/request]
        D2[quality/{id}/report]
    end
    
    subgraph "Economy"
        E1[ledger/transactions]
        E2[ledger/escrow]
        E3[reputation/updates]
    end
    
    subgraph "Health"
        F1[mesh/health/alerts]
        F2[mesh/health/redistribution]
    end
```

## Security Model

```mermaid
graph TB
    subgraph "Identity Layer"
        ED[Ed25519 Keypair]
        ID[Agent ID = SHA-256(pubkey)[:16]]
    end
    
    subgraph "Message Layer"
        PL[Payload]
        HL[Header + HLC]
        CJ[Canonical JSON]
        HM[HMAC-SHA256]
        RD[Replay Detector]
    end
    
    subgraph "Consensus Layer"
        BFT[BFT Ordering<br/>FoxMQ Hashgraph]
    end
    
    ED --> ID
    PL --> CJ
    HL --> CJ
    CJ --> HM
    HM --> RD
    RD --> BFT
```

## SDK Architecture

```mermaid
graph TB
    subgraph "Application"
        APP[Your Agent Code]
    end
    
    subgraph "SDK Layer"
        TS[TypeScript SDK]
        PY[Python Framework]
    end
    
    subgraph "Transport Layer"
        WS[WebSocket]
        MQTT[MQTT 5.0]
    end
    
    subgraph "Gateway"
        GW[AgentMesh Gateway]
    end
    
    subgraph "Core Mesh"
        FOX[FoxMQ Cluster]
        AGENTS[MESH Agents]
    end
    
    APP --> TS
    APP --> PY
    TS --> WS
    PY --> MQTT
    WS --> GW
    MQTT --> FOX
    GW --> FOX
    FOX --> AGENTS
```
