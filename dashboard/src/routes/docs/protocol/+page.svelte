<svelte:head>
  <title>Protocol — MESH Documentation</title>
  <meta name="description" content="MESH protocol specification: 8-phase order lifecycle, negotiation strategies, MQTT topic hierarchy, message envelope format, and WebSocket gateway." />
</svelte:head>

<h1>Order Lifecycle</h1>

<p>Every order in the MESH protocol progresses through 8 phases:</p>

<pre><code>Phase 0: DISCOVER    (continuous)
Phase 1: REQUEST     Buyer publishes purchase order
Phase 2: BID         Suppliers submit competing bids
Phase 3: NEGOTIATE   Multi-round counter-offers (max 3 rounds)
Phase 4: COMMIT      Escrow lock + supplier commitment
Phase 5: EXECUTE     Fulfillment + shipping + transit
Phase 6: VERIFY      Quality inspection
Phase 7: SETTLE      Escrow release + reputation updates</code></pre>

<h2>Order Status States</h2>

<p>Orders transition through the following states:</p>

<pre><code>open -> bidding -> negotiating -> committed -> fulfilling
  -> shipping -> delivered -> inspecting -> settled

At any point: -> cancelled | failed | recovering</code></pre>

<table>
  <thead>
    <tr>
      <th>Status</th>
      <th>Phase</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>open</code></td>
      <td>1</td>
      <td>Purchase order published, waiting for bids</td>
    </tr>
    <tr>
      <td><code>bidding</code></td>
      <td>2</td>
      <td>Bids being received during bid window</td>
    </tr>
    <tr>
      <td><code>negotiating</code></td>
      <td>3</td>
      <td>Counter-offers in progress</td>
    </tr>
    <tr>
      <td><code>committed</code></td>
      <td>4</td>
      <td>Supplier committed, escrow locked</td>
    </tr>
    <tr>
      <td><code>fulfilling</code></td>
      <td>5</td>
      <td>Supplier preparing the order</td>
    </tr>
    <tr>
      <td><code>shipping</code></td>
      <td>5</td>
      <td>Goods in transit</td>
    </tr>
    <tr>
      <td><code>delivered</code></td>
      <td>5</td>
      <td>Goods delivered to destination</td>
    </tr>
    <tr>
      <td><code>inspecting</code></td>
      <td>6</td>
      <td>Quality inspection in progress</td>
    </tr>
    <tr>
      <td><code>settled</code></td>
      <td>7</td>
      <td>Payment complete, order finished</td>
    </tr>
    <tr>
      <td><code>cancelled</code></td>
      <td>Any</td>
      <td>Order cancelled (e.g., no bids received)</td>
    </tr>
    <tr>
      <td><code>failed</code></td>
      <td>Any</td>
      <td>Order failed (e.g., supplier disappeared)</td>
    </tr>
    <tr>
      <td><code>recovering</code></td>
      <td>Any</td>
      <td>Order being recovered after agent failure</td>
    </tr>
  </tbody>
</table>

<h2>Phase 1: REQUEST</h2>

<p>The buyer publishes a <code>PurchaseOrderRequest</code>:</p>

<pre><code>&#123;
  "order_id": "po-2026-001",
  "goods": "microcontrollers",
  "category": "semiconductors",
  "quantity": 5000,
  "max_price_per_unit": 2.50,
  "quality_threshold": 0.95,
  "delivery_deadline_seconds": 3600,
  "required_capabilities": ["electronics"],
  "bid_deadline_seconds": 10
&#125;</code></pre>

<p><strong>Topic</strong>: <code>mesh/orders/&#123;order_id&#125;/request</code> (QoS 1)</p>

<h2>Phase 2: BID</h2>

<p>Suppliers with matching capabilities submit bids:</p>

<pre><code>&#123;
  "order_id": "po-2026-001",
  "bid_id": "uuid",
  "supplier_id": "supplier-01",
  "price_per_unit": 2.25,
  "available_quantity": 5000,
  "estimated_fulfillment_seconds": 30,
  "reputation_score": 0.88
&#125;</code></pre>

