<svelte:head>
  <title>Architecture — MESH Documentation</title>
  <meta name="description" content="MESH system architecture: layered design, agent roles, security model, economic model, and self-healing mechanisms." />
</svelte:head>

<h1>System Overview</h1>

<p>MESH is a decentralized multi-agent supply chain coordination system. There is <strong>no central orchestrator</strong>. All coordination happens through BFT-ordered MQTT messages on a FoxMQ cluster. Because FoxMQ uses Hashgraph consensus, every agent sees messages in the same total order, making all local state computations converge deterministically.</p>

<p>The architecture consists of four primary layers:</p>

<ul>
  <li><strong>Layer 1: FoxMQ BFT Cluster</strong> — Foundation layer providing Byzantine fault-tolerant messaging</li>
  <li><strong>Layer 2: Core Framework</strong> — Agent runtime with identity, state, and ledger management</li>
  <li><strong>Layer 3: Agent System</strong> — Five specialized agent roles for supply chain operations</li>
  <li><strong>Layer 4: Negotiation & Healing</strong> — Multi-round negotiation and self-healing mechanisms</li>
</ul>

<h2 id="layered-architecture">Layered Architecture</h2>

<p>Each layer builds on the previous one, providing abstractions that enable complex supply chain coordination:</p>

<div class="architecture-diagram">
  <div class="layer layer-6">
    <div class="layer-title">Dashboard (SvelteKit)</div>
    <div class="layer-desc">Real-time visualization: Agent Cards, Order Flow, Event Log, Metrics Panels</div>
  </div>
  <div class="layer layer-5">
    <div class="layer-title">Platform SaaS</div>
    <div class="layer-desc">REST API (FastAPI) • WebSocket Gateway • MQTT Sink • Payments Integration</div>
  </div>
  <div class="layer layer-4">
    <div class="layer-title">Negotiation & Self-Healing</div>
    <div class="layer-desc">Negotiation Engine • Self-Healing Detector • Arbiter • Recovery Manager</div>
  </div>
  <div class="layer layer-3">
    <div class="layer-title">Agent Roles</div>
    <div class="layer-desc">Buyer • Supplier • Logistics • Inspector • Oracle</div>
  </div>
  <div class="layer layer-2">
    <div class="layer-title">Core Framework</div>
    <div class="layer-desc">Identity • State • Registry • Ledger • Reputation • Clock • Crypto • Transport</div>
  </div>
  <div class="layer layer-1">
    <div class="layer-title">FoxMQ BFT Cluster</div>
    <div class="layer-desc">4-Node Hashgraph Gossip • MQTT 5.0 • Sub-100ms Total Ordering</div>
  </div>
</div>

<h3>Layer 1: FoxMQ BFT Cluster</h3>

<p>The foundation is a 4-node FoxMQ cluster providing:</p>

<ul>
  <li><strong>Total ordering</strong>: All agents see messages in identical order via Hashgraph consensus</li>
  <li><strong>Byzantine fault tolerance</strong>: Tolerates f &lt; n/3 faulty nodes (1 of 4)</li>
  <li><strong>MQTT 5.0</strong>: Standard pub/sub with QoS 0/1/2, retained messages, wildcards</li>
  <li><strong>Sub-100ms latency</strong>: Hashgraph gossip protocol</li>
</ul>

<p>Cluster topology forms a fully-connected mesh:</p>

<pre><code>foxmq-node1 (1883) &lt;--&gt; foxmq-node2 (1884)
       ^                        ^
       |                        |
       v                        v
foxmq-node4 (1886) &lt;--&gt; foxmq-node3 (1885)</code></pre>

<h3>Layer 2: Core Framework</h3>

<p>The <code>mesh/</code> package provides the agent runtime:</p>

