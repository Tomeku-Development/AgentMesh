<svelte:head>
  <title>Documentation — MESH</title>
  <meta name="description" content="MESH documentation: architecture, protocol specification, SDK reference, and getting started guides for decentralized multi-agent supply chain coordination." />
</svelte:head>

<div class="docs-index">
  <header class="docs-header">
    <h1 class="docs-title">MESH Documentation</h1>
    <p class="docs-subtitle">Everything you need to build, deploy, and operate autonomous supply chain agents.</p>
  </header>

  <div class="quick-links-grid">
    <a href="/docs/getting-started/" class="quick-link-card">
      <div class="card-icon">🚀</div>
      <h3 class="card-title">Getting Started</h3>
      <p class="card-description">Core concepts, quickstart guide, and authentication setup</p>
    </a>

    <a href="/docs/architecture/" class="quick-link-card">
      <div class="card-icon">🏗️</div>
      <h3 class="card-title">Architecture</h3>
      <p class="card-description">System design, agent roles, security model, and self-healing</p>
    </a>

    <a href="/docs/protocol/" class="quick-link-card">
      <div class="card-icon">📡</div>
      <h3 class="card-title">Protocol</h3>
      <p class="card-description">Order lifecycle, negotiation, MQTT topics, and message format</p>
    </a>

    <a href="/docs/sdk/" class="quick-link-card">
      <div class="card-icon">⚡</div>
      <h3 class="card-title">SDK Reference</h3>
      <p class="card-description">TypeScript SDK, code examples, and CLI tools</p>
    </a>
  </div>

  <section class="overview-section">
    <h2>What is MESH?</h2>
    <p>
      MESH is a decentralized multi-agent supply chain coordination platform. It enables autonomous AI agents 
      to coordinate complex supply chain operations through Byzantine fault-tolerant MQTT messaging, 
      LLM-powered negotiation, and cryptographic trust — all without central authority.
    </p>
    <p>
      The platform consists of 5 specialized agent roles (Buyer, Supplier, Logistics, Inspector, Oracle) 
      that work together through an 8-phase protocol to discover, negotiate, execute, and settle 
      supply chain transactions.
    </p>
  </section>

  <section class="overview-section">
    <h2>Key Features</h2>
    <ul>
      <li><strong>5 Autonomous Agents</strong> — Specialized roles with per-role reputation tracking</li>
      <li><strong>LLM-Powered Decisions</strong> — Dynamic negotiation and market analysis via Claude 3</li>
      <li><strong>Byzantine Fault Tolerance</strong> — BFT-ordered MQTT via 3-node FoxMQ cluster</li>
      <li><strong>Self-Healing Mesh</strong> — Automatic failure detection and intelligent recovery</li>
      <li><strong>Cryptographic Identity</strong> — Ed25519 signing for zero-trust architecture</li>
      <li><strong>Escrow Settlement</strong> — MESH_CREDIT token with atomic multi-party escrow</li>
    </ul>
  </section>
</div>

<style>
  .docs-index {
    max-width: 100%;
  }

  .docs-header {
    margin-bottom: 48px;
  }

  .docs-title {
    font-family: var(--font-heading, 'Chakra Petch', sans-serif);
    font-weight: 700;
    font-size: 1.8rem;
    color: var(--text, #f4f4f5);
    margin: 0 0 8px 0;
  }

  .docs-subtitle {
    font-family: var(--font-heading, 'Chakra Petch', sans-serif);
    font-weight: 400;
    font-size: 1rem;
    color: var(--text-secondary, #9a9a9e);
    line-height: 1.6;
    margin: 0;
  }

  .quick-links-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 48px;
  }

  .quick-link-card {
    background: var(--bg-surface, #232427);
    border: 1px solid var(--border, rgba(255, 255, 255, 0.08));
    border-radius: 3px;
    padding: 24px;
    text-decoration: none;
    transition: all 0.2s ease;
    display: block;
  }

  .quick-link-card:hover {
    transform: translateY(-2px);
    border-color: var(--border-strong, rgba(255, 255, 255, 0.14));
  }

  .card-icon {
    font-size: 1.5rem;
    margin-bottom: 12px;
  }

  .card-title {
    font-family: var(--font-heading, 'Chakra Petch', sans-serif);
    font-weight: 600;
    font-size: 1rem;
    color: var(--text, #f4f4f5);
    margin: 0 0 8px 0;
  }

  .card-description {
    font-family: var(--font-heading, 'Chakra Petch', sans-serif);
    font-weight: 400;
    font-size: 0.85rem;
    color: var(--text-secondary, #9a9a9e);
    line-height: 1.5;
    margin: 0;
  }

  .overview-section {
    margin-bottom: 32px;
  }

  .overview-section h2 {
    font-family: var(--font-heading, 'Chakra Petch', sans-serif);
    font-weight: 600;
    font-size: 1.3rem;
    color: var(--text, #f4f4f5);
    margin: 0 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border, rgba(255, 255, 255, 0.08));
  }

  .overview-section p {
    font-family: var(--font-heading, 'Chakra Petch', sans-serif);
    font-weight: 400;
    font-size: 0.95rem;
    color: var(--text-secondary, #9a9a9e);
    line-height: 1.7;
    margin: 0 0 16px 0;
  }

  .overview-section ul {
    list-style-type: disc;
    margin: 0 0 16px 20px;
    padding: 0;
    line-height: 1.8;
  }

  .overview-section li {
    font-family: var(--font-heading, 'Chakra Petch', sans-serif);
    font-size: 0.95rem;
    color: var(--text-secondary, #9a9a9e);
    margin-bottom: 4px;
  }

  .overview-section li strong {
    color: var(--text, #f4f4f5);
    font-weight: 600;
  }

  @media (max-width: 600px) {
    .quick-links-grid {
      grid-template-columns: 1fr;
    }

    .docs-title {
      font-size: 1.5rem;
    }

    .quick-link-card {
      padding: 20px;
    }
  }
</style>