<p><strong>Topic</strong>: <code>mesh/orders/&#123;order_id&#125;/bid</code> (QoS 1)</p>

<p>The buyer collects bids until <code>bid_deadline_seconds</code> expires.</p>

<h2>Phase 3: NEGOTIATE</h2>

<p>If the buyer wants to negotiate, they send a <code>CounterOffer</code>:</p>

<ul>
  <li>Max 3 rounds</li>
  <li>Only price, quantity, and deadline are negotiable</li>
  <li>Each counter-offer has an expiration</li>
</ul>

<p>See <a href="#negotiation">Negotiation Engine</a> for details.</p>

<h2>Phase 4: COMMIT</h2>

<p>The buyer accepts the best bid:</p>

<ol>
  <li><code>BidAcceptance</code> published → escrow locks <code>agreed_price * quantity</code></li>
  <li>Supplier responds with <code>OrderCommit</code> to confirm</li>
  <li>Order status changes to <code>committed</code></li>
</ol>

<p><strong>Topic</strong>: <code>mesh/orders/&#123;order_id&#125;/accept</code> (QoS 1)<br>
<strong>Topic</strong>: <code>mesh/orders/&#123;order_id&#125;/commit</code> (QoS 2)</p>

<h2>Phase 5: EXECUTE</h2>

<ol>
  <li>Supplier prepares the order (status: <code>fulfilling</code>)</li>
  <li>Buyer publishes <code>ShippingRequest</code> for logistics bids</li>
  <li>Logistics provider submits <code>ShippingBid</code>, gets assigned</li>
  <li><code>TransitUpdate</code> messages track: <code>picked_up</code> → <code>in_transit</code> → <code>delivered</code></li>
</ol>

<h2>Phase 6: VERIFY</h2>

<ol>
  <li>Buyer publishes <code>InspectionRequest</code> to inspectors</li>
  <li>Inspector publishes <code>InspectionReport</code> with quality score</li>
  <li>If <code>passed: true</code>, proceed to settlement</li>
  <li>If <code>passed: false</code>, dispute resolution may be triggered</li>
</ol>

<p><strong>Topic</strong>: <code>mesh/quality/&#123;inspection_id&#125;/report</code> (QoS 2)</p>

<h2>Phase 7: SETTLE</h2>

<p>After successful inspection:</p>

<ol>
  <li>Escrow released to supplier (minus fees)</li>
  <li>Platform fee (2%) deducted</li>
  <li>Burn (1%) permanently removed</li>
  <li>Logistics and inspector paid</li>
  <li>Reputation scores updated for all participants</li>
  <li>Order status: <code>settled</code></li>
</ol>

<h3>Error Handling</h3>

<table>
  <thead>
    <tr>
      <th>Error</th>
      <th>Recovery</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>No bids received</td>
      <td>Order cancelled after bid deadline</td>
    </tr>
    <tr>
      <td>Supplier disappears after commit</td>
      <td>Self-healing redistributes to backup supplier</td>
    </tr>
    <tr>
      <td>Inspection fails</td>
      <td>Dispute raised, arbiter decides escrow</td>
    </tr>
    <tr>
      <td>Logistics loses shipment</td>
      <td>Penalty applied, new shipping request issued</td>
    </tr>
  </tbody>
</table>

<h2 id="negotiation">Negotiation Engine</h2>

<p>The negotiation engine enables multi-round price negotiation between buyers and suppliers. Up to <strong>3 rounds</strong> of counter-offers are supported before the negotiation expires.</p>

<h3>Flow</h3>

<pre><code>Buyer                          Supplier
  |                               |
  |-- PurchaseOrderRequest ------>|
  |                               |
  |&lt;------ SupplierBid -----------|
  |                               |
  |-- CounterOffer (round 1) ----&gt;|  (buyer wants lower price)
  |                               |
  |-- CounterOffer (round 2) ----&gt;|  (supplier adjusts)
  |                               |
  |-- BidAcceptance -------------&gt;|  (buyer accepts)
  |         OR                    |
  |-- BidRejection --------------&gt;|  (buyer walks away)</code></pre>

<h3>Counter-Offer Message</h3>

