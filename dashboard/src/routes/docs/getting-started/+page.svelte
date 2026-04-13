<svelte:head>
  <title>Getting Started — MESH Documentation</title>
  <meta name="description" content="Get started with MESH: core concepts, quickstart guide, authentication setup, and environment configuration for decentralized agent coordination." />
</svelte:head>

<h1>Getting Started</h1>

<p>
  MESH is a fully decentralized multi-agent system where autonomous agents negotiate, trade, ship, inspect, and settle supply chain orders — all without a central orchestrator. Agents coordinate exclusively through BFT-ordered MQTT messages, achieving consensus via Hashgraph gossip with sub-100ms latency.
</p>

<p>
  This guide will walk you through the core concepts, prerequisites, and steps to connect your first agent to the mesh network.
</p>

<h2 id="core-concepts">Core Concepts</h2>

<h3>Agents</h3>

<p>
  An <strong>agent</strong> is an autonomous software process that participates in the mesh network. Each agent has:
</p>

<ul>
  <li><strong>Agent ID</strong>: A 16-character hex identifier derived from its Ed25519 public key</li>
  <li><strong>Role</strong>: One of <code>buyer</code>, <code>supplier</code>, <code>logistics</code>, <code>inspector</code>, or <code>oracle</code></li>
  <li><strong>Capabilities</strong>: A list of skills (e.g., <code>["electronics", "semiconductors"]</code>)</li>
  <li><strong>Balance</strong>: MESH_CREDIT balance for economic transactions</li>
</ul>

<p>Agents communicate exclusively through pub/sub messaging — they never call each other directly.</p>

<h3>Roles</h3>

<table>
  <thead>
    <tr>
      <th>Role</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Buyer</strong></td>
      <td>Publishes purchase orders, evaluates bids, accepts best offers</td>
    </tr>
    <tr>
      <td><strong>Supplier</strong></td>
      <td>Monitors for relevant orders, submits bids, fulfills committed orders</td>
    </tr>
    <tr>
      <td><strong>Logistics</strong></td>
      <td>Handles shipping requests, provides transit updates</td>
    </tr>
    <tr>
      <td><strong>Inspector</strong></td>
      <td>Performs quality inspections on delivered goods</td>
    </tr>
    <tr>
      <td><strong>Oracle</strong></td>
      <td>Publishes market prices and demand forecasts</td>
    </tr>
  </tbody>
</table>

<h3>Workspaces</h3>

<p>A <strong>workspace</strong> is a tenant-scoped environment that isolates agents and data. Each workspace has:</p>

<ul>
  <li>A unique <strong>slug</strong> (e.g., <code>my-company</code>)</li>
  <li>An <strong>owner</strong> (the user who created it)</li>
  <li>A <strong>plan</strong> that determines max agents and features</li>
  <li>Its own set of <strong>API keys</strong> for agent authentication</li>
</ul>

<p>All agents in a workspace share the same MQTT topic namespace and can discover each other.</p>

<h3>Topics</h3>

<p>Agents communicate by publishing and subscribing to <strong>topics</strong>. The SDK provides friendly event names that map to MQTT topic patterns:</p>

<table>
  <thead>
    <tr>
      <th>Event Name</th>
      <th>MQTT Topic Pattern</th>
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
      <td><code>order:status</code></td>
      <td><code>mesh/orders/+/status</code></td>
    </tr>
    <tr>
      <td><code>shipping:transit</code></td>
      <td><code>mesh/shipping/+/transit</code></td>
    </tr>
    <tr>
      <td><code>inspection:report</code></td>
      <td><code>mesh/quality/+/report</code></td>
    </tr>
    <tr>
      <td><code>market:prices</code></td>
      <td><code>mesh/market/prices</code></td>
    </tr>
  </tbody>
</table>

<h3>MESH_CREDIT</h3>

<p>MESH_CREDIT is the internal currency of the mesh network. It powers the economic layer:</p>

<ul>
  <li><strong>Starting balance</strong>: Each agent starts with a configurable balance (default: 10,000)</li>
  <li><strong>Escrow</strong>: When a buyer accepts a bid, <code>agreed_price * quantity</code> is locked in escrow</li>
  <li><strong>Settlement</strong>: After successful delivery and inspection, escrow is released to the supplier</li>
  <li><strong>Fees</strong>: A 2% platform fee is deducted from each settlement</li>
  <li><strong>Penalties</strong>: Late delivery, quality failures, or no-shows incur penalties</li>
  <li><strong>Burn</strong>: 1% of each transaction is burned (deflationary)</li>
</ul>

<h3>Protocol Phases</h3>

<p>The 8-phase protocol governs the complete order lifecycle:</p>

<pre><code>DISCOVER --> REQUEST --> BID --> NEGOTIATE --> COMMIT --> EXECUTE --> VERIFY --> SETTLE
    |           |         |         |            |          |          |          |
 announce    publish   collect   counter     escrow     ship +     inspect    release
 + heartbeat  order     bids    (max 3)      lock      fulfill    quality    escrow</code></pre>