<table>
  <thead>
    <tr>
      <th>Component</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Identity</strong></td>
      <td>Ed25519 keypairs, agent_id = SHA-256(public_key)[:16]</td>
    </tr>
    <tr>
      <td><strong>State</strong></td>
      <td>Agent lifecycle: IDLE → ACTIVE → BUSY → RECOVERING</td>
    </tr>
    <tr>
      <td><strong>Registry</strong></td>
      <td>Peer discovery via retained announcements + heartbeat monitoring</td>
    </tr>
    <tr>
      <td><strong>Transport</strong></td>
      <td>MQTT pub/sub wrapper with QoS-aware publishing</td>
    </tr>
    <tr>
      <td><strong>Clock</strong></td>
      <td>Hybrid Logical Clocks for causal ordering</td>
    </tr>
    <tr>
      <td><strong>Crypto</strong></td>
      <td>HMAC-SHA256 message signing, replay detection (30s window)</td>
    </tr>
    <tr>
      <td><strong>Ledger</strong></td>
      <td>MESH_CREDIT balances, escrow, settlement</td>
    </tr>
    <tr>
      <td><strong>Reputation</strong></td>
      <td>Per-capability scores with decay toward neutral (0.5)</td>
    </tr>
  </tbody>
</table>

<h3>Layer 3: Agent Roles</h3>

<p>Five specialized agents extend <code>BaseAgent</code>:</p>

<ul>
  <li><strong>Buyer</strong>: Publishes purchase orders, evaluates bids, manages escrow</li>
  <li><strong>Supplier</strong>: Monitors orders, submits bids, fulfills commitments</li>
  <li><strong>Logistics</strong>: Handles shipping, provides transit updates</li>
  <li><strong>Inspector</strong>: Performs quality inspections, publishes reports</li>
  <li><strong>Oracle</strong>: Publishes market prices and demand forecasts</li>
</ul>

<h3>Layer 4: Negotiation & Healing</h3>

<ul>
  <li><strong>Negotiation Engine</strong>: Multi-round counter-offer protocol (max 3 rounds) with pluggable strategies</li>
  <li><strong>Self-Healing</strong>: Heartbeat-based failure detection, role redistribution, gradual recovery</li>
  <li><strong>Arbiter</strong>: Dispute resolution and tie-breaking for simultaneous bids</li>
</ul>

<h2 id="agent-roles">Agent Roles</h2>

<p>Every agent on the mesh has exactly one role. Roles determine what topics an agent subscribes to and what actions it can take.</p>

<table>
  <thead>
    <tr>
      <th>Role</th>
      <th>Primary Action</th>
      <th>Key Topics</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Buyer</strong></td>
      <td>Publish orders, evaluate bids</td>
      <td><code>order:request</code>, <code>order:accept</code></td>
    </tr>
    <tr>
      <td><strong>Supplier</strong></td>
      <td>Submit bids, fulfill orders</td>
      <td><code>order:bid</code>, <code>order:commit</code></td>
    </tr>
    <tr>
      <td><strong>Logistics</strong></td>
      <td>Ship goods, provide tracking</td>
      <td><code>shipping:bid</code>, <code>shipping:transit</code></td>
    </tr>
    <tr>
      <td><strong>Inspector</strong></td>
      <td>Verify quality</td>
      <td><code>inspection:report</code></td>
    </tr>
    <tr>
      <td><strong>Oracle</strong></td>
      <td>Provide market data</td>
      <td><code>market:prices</code>, <code>market:demand</code></td>
    </tr>
  </tbody>
</table>

<h3>Buyer</h3>

<p>The buyer initiates the supply chain process:</p>

<ol>
  <li>Publishes a <code>PurchaseOrderRequest</code> with goods, quantity, max price, and quality threshold</li>
  <li>Receives <code>SupplierBid</code> messages during the bid window</li>
  <li>Evaluates bids using a scoring formula (price weight + reputation weight)</li>
  <li>Publishes <code>BidAcceptance</code> for the winner (triggers escrow lock)</li>
  <li>Monitors order status through fulfillment, shipping, and inspection</li>
  <li>After inspection passes, settlement releases escrow to the supplier</li>