<pre><code>&#123;
  "order_id": "po-2026-001",
  "counter_id": "uuid",
  "original_bid_id": "bid-uuid",
  "from_agent": "buyer-01",
  "to_agent": "supplier-01",
  "round": 1,
  "proposed_price_per_unit": 2.15,
  "proposed_quantity": null,
  "proposed_deadline_seconds": null,
  "justification": "Market rate for this category is $2.10",
  "expires_seconds": 10
&#125;</code></pre>

<h3>Rules</h3>

<ol>
  <li><strong>Max 3 rounds</strong>: After round 3, the buyer must accept or reject</li>
  <li><strong>Expiration</strong>: Each counter-offer has an <code>expires_seconds</code> deadline</li>
  <li><strong>Only price, quantity, and deadline</strong> can be negotiated</li>
  <li><strong>Justification</strong>: Each counter-offer includes a reason (used by adaptive strategies)</li>
</ol>

<h3>Strategies</h3>

<p>The negotiation engine supports three pluggable pricing strategies:</p>

<h4>Aggressive</h4>

<ul>
  <li>Starts with the lowest viable price</li>
  <li>Makes small concessions (5% per round)</li>
  <li>Walks away if the price exceeds <code>base_price * 1.15</code></li>
  <li>Best for: commodity goods with many suppliers</li>
</ul>

<h4>Conservative</h4>

<ul>
  <li>Starts close to the buyer's max price</li>
  <li>Makes moderate concessions (10% per round)</li>
  <li>Accepts early to secure the order</li>
  <li>Best for: specialized goods with few suppliers</li>
</ul>

<h4>Adaptive</h4>

<ul>
  <li>Analyzes the counter-offer history to determine the other party's strategy</li>
  <li>Adjusts concession size based on the opponent's behavior</li>
  <li>Uses a weighted scoring formula: <code>0.6 * price_factor + 0.4 * reputation_factor</code></li>
  <li>Best for: general-purpose negotiation</li>
</ul>

<h3>Bid Scoring Formula</h3>

<p>After <code>bid_deadline_seconds</code> expires, the buyer's <code>NegotiationEngine</code> evaluates all collected bids:</p>

<pre><code>score = 0.35 * price_score + 0.30 * reputation + 0.20 * speed_score + 0.15 * confidence</code></pre>

<p>Where:</p>

<ul>
  <li><code>price_score = max(0, 1 - price/max_price)</code></li>
  <li><code>speed_score = max(0, 1 - estimated_time/deadline)</code></li>
  <li><code>reputation</code> and <code>confidence</code> from the <code>ReputationEngine</code></li>
</ul>

<h3>Decision Logic</h3>

<ul>
  <li>If best bid price &lt;= 95% of market price: <strong>accept immediately</strong> (skip Phase 3)</li>
  <li>If best bid price &lt;= max_price: <strong>counter</strong> if rounds remaining</li>
  <li>If best bid price &gt; max_price: <strong>counter</strong> if rounds remaining, else <strong>reject</strong></li>
</ul>

<h3>Arbiter</h3>

<p>When two suppliers submit bids at the same price and reputation, the <strong>arbiter</strong> resolves ties:</p>

<ol>
  <li><strong>Earlier timestamp</strong> wins (HLC ordering)</li>
  <li>If timestamps are identical: <strong>lower agent_id</strong> wins (deterministic)</li>
  <li>The arbiter's decision is final and published as a <code>BidAcceptance</code></li>
</ol>

<h2 id="mqtt-topics">MQTT Topic Hierarchy</h2>

<p>All MESH protocol topics are namespaced under <code>mesh/</code>:</p>