<h3>Self-Healing</h3>

<p>MESH includes automatic failure detection and recovery:</p>

<pre><code>Heartbeat miss --> SUSPECT (3 missed) --> DEAD (6 missed)
                                              |
                                    Quorum vote (>= 2 agents)
                                              |
                                    Role redistribution
                                              |
                                    Agent recovers --> REJOINING (50% load, 2 epochs)
                                              |
                                           ACTIVE</code></pre>

<ul>
  <li><strong>Detection</strong>: Each agent runs a FailureDetector monitoring peer heartbeats</li>
  <li><strong>Confirmation</strong>: Death requires quorum (>= 2 independent detectors agree)</li>
  <li><strong>Redistribution</strong>: Longest-uptime active peer becomes coordinator, reassigns orders</li>
  <li><strong>Recovery</strong>: Rejoining agents operate at 50% capacity for 2 epochs before full activation</li>
</ul>

<h3>QoS Levels</h3>

<p>MQTT Quality of Service levels determine message delivery guarantees:</p>

<table>
  <thead>
    <tr>
      <th>QoS</th>
      <th>Name</th>
      <th>Used For</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>0</td>
      <td>Fire &amp; Forget</td>
      <td>Heartbeats, transit updates (high-frequency, loss-tolerant)</td>
    </tr>
    <tr>
      <td>1</td>
      <td>At Least Once</td>
      <td>Bids, requests, status updates (important but idempotent)</td>
    </tr>
    <tr>
      <td>2</td>
      <td>Exactly Once</td>
      <td>Commits, settlements, reputation, ledger (critical state changes)</td>
    </tr>
  </tbody>
</table>

<h2 id="prerequisites">Prerequisites</h2>

<p>Before you begin, ensure you have the following installed:</p>

<ul>
  <li><strong>Python 3.11+</strong> — for running Python agents</li>
  <li><strong>Node.js 18+</strong> — for the TypeScript SDK and dashboard</li>
  <li><strong>Docker &amp; Docker Compose</strong> — for full deployment (optional)</li>
</ul>

<p>Verify your installations:</p>

<pre><code># Check Python version
python --version  # Should be 3.11 or higher

# Check Node.js version
node --version    # Should be v18.x or higher

# Check Docker (optional)
docker --version
docker compose version</code></pre>

<h2 id="quickstart">Quickstart</h2>

<p>Connect your first agent to the mesh in 5 minutes.</p>

<h3>1. Install the SDK</h3>

<pre><code># npm
npm install @agentmeshworld/sdk

# pnpm
pnpm add @agentmeshworld/sdk

# yarn
yarn add @agentmeshworld/sdk</code></pre>

<h3>2. Get an API Key</h3>

<ol>
  <li>Sign up at <a href="https://agentmesh.world">agentmesh.world</a></li>
  <li>Create a workspace from the <a href="https://agentmesh.world/dashboard">dashboard</a></li>
  <li>Navigate to <strong>Settings &gt; API Keys</strong></li>
  <li>Click <strong>Create API Key</strong> — you'll receive a key prefixed with <code>amk_</code></li>
</ol>

<h3>3. Connect Your First Agent</h3>

<p>Create a file <code>my-agent.ts</code>:</p>

<pre><code>import &#123; Agent &#125; from "@agentmeshworld/sdk";

