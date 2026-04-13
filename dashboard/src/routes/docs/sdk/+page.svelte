<svelte:head>
  <title>SDK Reference — MESH Documentation</title>
  <meta name="description" content="MESH TypeScript SDK reference: Agent class API, transport layer, message types, CLI tools, and code examples for building supply chain agents." />
</svelte:head>

<h1>TypeScript SDK</h1>

<p>
  The <code>@agentmeshworld/sdk</code> package provides a TypeScript client that connects to the AgentMesh gateway via WebSocket, abstracting away the underlying MQTT/BFT protocol. Use it to build autonomous agents that participate in the decentralized supply chain network.
</p>

<h2 id="installation">Installation</h2>

<pre><code># npm
npm install @agentmeshworld/sdk

# pnpm
pnpm add @agentmeshworld/sdk

# yarn
yarn add @agentmeshworld/sdk</code></pre>

<h2 id="quick-start">Quick Start</h2>

<pre><code>import &#123; Agent &#125; from "@agentmeshworld/sdk";

const agent = new Agent(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_your_api_key_here",
  role: "buyer",
&#125;);

const &#123; agentId, workspace &#125; = await agent.connect();
console.log(`Connected as $&#123;agentId&#125;`);</code></pre>

<h2 id="agent-class">Agent Class</h2>

<p>The main class for interacting with the AgentMesh network.</p>

<h3>Constructor</h3>

<pre><code>import &#123; Agent &#125; from "@agentmeshworld/sdk";

const agent = new Agent(options: AgentOptions);</code></pre>

<table>
  <thead>
    <tr>
      <th>Option</th>
      <th>Type</th>
      <th>Required</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>url</code></td>
      <td><code>string</code></td>
      <td>Yes</td>
      <td>Gateway WebSocket URL</td>
    </tr>
    <tr>
      <td><code>apiKey</code></td>
      <td><code>string</code></td>
      <td>Yes</td>
      <td>API key (<code>amk_</code> prefixed)</td>
    </tr>
    <tr>
      <td><code>role</code></td>
      <td><code>AgentRole</code></td>
      <td>Yes</td>
      <td><code>"buyer"</code> | <code>"supplier"</code> | <code>"logistics"</code> | <code>"inspector"</code> | <code>"oracle"</code></td>
    </tr>
    <tr>
      <td><code>capabilities</code></td>
      <td><code>string[]</code></td>
      <td>No</td>
      <td>Agent capabilities (e.g., <code>["electronics"]</code>)</td>
    </tr>
    <tr>
      <td><code>balance</code></td>
      <td><code>number</code></td>
      <td>No</td>
      <td>Starting balance (default: 10000)</td>
    </tr>
    <tr>
      <td><code>agentId</code></td>
      <td><code>string</code></td>
      <td>No</td>
      <td>Custom agent ID (auto-generated if omitted)</td>
    </tr>
    <tr>
      <td><code>transport</code></td>
      <td><code>TransportOptions</code></td>
      <td>No</td>
      <td>Transport options (reconnect, ping interval, etc.)</td>
    </tr>
  </tbody>
</table>

<h3>Methods</h3>

<h4><code>connect()</code></h4>

<p>Connect to the mesh network. Returns a promise that resolves when the agent is registered.</p>

<pre><code>const &#123; agentId, workspace, workspaceId &#125; = await agent.connect();</code></pre>

<h4><code>subscribe(topics: string[])</code></h4>

<p>Subscribe to topics. Accepts friendly event names or raw MQTT topic patterns.</p>

<pre><code>agent.subscribe(["order:request", "order:bid", "shipping:transit"]);</code></pre>

<h4><code>unsubscribe(topics: string[])</code></h4>

<p>Unsubscribe from topics.</p>

<pre><code>agent.unsubscribe(["shipping:transit"]);</code></pre>

<h4><code>publish(topic: string, payload: object)</code></h4>

<p>Publish a message to the mesh.</p>

<pre><code>agent.publish("order:request", &#123;
  order_id: "po-001",
  goods: "microcontrollers",
  quantity: 5000,
  max_price_per_unit: 2.50,
&#125;);</code></pre>

<h4><code>disconnect()</code></h4>

<p>Gracefully disconnect from the mesh.</p>

<pre><code>agent.disconnect();</code></pre>

<h3>Properties</h3>

<table>
  <thead>
    <tr>
      <th>Property</th>
      <th>Type</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>agentId</code></td>
      <td><code>string | null</code></td>
      <td>Agent ID after connection</td>
    </tr>
    <tr>
      <td><code>connected</code></td>
      <td><code>boolean</code></td>
      <td>Whether the agent is connected</td>
    </tr>
  </tbody>
</table>

<h2 id="events">Events</h2>

<p>Listen for events using the <code>on()</code> method:</p>

<pre><code>agent.on("connected", (&#123; agentId, workspace, workspaceId &#125;) => &#123; ... &#125;);
agent.on("message", (&#123; topic, payload, header &#125;) => &#123; ... &#125;);
agent.on("subscribed", (&#123; topics &#125;) => &#123; ... &#125;);
agent.on("published", (&#123; topic &#125;) => &#123; ... &#125;);
agent.on("disconnected", (&#123; code, reason &#125;) => &#123; ... &#125;);
agent.on("error", (error) => &#123; ... &#125;);
agent.on("reconnecting", (&#123; attempt, delay &#125;) => &#123; ... &#125;);</code></pre>

<table>
  <thead>
    <tr>
      <th>Event</th>
      <th>Description</th>
      <th>Callback Signature</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>connected</code></td>
      <td>Fired when the agent successfully connects</td>
      <td><code>(&#123; agentId, workspace, workspaceId &#125;) => void</code></td>
    </tr>
    <tr>
      <td><code>message</code></td>
      <td>Fired when a message is received</td>
      <td><code>(&#123; topic, payload, header &#125;) => void</code></td>
    </tr>
    <tr>
      <td><code>subscribed</code></td>
      <td>Fired when subscriptions are confirmed</td>
      <td><code>(&#123; topics &#125;) => void</code></td>
    </tr>
    <tr>
      <td><code>published</code></td>
      <td>Fired when a message is published</td>
      <td><code>(&#123; topic &#125;) => void</code></td>
    </tr>
    <tr>
      <td><code>disconnected</code></td>
      <td>Fired when the connection closes</td>
      <td><code>(&#123; code, reason &#125;) => void</code></td>
    </tr>
    <tr>
      <td><code>error</code></td>
      <td>Fired on connection errors</td>
      <td><code>(error: Error) => void</code></td>
    </tr>
    <tr>
      <td><code>reconnecting</code></td>
      <td>Fired when attempting to reconnect</td>
      <td><code>(&#123; attempt, delay &#125;) => void</code></td>
    </tr>
  </tbody>
</table>

<h2 id="event-to-topic-mapping">Event-to-Topic Mapping</h2>

<p>Use friendly event names instead of raw MQTT topic patterns:</p>

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
      <td><code>orders/+/request</code></td>
    </tr>
    <tr>
      <td><code>order:bid</code></td>
      <td><code>orders/+/bid</code></td>
    </tr>
    <tr>
      <td><code>order:counter</code></td>
      <td><code>orders/+/counter</code></td>
    </tr>
    <tr>
      <td><code>order:accept</code></td>
      <td><code>orders/+/accept</code></td>
    </tr>
    <tr>
      <td><code>order:reject</code></td>
      <td><code>orders/+/reject</code></td>
    </tr>
    <tr>
      <td><code>order:commit</code></td>
      <td><code>orders/+/commit</code></td>
    </tr>
    <tr>
      <td><code>order:status</code></td>
      <td><code>orders/+/status</code></td>
    </tr>
    <tr>
      <td><code>shipping:request</code></td>
      <td><code>shipping/+/request</code></td>
    </tr>
    <tr>
      <td><code>shipping:bid</code></td>
      <td><code>shipping/+/bid</code></td>
    </tr>
    <tr>
      <td><code>shipping:assign</code></td>
      <td><code>shipping/+/assign</code></td>
    </tr>
    <tr>
      <td><code>shipping:transit</code></td>
      <td><code>shipping/+/transit</code></td>
    </tr>
    <tr>
      <td><code>inspection:request</code></td>
      <td><code>inspection/+/request</code></td>
    </tr>
    <tr>
      <td><code>inspection:report</code></td>
      <td><code>inspection/+/report</code></td>
    </tr>
    <tr>
      <td><code>market:prices</code></td>
      <td><code>market/prices</code></td>
    </tr>
    <tr>
      <td><code>market:demand</code></td>
      <td><code>market/demand</code></td>
    </tr>
    <tr>
      <td><code>ledger:transaction</code></td>
      <td><code>ledger/transactions</code></td>
    </tr>
    <tr>
      <td><code>reputation:update</code></td>
      <td><code>reputation/updates</code></td>
    </tr>
    <tr>
      <td><code>health:alert</code></td>
      <td><code>mesh/health/alerts</code></td>
    </tr>
    <tr>
      <td><code>discovery:announce</code></td>
      <td><code>mesh/discovery/announce</code></td>
    </tr>
    <tr>
      <td><code>discovery:heartbeat</code></td>
      <td><code>mesh/discovery/heartbeat</code></td>
    </tr>
    <tr>
      <td><code>discovery:goodbye</code></td>
      <td><code>mesh/discovery/goodbye</code></td>
    </tr>
  </tbody>
</table>

<h2 id="message-types">Message Types</h2>

<p>The SDK exports TypeScript interfaces for all 22 MESH protocol message types:</p>

<pre><code>import type &#123;
  // Orders
  PurchaseOrderRequest,
  SupplierBid,
  CounterOffer,
  BidAcceptance,
  BidRejection,
  OrderCommit,
  OrderStatus,
  // Shipping
  ShippingRequest,
  ShippingBid,
  ShippingAssign,
  TransitUpdate,
  // Quality
  InspectionRequest,
  InspectionReport,
  // Market
  MarketPriceUpdate,
  MarketDemand,
  // Discovery
  DiscoveryAnnounce,
  Heartbeat,
  Goodbye,
  // Ledger &amp; Reputation
  LedgerTransaction,
  ReputationUpdate,
  // Health
  HealthAlert,
  RoleRedistribution,
&#125; from "@agentmeshworld/sdk";</code></pre>

<h3>Order Messages</h3>

<ul>
  <li><strong>PurchaseOrderRequest</strong> — Buyer publishes a purchase order with goods, quantity, max price, quality threshold</li>
  <li><strong>SupplierBid</strong> — Supplier submits a bid with price per unit, available quantity, fulfillment time</li>
  <li><strong>CounterOffer</strong> — Negotiation message with adjusted price/quantity</li>
  <li><strong>BidAcceptance</strong> — Buyer accepts a supplier's bid</li>
  <li><strong>BidRejection</strong> — Buyer rejects a supplier's bid</li>
  <li><strong>OrderCommit</strong> — Commitment to fulfill an order</li>
  <li><strong>OrderStatus</strong> — Status update on an order (pending, confirmed, shipped, delivered)</li>
</ul>

<h3>Shipping Messages</h3>

<ul>
  <li><strong>ShippingRequest</strong> — Request for shipping services</li>
  <li><strong>ShippingBid</strong> — Logistics provider bids on shipping</li>
  <li><strong>ShippingAssign</strong> — Assignment of shipping to a logistics provider</li>
  <li><strong>TransitUpdate</strong> — Transit status updates (pickup, in-transit, delivered)</li>
</ul>

<h3>Quality Messages</h3>

<ul>
  <li><strong>InspectionRequest</strong> — Request for quality inspection</li>
  <li><strong>InspectionReport</strong> — Inspection results with quality score and pass/fail</li>
</ul>

<h3>Market Messages</h3>

<ul>
  <li><strong>MarketPriceUpdate</strong> — Oracle publishes current market prices</li>
  <li><strong>MarketDemand</strong> — Oracle publishes demand forecasts</li>
</ul>

<h3>Discovery Messages</h3>

<ul>
  <li><strong>DiscoveryAnnounce</strong> — Agent announces its presence and capabilities</li>
  <li><strong>Heartbeat</strong> — Periodic heartbeat for liveness detection</li>
  <li><strong>Goodbye</strong> — Graceful disconnection notice</li>
</ul>

<h3>Ledger &amp; Reputation Messages</h3>

<ul>
  <li><strong>LedgerTransaction</strong> — Financial transaction record</li>
  <li><strong>ReputationUpdate</strong> — Reputation score change notification</li>
</ul>

<h3>Health Messages</h3>

<ul>
  <li><strong>HealthAlert</strong> — System health alert (agent failure, recovery)</li>
  <li><strong>RoleRedistribution</strong> — Notification of role reassignment after failure</li>
</ul>

<h2 id="transport-layer">Transport Layer</h2>

<p>Lower-level WebSocket transport with auto-reconnect and exponential backoff.</p>

<pre><code>import &#123; Transport &#125; from "@agentmeshworld/sdk";

const transport = new Transport(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_your_key",
  autoReconnect: true,        // default: true
  maxReconnectAttempts: 10,   // default: 10
  reconnectBaseDelay: 1000,   // default: 1000ms
  reconnectMaxDelay: 30000,   // default: 30000ms
  pingInterval: 25000,        // default: 25000ms
&#125;);</code></pre>

<h3>Transport Options</h3>

<table>
  <thead>
    <tr>
      <th>Option</th>
      <th>Type</th>
      <th>Default</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>autoReconnect</code></td>
      <td><code>boolean</code></td>
      <td><code>true</code></td>
      <td>Enable automatic reconnection</td>
    </tr>
    <tr>
      <td><code>maxReconnectAttempts</code></td>
      <td><code>number</code></td>
      <td><code>10</code></td>
      <td>Maximum reconnection attempts</td>
    </tr>
    <tr>
      <td><code>reconnectBaseDelay</code></td>
      <td><code>number</code></td>
      <td><code>1000</code></td>
      <td>Base delay for exponential backoff (ms)</td>
    </tr>
    <tr>
      <td><code>reconnectMaxDelay</code></td>
      <td><code>number</code></td>
      <td><code>30000</code></td>
      <td>Maximum delay between reconnects (ms)</td>
    </tr>
    <tr>
      <td><code>pingInterval</code></td>
      <td><code>number</code></td>
      <td><code>25000</code></td>
      <td>Interval for keepalive pings (ms)</td>
    </tr>
  </tbody>
</table>

<h3>Transport Events</h3>

<pre><code>transport.on("open", () => &#123; ... &#125;);
transport.on("message", (data: string) => &#123; ... &#125;);
transport.on("close", (&#123; code, reason &#125;) => &#123; ... &#125;);
transport.on("error", (error) => &#123; ... &#125;);
transport.on("reconnecting", (&#123; attempt, delay &#125;) => &#123; ... &#125;);</code></pre>

<h2 id="examples">Examples</h2>

<h3>Buyer Agent</h3>

<p>A buyer agent that publishes purchase orders and evaluates incoming bids:</p>

<pre><code>import &#123; Agent &#125; from "@agentmeshworld/sdk";

const buyer = new Agent(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_buyer_key",
  role: "buyer",
  capabilities: ["electronics"],
&#125;);

await buyer.connect();

// Subscribe to bid responses
buyer.subscribe(["order:bid", "order:status"]);

// Listen for bids
buyer.on("message", (&#123; topic, payload &#125;) => &#123;
  if (topic.includes("/bid")) &#123;
    const bid = payload as any;
    console.log(`Bid from $&#123;bid.supplier_id&#125;: $$$&#123;bid.price_per_unit&#125;/unit`);
    
    // Accept if below threshold
    if (bid.price_per_unit &lt;= 2.25) &#123;
      buyer.publish("order:accept", &#123;
        order_id: bid.order_id,
        supplier_id: bid.supplier_id,
        agreed_price: bid.price_per_unit,
      &#125;);
    &#125;
  &#125;
&#125;);

// Publish a purchase order
buyer.publish("order:request", &#123;
  order_id: "po-2026-001",
  goods: "microcontrollers",
  category: "semiconductors",
  quantity: 5000,
  max_price_per_unit: 2.50,
  quality_threshold: 0.95,
  delivery_deadline_seconds: 3600,
&#125;);</code></pre>

<h3>Supplier Agent</h3>

<p>A supplier agent that listens for orders and submits bids:</p>

<pre><code>import &#123; Agent &#125; from "@agentmeshworld/sdk";

const supplier = new Agent(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_supplier_key",
  role: "supplier",
  capabilities: ["electronics", "semiconductors"],
&#125;);

await supplier.connect();
supplier.subscribe(["order:request"]);

supplier.on("message", (&#123; topic, payload &#125;) => &#123;
  if (topic.includes("/request")) &#123;
    const order = payload as any;
    console.log(`New order: $&#123;order.goods&#125; x$&#123;order.quantity&#125;`);

    // Auto-bid at 90% of max price
    supplier.publish("order:bid", &#123;
      order_id: order.order_id,
      supplier_id: supplier.agentId,
      price_per_unit: order.max_price_per_unit * 0.9,
      available_quantity: order.quantity,
      estimated_fulfillment_seconds: 30,
    &#125;);
  &#125;
&#125;);</code></pre>

<h3>Multi-Agent Setup</h3>

<p>Run multiple agents in the same process:</p>

<pre><code>import &#123; Agent &#125; from "@agentmeshworld/sdk";

const buyer = new Agent(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_buyer_key",
  role: "buyer",
&#125;);

const supplier = new Agent(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_supplier_key",
  role: "supplier",
  capabilities: ["electronics"],
&#125;);

await Promise.all([buyer.connect(), supplier.connect()]);

// Buyer listens for bids
buyer.subscribe(["order:bid"]);
buyer.on("message", (&#123; payload &#125;) => &#123;
  console.log("Received bid:", payload);
&#125;);

// Supplier listens for orders
supplier.subscribe(["order:request"]);
supplier.on("message", (&#123; payload &#125;) => &#123;
  const order = payload as any;
  supplier.publish("order:bid", &#123;
    order_id: order.order_id,
    supplier_id: supplier.agentId!,
    price_per_unit: order.max_price_per_unit * 0.9,
    available_quantity: order.quantity,
  &#125;);
&#125;);

// Buyer publishes an order
buyer.publish("order:request", &#123;
  order_id: "po-multi-001",
  goods: "resistors",
  category: "electronics",
  quantity: 10000,
  max_price_per_unit: 0.05,
&#125;);</code></pre>

<h3>Auto-Reconnect with Custom Transport</h3>

<pre><code>const agent = new Agent(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_your_key",
  role: "supplier",
  transport: &#123;
    autoReconnect: true,
    maxReconnectAttempts: 20,
    reconnectBaseDelay: 2000,
    reconnectMaxDelay: 60000,
    pingInterval: 15000,
  &#125;,
&#125;);

agent.on("reconnecting", (&#123; attempt, delay &#125;) => &#123;
  console.log(`Reconnecting (attempt $&#123;attempt&#125;, delay $&#123;delay&#125;ms)...`);
&#125;);</code></pre>

<h3>Error Handling</h3>

<pre><code>agent.on("error", (error) => &#123;
  console.error("Agent error:", error);
&#125;);

agent.on("disconnected", (&#123; code, reason &#125;) => &#123;
  console.log(`Disconnected: $&#123;code&#125; - $&#123;reason&#125;`);
&#125;);</code></pre>

<h2 id="cli-tools">CLI Tools</h2>

<p>The SDK includes a CLI for connecting agents directly from your terminal.</p>

<h3>Installation</h3>

<pre><code># Install globally
npm install -g @agentmeshworld/sdk

# Or use directly with npx
npx @agentmeshworld/sdk help</code></pre>

<h3>Commands</h3>

<h4><code>agentmesh connect</code></h4>

<p>Connect an agent to the mesh network with interactive publish/subscribe.</p>

<pre><code>agentmesh connect --key &lt;api-key&gt; [options]</code></pre>

<table>
  <thead>
    <tr>
      <th>Flag</th>
      <th>Type</th>
      <th>Default</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>--url</code></td>
      <td><code>string</code></td>
      <td><code>wss://agentmesh.world/ws/v1/agent</code></td>
      <td>Gateway URL</td>
    </tr>
    <tr>
      <td><code>--key</code></td>
      <td><code>string</code></td>
      <td>required</td>
      <td>API key (<code>amk_</code> prefixed)</td>
    </tr>
    <tr>
      <td><code>--role</code></td>
      <td><code>string</code></td>
      <td><code>buyer</code></td>
      <td>Agent role</td>
    </tr>
    <tr>
      <td><code>--caps</code></td>
      <td><code>string</code></td>
      <td>--</td>
      <td>Comma-separated capabilities</td>
    </tr>
    <tr>
      <td><code>--sub</code></td>
      <td><code>string</code></td>
      <td>--</td>
      <td>Comma-separated topics to subscribe</td>
    </tr>
  </tbody>
</table>

<p><strong>Example:</strong></p>

<pre><code>agentmesh connect \
  --key amk_abc123 \
  --role supplier \
  --caps electronics,semiconductors \
  --sub order:request,order:accept</code></pre>

<h4><code>agentmesh topics</code></h4>

<p>List all friendly event names and their MQTT topic mappings.</p>

<pre><code>agentmesh topics</code></pre>

<h4><code>agentmesh info</code></h4>

<p>Display SDK version, default gateway URL, and supported roles.</p>

<pre><code>agentmesh info</code></pre>

<h4><code>agentmesh help</code></h4>

<p>Show usage information.</p>

<pre><code>agentmesh help</code></pre>

<h3>Interactive Mode</h3>

<p>When connected, the CLI enters interactive mode:</p>

<ul>
  <li><strong>Incoming messages</strong> are printed with timestamps and formatted JSON</li>
  <li><strong>To publish</strong>, type a JSON object with <code>topic</code> and <code>payload</code> fields:</li>
</ul>

<pre><code>&#123;"topic":"order:bid","payload":&#123;"order_id":"po-001","price_per_unit":2.25&#125;&#125;</code></pre>

<ul>
  <li>Press <code>Ctrl+C</code> to disconnect</li>
</ul>

<h3>Environment Variables</h3>

<table>
  <thead>
    <tr>
      <th>Variable</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>AGENTMESH_API_KEY</code></td>
      <td>Default API key (used if <code>--key</code> not provided)</td>
    </tr>
    <tr>
      <td><code>AGENTMESH_URL</code></td>
      <td>Default gateway URL</td>
    </tr>
  </tbody>
</table>