<pre><code>mesh/
├── discovery/
│   ├── announce          QoS 1, Retained
│   ├── heartbeat         QoS 0
│   └── goodbye           QoS 1
├── orders/&#123;order_id&#125;/
│   ├── request           QoS 1
│   ├── bid               QoS 1
│   ├── counter           QoS 1
│   ├── accept            QoS 1
│   ├── reject            QoS 1
│   ├── commit            QoS 2
│   └── status            QoS 1
├── shipping/&#123;shipment_id&#125;/
│   ├── request           QoS 1
│   ├── bid               QoS 1
│   ├── assign            QoS 1
│   ├── transit           QoS 0
│   ├── deliver           QoS 1
│   └── confirm           QoS 1
├── quality/&#123;inspection_id&#125;/
│   ├── request           QoS 1
│   ├── report            QoS 2
│   └── dispute           QoS 2
├── market/
│   ├── prices            QoS 1
│   ├── demand            QoS 1
│   └── alerts            QoS 1
├── reputation/
│   ├── scores            QoS 2
│   └── updates           QoS 2
├── ledger/
│   ├── balances          QoS 2
│   ├── transactions      QoS 2
│   └── escrow            QoS 2
├── health/
│   ├── alerts            QoS 1
│   ├── redistribution    QoS 2
│   └── recovery          QoS 1
└── system/
    └── metrics           QoS 0</code></pre>

<h3>QoS Levels</h3>

<table>
  <thead>
    <tr>
      <th>QoS</th>
      <th>Name</th>
      <th>When to Use</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>0</strong></td>
      <td>Fire &amp; Forget</td>
      <td>Heartbeats, transit updates, metrics — high-frequency, loss-tolerant</td>
    </tr>
    <tr>
      <td><strong>1</strong></td>
      <td>At Least Once</td>
      <td>Bids, requests, status updates — important but idempotent</td>
    </tr>
    <tr>
      <td><strong>2</strong></td>
      <td>Exactly Once</td>
      <td>Commits, settlements, reputation, ledger — critical state changes</td>
    </tr>
  </tbody>
</table>

<h3>Topic Reference</h3>

<table>
  <thead>
    <tr>
      <th>Topic Pattern</th>
      <th>QoS</th>
      <th>Publisher</th>
      <th>Subscribers</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>mesh/discovery/announce</code></td>
      <td>1</td>
      <td>All agents</td>
      <td>All agents</td>
    </tr>
    <tr>
      <td><code>mesh/discovery/heartbeat</code></td>
      <td>0</td>
      <td>All agents</td>
      <td>All agents</td>
    </tr>
    <tr>
      <td><code>mesh/orders/+/request</code></td>
      <td>1</td>
      <td>Buyer</td>
      <td>Suppliers</td>
    </tr>
    <tr>
      <td><code>mesh/orders/+/bid</code></td>
      <td>1</td>
      <td>Suppliers</td>
      <td>Buyer</td>
    </tr>
    <tr>
      <td><code>mesh/orders/+/commit</code></td>
      <td>2</td>
      <td>Supplier</td>
      <td>Buyer</td>
    </tr>
    <tr>
      <td><code>mesh/shipping/+/transit</code></td>
      <td>0</td>
      <td>Logistics</td>
      <td>Buyer, Supplier</td>
    </tr>
    <tr>
      <td><code>mesh/quality/+/report</code></td>
      <td>2</td>
      <td>Inspector</td>
      <td>Buyer, Supplier</td>
    </tr>
    <tr>
      <td><code>mesh/ledger/transactions</code></td>
      <td>2</td>
      <td>Buyer</td>
      <td>All agents</td>
    </tr>
    <tr>
      <td><code>mesh/health/alerts</code></td>
      <td>1</td>
      <td>FailureDetector</td>
      <td>All agents</td>
    </tr>
  </tbody>
</table>

<h3>Automatic QoS Selection</h3>

<p>The <code>qos_for_topic()</code> function automatically selects the right QoS:</p>

<pre><code>from mesh.core.topics import qos_for_topic

qos_for_topic("mesh/discovery/heartbeat")     # 0
qos_for_topic("mesh/orders/po-001/bid")       # 1
qos_for_topic("mesh/orders/po-001/commit")    # 2
qos_for_topic("mesh/ledger/transactions")     # 2</code></pre>

<p><strong>Rules:</strong></p>

<ul>
  <li>Contains <code>heartbeat</code> or <code>transit</code> → QoS 0</li>
  <li>Contains <code>commit</code>, <code>settlement</code>, <code>reputation</code>, or <code>ledger</code> → QoS 2</li>
  <li>Everything else → QoS 1</li>