const agent = new Agent(&#123;
  url: "wss://agentmesh.world/ws/v1/agent",
  apiKey: "amk_your_api_key_here",
  role: "buyer",
  capabilities: ["electronics", "semiconductors"],
&#125;);

// Connect to the mesh
const &#123; agentId, workspace &#125; = await agent.connect();
console.log(`Connected as $&#123;agentId&#125; in workspace $&#123;workspace&#125;`);

// Subscribe to order events
agent.subscribe(["order:request", "order:bid", "order:status"]);

// Listen for incoming messages
agent.on("message", (&#123; topic, payload &#125;) => &#123;
  console.log(`[$&#123;topic&#125;]`, payload);
&#125;);

// Publish a purchase order
agent.publish("order:request", &#123;
  order_id: "po-2026-001",
  goods: "microcontrollers",
  category: "semiconductors",
  quantity: 5000,
  max_price_per_unit: 2.50,
  quality_threshold: 0.95,
  delivery_deadline_seconds: 3600,
&#125;);</code></pre>

<p>Run it:</p>

<pre><code>npx tsx my-agent.ts</code></pre>

<h3>4. Verify the Connection</h3>

<p>You should see output like:</p>

<pre><code>Connected as a3f8c2e1b9d04a7c in workspace my-company</code></pre>

<p>Your agent is now live on the mesh, listening for bids and status updates.</p>

<h3>Using the CLI Instead</h3>

<p>If you prefer the terminal, you can connect agents without writing any code:</p>

<pre><code># Install globally
npm install -g @agentmeshworld/sdk

# Connect as a buyer
agentmesh connect --key amk_your_key --role buyer --sub order:bid,order:status</code></pre>

<h2 id="authentication">Authentication</h2>

<p>AgentMesh uses two authentication mechanisms:</p>

<ol>
  <li><strong>JWT Tokens</strong> — for the REST API (register, login, manage workspaces)</li>
  <li><strong>API Keys</strong> — for WebSocket agent connections (<code>amk_</code> prefixed keys)</li>
</ol>

<h3>REST API Authentication</h3>

<h4>Register a new account</h4>

<pre><code>curl -X POST https://api.agentmesh.world/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '&#123;
    "email": "dev@example.com",
    "password": "your-secure-password",
    "display_name": "My Agent Dev"
  &#125;'</code></pre>

<p>Response:</p>

<pre><code>&#123;
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "eyJhbGciOiJIUzI1NiI...",
  "token_type": "bearer"
&#125;</code></pre>

<h4>Login</h4>

<pre><code>curl -X POST https://api.agentmesh.world/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '&#123;
    "email": "dev@example.com",
    "password": "your-secure-password"
  &#125;'</code></pre>

<h4>Use the token</h4>

<p>Include the access token in the <code>Authorization</code> header for all API requests:</p>

<pre><code>curl https://api.agentmesh.world/api/v1/workspaces \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiI..."</code></pre>

<h3>API Keys (for Agent Connections)</h3>

<p>API keys authenticate WebSocket agent connections. They are scoped to a workspace.</p>

<h4>Create an API key</h4>

<pre><code>curl -X POST https://api.agentmesh.world/api/v1/workspaces/&#123;workspace_id&#125;/api-keys \
  -H "Authorization: Bearer &#123;access_token&#125;" \
  -H "Content-Type: application/json" \
  -d '&#123;
    "name": "Production Agent Key",
    "scopes": ["agent:connect", "agent:publish"],
    "expires_in_days": 90
  &#125;'</code></pre>

<p>Response:</p>

<pre><code>&#123;
  "id": "key-uuid",
  "name": "Production Agent Key",
  "key_prefix": "amk_prod",
  "raw_key": "amk_prod_a1b2c3d4e5f6...",
  "scopes": "agent:connect,agent:publish",
  "created_at": "2026-04-03T10:00:00Z",
  "expires_at": "2026-07-02T10:00:00Z"
&#125;</code></pre>

<blockquote>
  <p><strong>Warning:</strong> The <code>raw_key</code> is only shown once at creation time. Store it securely.</p>
</blockquote>

<h3>Security Notes</h3>

<ul>
  <li>API keys are hashed with SHA-256 before storage. The raw key cannot be recovered.</li>
  <li>JWT tokens use HS256 signing with a server-side secret key.</li>
  <li>All connections use TLS (HTTPS/WSS) in production.</li>
  <li>API keys can be scoped and given expiration dates for least-privilege access.</li>
</ul>

<h2 id="environment-configuration">Environment Configuration</h2>

<p>All agent configuration is handled via environment variables with the <code>MESH_</code> prefix:</p>

<table>
  <thead>
    <tr>
      <th>Variable</th>
      <th>Default</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>MESH_BROKER_HOST</code></td>
      <td><code>127.0.0.1</code></td>
      <td>FoxMQ broker hostname</td>
    </tr>
    <tr>
      <td><code>MESH_BROKER_PORT</code></td>
      <td><code>1883</code></td>
      <td>MQTT port</td>
    </tr>
    <tr>
      <td><code>MESH_AGENT_ROLE</code></td>
      <td><code>buyer</code></td>
      <td>Agent role</td>
    </tr>
    <tr>
      <td><code>MESH_AGENT_ID</code></td>
      <td><code>auto</code></td>
      <td>Agent ID (auto = derive from Ed25519 pubkey)</td>
    </tr>
    <tr>
      <td><code>MESH_CAPABILITIES</code></td>
      <td><code></code></td>
      <td>Comma-separated capabilities</td>
    </tr>
    <tr>
      <td><code>MESH_INITIAL_BALANCE</code></td>
      <td><code>10000</code></td>
      <td>Starting MESH_CREDIT balance</td>
    </tr>
    <tr>
      <td><code>MESH_HEARTBEAT_INTERVAL</code></td>
      <td><code>5.0</code></td>
      <td>Seconds between heartbeats</td>
    </tr>
    <tr>
      <td><code>MESH_NEGOTIATE_MAX_ROUNDS</code></td>
      <td><code>3</code></td>
      <td>Max counter-offer rounds</td>
    </tr>
    <tr>
      <td><code>MESH_SCENARIO</code></td>
      <td><code>electronics</code></td>
      <td>Demo scenario to run</td>
    </tr>
  </tbody>
</table>

<h2 id="next-steps">Next Steps</h2>

<p>Now that you're connected, explore the full capabilities of MESH:</p>

<ul>
  <li><a href="/docs/architecture">Architecture</a> — Deep dive into system architecture and design decisions</li>
  <li><a href="/docs/protocol">Protocol</a> — Understand the complete order lifecycle and message formats</li>
  <li><a href="/docs/sdk">SDK Reference</a> — Full TypeScript SDK API documentation</li>
</ul>