</ol>

<h3>Supplier</h3>

<p>The supplier responds to purchase orders:</p>

<ol>
  <li>Subscribes to <code>order:request</code> filtered by capabilities</li>
  <li>Checks if the order matches its goods categories and pricing model</li>
  <li>Publishes a <code>SupplierBid</code> with price, quantity, and estimated fulfillment time</li>
  <li>May receive <code>CounterOffer</code> messages and respond in negotiation rounds</li>
  <li>On acceptance, publishes <code>OrderCommit</code> to confirm</li>
  <li>Fulfills the order and updates status to <code>fulfilling</code> → <code>shipping</code></li>
</ol>

<h3>Logistics</h3>

<p>The logistics provider handles physical delivery:</p>

<ol>
  <li>Subscribes to <code>shipping:request</code></li>
  <li>Publishes <code>ShippingBid</code> with price, estimated transit time, and vehicle type</li>
  <li>On assignment, picks up goods and publishes <code>TransitUpdate</code> messages</li>
  <li>Status flow: <code>picked_up</code> → <code>in_transit</code> → <code>out_for_delivery</code> → <code>delivered</code></li>
</ol>

<p>Transit updates use QoS 0 for high-frequency, low-overhead tracking.</p>

<h3>Inspector</h3>

<p>The inspector verifies delivered goods:</p>

<ol>
  <li>Subscribes to <code>inspection:request</code></li>
  <li>Performs quality assessment (physical sensors, ML models, manual checks)</li>
  <li>Publishes <code>InspectionReport</code> with quality score, defect count, and recommendation</li>
  <li>Recommendation: <code>accept</code>, <code>partial_accept</code>, or <code>reject</code></li>
</ol>

<p>Inspection reports use QoS 2 (exactly-once) since they affect settlement.</p>

<h3>Oracle</h3>

<p>The oracle provides market intelligence:</p>

<ol>
  <li>Publishes <code>MarketPriceUpdate</code> with prices per goods category</li>
  <li>Publishes <code>MarketDemand</code> with demand forecasts and growth rates</li>
  <li>Other agents use oracle data to calibrate pricing strategies</li>
</ol>

<p>Oracles are passive — they publish data but don't participate in orders.</p>

<h2 id="security">Security Model</h2>

<p>MESH employs multiple cryptographic mechanisms to ensure message integrity and agent authenticity.</p>

<h3>Identity</h3>

<p>Each agent generates an <strong>Ed25519 keypair</strong> on creation:</p>

<ul>
  <li><strong>Private key</strong>: Used for signing (never transmitted)</li>
  <li><strong>Public key</strong>: Shared via <code>DiscoveryAnnounce</code> messages</li>
  <li><strong>Agent ID</strong>: <code>SHA-256(public_key)[:16]</code> (16-character hex identifier)</li>
</ul>

<pre><code>from mesh.core.identity import AgentIdentity

identity = AgentIdentity.generate()
print(identity.agent_id)      # "a3f8c2e1b9d04a7c"
print(identity.public_key_hex) # Full Ed25519 public key</code></pre>

<h3>Message Signing</h3>

<p>Every message published to the mesh is signed with <strong>HMAC-SHA256</strong>:</p>

<ol>
  <li>The payload is serialized to <strong>canonical JSON</strong> (sorted keys, no whitespace)</li>
  <li>An HMAC-SHA256 is computed over the canonical JSON using a shared secret</li>
  <li>The hex digest is included in the <code>MessageEnvelope.signature</code> field</li>
</ol>

<pre><code>&#123;
  "header": &#123;
    "message_id": "uuid",
    "timestamp": "2026-04-03T10:30:00Z",
    "sender_id": "a3f8c2e1b9d04a7c",
    "sender_role": "buyer",
    "protocol_version": "mesh/1.0"
  &#125;,
  "payload": &#123; "order_id": "po-001", "goods": "microcontrollers" &#125;,
  "signature": "a1b2c3d4e5f6..."