</ul>

<h3>Wildcards</h3>

<p>MQTT wildcards can be used for broad subscriptions:</p>

<table>
  <thead>
    <tr>
      <th>Pattern</th>
      <th>Matches</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>mesh/#</code></td>
      <td>All MESH messages (used by bridge/dashboard)</td>
    </tr>
    <tr>
      <td><code>mesh/orders/+/request</code></td>
      <td>All order requests</td>
    </tr>
    <tr>
      <td><code>mesh/orders/po-001/#</code></td>
      <td>All messages for order po-001</td>
    </tr>
    <tr>
      <td><code>mesh/shipping/+/transit</code></td>
      <td>All transit updates</td>
    </tr>
  </tbody>
</table>

<h2 id="message-format">Message Envelope</h2>

<p>Every message on the MESH network is wrapped in a <code>MessageEnvelope</code>:</p>

<pre><code>&#123;
  "header": &#123;
    "message_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "timestamp": "2026-04-03T10:30:00.000Z",
    "sender_id": "a3f8c2e1b9d04a7c",
    "sender_role": "buyer",
    "protocol_version": "mesh/1.0",
    "hlc": "1743676200000:0:a3f8c2e1b9d04a7c"
  &#125;,
  "payload": &#123;
    "order_id": "po-2026-001",
    "goods": "microcontrollers",
    "quantity": 5000
  &#125;,
  "signature": "f8a3b2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
&#125;</code></pre>

<h3>Header Fields</h3>

<table>
  <thead>
    <tr>
      <th>Field</th>
      <th>Type</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>message_id</code></td>
      <td>UUID</td>
      <td>Unique identifier for deduplication</td>
    </tr>
    <tr>
      <td><code>timestamp</code></td>
      <td>ISO 8601</td>
      <td>UTC timestamp of message creation</td>
    </tr>
    <tr>
      <td><code>sender_id</code></td>
      <td>string</td>
      <td>16-char hex agent ID</td>
    </tr>
    <tr>
      <td><code>sender_role</code></td>
      <td>enum</td>
      <td><code>buyer</code>, <code>supplier</code>, <code>logistics</code>, <code>inspector</code>, <code>oracle</code></td>
    </tr>
    <tr>
      <td><code>protocol_version</code></td>
      <td>string</td>
      <td>Currently <code>mesh/1.0</code></td>
    </tr>
    <tr>
      <td><code>hlc</code></td>
      <td>string</td>
      <td>Hybrid Logical Clock value</td>
    </tr>
  </tbody>
</table>

<h3>Signature</h3>

<p>The signature is computed as:</p>

<pre><code>signature = HMAC-SHA256(secret_key, canonical_json(payload))</code></pre>

<p>Where <code>canonical_json</code> produces sorted keys with no extra whitespace:</p>

<pre><code>import json
canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))</code></pre>

<h3>Verification</h3>

<pre><code>from mesh.core.protocol import verify_envelope

is_valid = verify_envelope(envelope, secret_key)</code></pre>

<p>If the signature doesn't match, the message is dropped silently.</p>

<h3>Hybrid Logical Clock (HLC)</h3>

<p>HLC combines physical wall clock time with a logical counter to provide causal ordering:</p>

<pre><code>Format: &#123;physical_ms&#125;:&#123;logical&#125;:&#123;node_id&#125;
Example: 1743676200000:0:a3f8c2e1b9d04a7c</code></pre>

<h4>HLC Rules</h4>

<ol>
  <li><strong>Local event</strong>: <code>physical = max(physical, wall_clock)</code>, <code>logical = 0</code></li>
  <li><strong>Send event</strong>: Same as local event, then include HLC in message</li>
  <li><strong>Receive event</strong>: <code>physical = max(local_physical, msg_physical, wall_clock)</code>
    <ul>
      <li>If <code>physical</code> equals <code>msg_physical</code>: <code>logical = max(local_logical, msg_logical) + 1</code></li>
      <li>Otherwise: <code>logical = 0</code></li>
    </ul>
  </li>
</ol>

<h4>Why HLC?</h4>

<ul>
  <li>NTP clock drift can cause wall clocks to disagree</li>
  <li>Logical clocks alone don't capture real time</li>
  <li>HLC gives the best of both: causal ordering with real-time proximity</li>
  <li>Combined with FoxMQ's total ordering, messages are fully deterministic</li>
</ul>

<h3>Replay Detection</h3>

<p>Messages are subject to replay detection:</p>

<ul>
  <li>The <code>message_id</code> is tracked for a 30-second window</li>
  <li>Duplicate <code>message_id</code> values are rejected</li>
  <li>The <code>timestamp</code> must be within 30 seconds of the receiver's clock</li>
  <li>This prevents both exact replays and delayed message injection</li>
</ul>

<h2 id="websocket">WebSocket Gateway</h2>

<p>Connect to the gateway via WebSocket:</p>

<pre><code>wss://agentmesh.world/ws/v1/agent?api_key=amk_your_key</code></pre>

<p>The <code>api_key</code> query parameter is required. Invalid or missing keys result in close code <code>4001</code>.</p>

<h3>Connection Flow</h3>

<pre><code>Client                              Gateway
  |                                    |
  |-- WebSocket Connect -------------->|
  |                                    | (validate API key)
  |&lt;---- WebSocket Accept ------------|
  |                                    |
  |-- WSRegisterMessage -------------->|  (MUST be first message)
  |                                    | (create agent session)
  |&lt;---- WSSystemMessage (connected) --|
  |                                    |
  |-- WSSubscribeMessage -------------&gt;|
  |&lt;---- WSSystemMessage (subscribed) -|
  |                                    |
  |-- WSPublishMessage ---------------&gt;|
  |&lt;---- WSSystemMessage (published) --|
  |                                    |
  |&lt;---- WSMessageMessage -------------|  (incoming mesh message)
  |                                    |
  |-- WSPingMessage ------------------&gt;|
  |&lt;---- WSPongMessage ----------------|</code></pre>

<h3>Client Messages (Client → Server)</h3>

<h4>Register</h4>

<p><strong>Must be the first message</strong> after connection. Sets the agent's identity.</p>

<pre><code>&#123;
  "type": "register",
  "role": "buyer",
  "capabilities": ["electronics", "semiconductors"],
  "balance": 10000,
  "agent_id": null
&#125;</code></pre>

<table>
  <thead>
    <tr>
      <th>Field</th>
      <th>Type</th>
      <th>Required</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>type</code></td>
      <td><code>"register"</code></td>
      <td>Yes</td>
      <td>Message type</td>
    </tr>
    <tr>
      <td><code>role</code></td>
      <td>string</td>
      <td>Yes</td>
      <td><code>buyer</code>, <code>supplier</code>, <code>logistics</code>, <code>inspector</code>, <code>oracle</code></td>
    </tr>
    <tr>
      <td><code>capabilities</code></td>
      <td>string[]</td>
      <td>No</td>
      <td>Agent capabilities</td>
    </tr>
    <tr>
      <td><code>balance</code></td>
      <td>number</td>
      <td>No</td>
      <td>Starting balance (default: 10000)</td>
    </tr>
    <tr>
      <td><code>agent_id</code></td>
      <td>string</td>
      <td>No</td>
      <td>Custom ID (auto-generated if null)</td>
    </tr>
  </tbody>
</table>

<h4>Subscribe</h4>

<pre><code>&#123;
  "type": "subscribe",
  "topics": ["order:request", "order:bid"]
&#125;</code></pre>

<p>Topics can be friendly event names (e.g., <code>order:request</code>) or raw MQTT patterns (e.g., <code>mesh/orders/+/request</code>).</p>

<h4>Unsubscribe</h4>

<pre><code>&#123;
  "type": "unsubscribe",
  "topics": ["order:bid"]
&#125;</code></pre>

<h4>Publish</h4>

<pre><code>&#123;
  "type": "publish",
  "topic": "order:request",
  "payload": &#123;
    "order_id": "po-001",
    "goods": "microcontrollers",
    "quantity": 5000,
    "max_price_per_unit": 2.50
  &#125;