&#125;</code></pre>

<h3>Replay Detection</h3>

<p>Messages include a <strong>30-second replay window</strong>:</p>

<ul>
  <li>Each agent tracks the <code>message_id</code> of recently processed messages</li>
  <li>Duplicate <code>message_id</code> values within the window are rejected</li>
  <li>The <code>timestamp</code> field must be within 30 seconds of the receiver's clock</li>
  <li>Combined with HLC ordering, this prevents both replay and reordering attacks</li>
</ul>

<h3>Hybrid Logical Clocks</h3>

<p>HLC provides causal ordering across distributed agents:</p>

<pre><code>Format: physical_ms:logical:node_id
Example: 1743676200000:0:a3f8c2e1b9d04a7c</code></pre>

<ul>
  <li><strong>physical_ms</strong>: Wall clock time in milliseconds</li>
  <li><strong>logical</strong>: Logical counter for events at the same physical time</li>
  <li><strong>node_id</strong>: Agent ID to break ties</li>
</ul>

<p>HLC guarantees: if event A causally precedes event B, then <code>HLC(A) &lt; HLC(B)</code>.</p>

<h3>Threat Model</h3>

<table>
  <thead>
    <tr>
      <th>Threat</th>
      <th>Mitigation</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Message tampering</td>
      <td>HMAC-SHA256 signature on every message</td>
    </tr>
    <tr>
      <td>Replay attacks</td>
      <td>30-second window + message_id deduplication</td>
    </tr>
    <tr>
      <td>Identity spoofing</td>
      <td>Ed25519 keypairs + agent_id derived from public key</td>
    </tr>
    <tr>
      <td>Byzantine agents</td>
      <td>BFT consensus (f &lt; n/3) + reputation penalties</td>
    </tr>
    <tr>
      <td>Eavesdropping</td>
      <td>TLS for all transport layers</td>
    </tr>
    <tr>
      <td>API key theft</td>
      <td>Scoped keys with expiration, SHA-256 hashed storage</td>
    </tr>
  </tbody>
</table>

<h2 id="economic-model">Economic Model</h2>

<p>MESH_CREDIT is the internal currency of the AgentMesh network. It enables trustless economic coordination between agents.</p>

<h3>Initial Balance</h3>

<p>Each agent starts with a configurable balance (default: 10,000 MESH_CREDIT). This allows agents to participate in transactions immediately.</p>

<h3>Transaction Types</h3>

<table>
  <thead>
    <tr>
      <th>Type</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>escrow_lock</code></td>
      <td>Buyer's funds locked when a bid is accepted</td>
    </tr>
    <tr>
      <td><code>escrow_release</code></td>
      <td>Escrow released to supplier after successful delivery</td>
    </tr>
    <tr>
      <td><code>payment</code></td>
      <td>Direct payment between agents</td>
    </tr>
    <tr>
      <td><code>fee</code></td>
      <td>Platform fee (2% of each settlement)</td>
    </tr>
    <tr>
      <td><code>penalty</code></td>
      <td>Deducted for late delivery, quality failures, or no-shows</td>
    </tr>
    <tr>
      <td><code>reward</code></td>
      <td>Bonus for exceptional performance</td>
    </tr>
    <tr>
      <td><code>burn</code></td>
      <td>1% of each transaction is permanently removed (deflationary)</td>
    </tr>
  </tbody>
</table>

<h3>Settlement Distribution</h3>

<p>After successful order completion:</p>

<pre><code>1. Buyer accepts bid:
   - Escrow locks: agreed_price * quantity
   - Buyer balance: -12,500 (locked)

2. Supplier fulfills + delivers:
   - Logistics paid: 500 MESH_CREDIT
   - Inspector paid: 200 MESH_CREDIT

3. Inspection passes:
   - Escrow released to supplier: 12,500
   - Platform fee (2%): -250 (from supplier)
   - Burn (1%): -125 (from transaction)
   - Net to supplier: 12,125

4. Final distribution:
   Supplier:   92%
   Logistics:  3%
   Inspector:  2%
   Burn:       3% (deflationary)</code></pre>

<h3>Penalty Scenarios</h3>

<table>
  <thead>
    <tr>
      <th>Event</th>
      <th>Penalty</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Late delivery (&gt;50% over deadline)</td>
      <td>5% of order value</td>
    </tr>
    <tr>
      <td>Quality failure (score &lt; threshold)</td>
      <td>10% of order value</td>
    </tr>
    <tr>
      <td>No-show (accepted bid, never committed)</td>
      <td>15% of order value</td>
    </tr>
    <tr>
      <td>Byzantine behavior (detected by consensus)</td>
      <td>25% of order value + quarantine</td>
    </tr>
  </tbody>
</table>

<h3>Escrow Rules</h3>

<ul>
  <li>Escrow is locked atomically when the buyer publishes <code>BidAcceptance</code></li>
  <li>Escrow cannot be partially released — it's all-or-nothing</li>
  <li>On order cancellation, escrow returns to the buyer minus any penalties</li>
  <li>On dispute, the arbiter decides escrow distribution</li>
</ul>

<h3>Reputation Impact</h3>

<p>Economic outcomes directly affect reputation scores:</p>

<table>
  <thead>
    <tr>
      <th>Outcome</th>
      <th>Reputation Change</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Order fulfilled on time</td>
      <td>+0.03</td>
    </tr>
    <tr>
      <td>Quality inspection passed</td>
      <td>+0.02</td>
    </tr>
    <tr>
      <td>On-time delivery</td>
      <td>+0.03</td>
    </tr>
    <tr>
      <td>Late delivery</td>
      <td>-0.05</td>
    </tr>
    <tr>
      <td>Quality failure</td>
      <td>-0.08</td>
    </tr>
    <tr>
      <td>No-show</td>
      <td>-0.15</td>
    </tr>
    <tr>
      <td>Byzantine behavior</td>
      <td>-0.25</td>
    </tr>
    <tr>
      <td>Natural decay (per epoch)</td>
      <td>toward 0.5</td>
    </tr>
  </tbody>
</table>

<p>Reputation is <strong>per-capability</strong>, not global. A supplier with reputation 0.95 in "electronics" may have 0.60 in "batteries" if they're less experienced there.</p>

<h2 id="self-healing">Self-Healing</h2>

<p>The AgentMesh self-healing system operates without any central coordinator. It uses three components:</p>

<ol>
  <li><strong>Detector</strong>: Monitors heartbeats and detects agent failures</li>
  <li><strong>Redistributor</strong>: Reassigns roles from failed agents to healthy ones</li>
  <li><strong>Recovery</strong>: Manages gradual capacity ramp-up for replacement agents</li>
</ol>

<h3>Failure Detection</h3>

<p>Every agent publishes <code>Heartbeat</code> messages every 5 seconds (configurable):</p>

<pre><code>&#123;
  "agent_id": "supplier-01",
  "role": "supplier",
  "status": "healthy",
  "load": 0.35,
  "active_orders": 2,
  "uptime_seconds": 3600
&#125;</code></pre>

<h4>Detection Rules</h4>

<table>
  <thead>
    <tr>
      <th>Condition</th>
      <th>Action</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1 missed heartbeat (5s)</td>
      <td>Status: <code>warning</code> — continue monitoring</td>
    </tr>
    <tr>
      <td>2 missed heartbeats (10s)</td>
      <td>Status: <code>critical</code> — prepare for redistribution</td>
    </tr>
    <tr>
      <td>3 missed heartbeats (15s)</td>
      <td>Status: <code>fatal</code> — trigger redistribution</td>
    </tr>
  </tbody>
</table>

<h3>Quorum Confirmation</h3>

<p>A single agent's detection is not sufficient. Death is confirmed when >= 2 independent agents publish <code>HealthAlert</code> with severity <code>critical</code> for the same peer. This prevents false positives from network partitions.</p>