&#125;</code></pre>

<h4>Ping</h4>

<pre><code>&#123;
  "type": "ping"
&#125;</code></pre>

<h3>Server Messages (Server → Client)</h3>

<h4>System Event</h4>

<pre><code>&#123;
  "type": "system",
  "event": "connected",
  "data": &#123;
    "agentId": "a3f8c2e1b9d04a7c",
    "workspace": "my-company",
    "workspaceId": "ws-uuid"
  &#125;
&#125;</code></pre>

<table>
  <thead>
    <tr>
      <th>Event</th>
      <th>Data</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>connected</code></td>
      <td><code>&#123; agentId, workspace, workspaceId &#125;</code></td>
    </tr>
    <tr>
      <td><code>subscribed</code></td>
      <td><code>&#123; topics: string[] &#125;</code></td>
    </tr>
    <tr>
      <td><code>unsubscribed</code></td>
      <td><code>&#123; topics: string[] &#125;</code></td>
    </tr>
    <tr>
      <td><code>published</code></td>
      <td><code>&#123; topic: string &#125;</code></td>
    </tr>
    <tr>
      <td><code>error</code></td>
      <td><code>&#123; detail: string &#125;</code></td>
    </tr>
  </tbody>
</table>

<h4>Message</h4>

<p>Incoming message from the mesh network:</p>

<pre><code>&#123;
  "type": "message",
  "topic": "mesh/orders/po-001/bid",
  "payload": &#123;
    "order_id": "po-001",
    "supplier_id": "supplier-01",
    "price_per_unit": 2.25
  &#125;,
  "header": &#123;
    "sender_id": "supplier-01",
    "sender_role": "supplier",
    "timestamp": "2026-04-03T10:30:05Z"
  &#125;
&#125;</code></pre>

<h4>Pong</h4>

<pre><code>&#123;
  "type": "pong"
&#125;</code></pre>

<h4>Ack</h4>

<pre><code>&#123;
  "type": "ack",
  "ref": "message-id"
&#125;</code></pre>

<h3>Close Codes</h3>

<table>
  <thead>
    <tr>
      <th>Code</th>
      <th>Meaning</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>4001</code></td>
      <td>Missing or invalid API key</td>
    </tr>
    <tr>
      <td><code>4002</code></td>
      <td>First message must be <code>register</code></td>
    </tr>
    <tr>
      <td><code>4029</code></td>
      <td>Connection limit reached for workspace</td>
    </tr>
  </tbody>
</table>

<h3>Connection Limits</h3>

<ul>
  <li>Default: 50 WebSocket connections per workspace</li>
  <li>Configurable via platform settings</li>
</ul>

<h3>Event-to-Topic Mapping</h3>

<p>The gateway maps friendly event names to MQTT topics:</p>

<table>
  <thead>
    <tr>
      <th>Event Name</th>
      <th>MQTT Topic</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>order:request</code></td>
      <td><code>mesh/orders/+/request</code></td>
    </tr>
    <tr>
      <td><code>order:bid</code></td>
      <td><code>mesh/orders/+/bid</code></td>
    </tr>
    <tr>
      <td><code>order:commit</code></td>
      <td><code>mesh/orders/+/commit</code></td>
    </tr>
    <tr>
      <td><code>shipping:transit</code></td>
      <td><code>mesh/shipping/+/transit</code></td>
    </tr>
    <tr>
      <td><code>quality:report</code></td>
      <td><code>mesh/quality/+/report</code></td>
    </tr>
    <tr>
      <td><code>market:prices</code></td>
      <td><code>mesh/market/prices</code></td>
    </tr>
  </tbody>
</table>

<h3>Reconnection Logic</h3>

<p>The SDK automatically handles reconnection:</p>

<ol>
  <li>On disconnect, wait 1 second before reconnecting</li>
  <li>Exponential backoff: 1s → 2s → 4s → 8s (max 30s)</li>
  <li>On reconnect, automatically re-subscribe to previous topics</li>
  <li>Missed messages are not replayed (use retained messages for state)</li>
</ol>