<h3>Role Redistribution</h3>

<p>When an agent fails, the redistributor selects a replacement:</p>

<h4>Selection Criteria</h4>

<ol>
  <li><strong>Same role</strong>: The replacement must have the same role or compatible capabilities</li>
  <li><strong>Lowest load</strong>: Prefer agents with the lowest current <code>load</code> factor</li>
  <li><strong>Highest reputation</strong>: Among equally loaded agents, prefer higher reputation</li>
  <li><strong>Not recovering</strong>: Agents already in recovery mode are deprioritized</li>
</ol>

<h4>What Gets Transferred</h4>

<ul>
  <li><strong>Active orders</strong>: All in-progress orders from the failed agent</li>
  <li><strong>Capabilities</strong>: The failed agent's capability set</li>
  <li><strong>State</strong>: Current order states (bidding, committed, fulfilling)</li>
</ul>

<h3>Recovery Protocol</h3>

<p>The replacement agent doesn't immediately operate at full capacity:</p>

<h4>Ramp-Up Schedule</h4>

<table>
  <thead>
    <tr>
      <th>Phase</th>
      <th>Capacity</th>
      <th>Duration</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Initial</td>
      <td>50%</td>
      <td>First 30 seconds</td>
    </tr>
    <tr>
      <td>Warming</td>
      <td>75%</td>
      <td>30-60 seconds</td>
    </tr>
    <tr>
      <td>Full</td>
      <td>100%</td>
      <td>After 60 seconds</td>
    </tr>
  </tbody>
</table>

<h4>Recovery Behavior</h4>

<ul>
  <li>During ramp-up, the agent handles transferred orders but limits new bids</li>
  <li>If the replacement also fails during ramp-up, the system escalates to the next candidate</li>
  <li>The original agent can rejoin with status <code>rejoining</code> after recovery</li>
</ul>

<h3>Rejoining</h3>

<p>If a failed agent comes back online:</p>

<ol>
  <li>It announces with <code>status: "rejoining"</code> instead of <code>online</code></li>
  <li>It does not immediately reclaim its transferred orders</li>
  <li>It starts at 50% capacity and ramps up</li>
  <li>Transferred orders stay with the replacement to avoid disruption</li>
  <li>New orders are gradually routed to the rejoining agent</li>
</ol>

<style>
  .architecture-diagram {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin: 24px 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    overflow: hidden;
  }
  
  .layer {
    padding: 16px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  }
  
  .layer:last-child {
    border-bottom: none;
  }
  
  .layer-title {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  
  .layer-desc {
    font-family: var(--font-heading);
    font-size: 0.85rem;
    color: var(--text-secondary);
  }
  
  .layer-1 { background: linear-gradient(90deg, rgba(255, 111, 0, 0.15) 0%, rgba(255, 111, 0, 0.05) 100%); }
  .layer-1 .layer-title { color: #ff6f00; }
  
  .layer-2 { background: linear-gradient(90deg, rgba(255, 111, 0, 0.12) 0%, rgba(255, 111, 0, 0.04) 100%); }
  .layer-2 .layer-title { color: #ff8533; }
  
  .layer-3 { background: linear-gradient(90deg, rgba(255, 111, 0, 0.09) 0%, rgba(255, 111, 0, 0.03) 100%); }
  .layer-3 .layer-title { color: #ff9b66; }
  
  .layer-4 { background: linear-gradient(90deg, rgba(255, 111, 0, 0.06) 0%, rgba(255, 111, 0, 0.02) 100%); }
  .layer-4 .layer-title { color: #ffb899; }
  
  .layer-5 { background: rgba(255, 255, 255, 0.02); }
  .layer-5 .layer-title { color: var(--text-secondary); }
  
  .layer-6 { background: rgba(255, 255, 255, 0.04); }
  .layer-6 .layer-title { color: var(--text); }
</style>
