<svelte:head>
  <title>MESH — Decentralized Multi-Agent Supply Chain Coordination</title>
  <meta name="description" content="MESH enables autonomous AI agents to coordinate supply chain operations through Byzantine fault-tolerant MQTT messaging, cryptographic identity, and intelligent LLM-driven negotiation." />
  <meta name="robots" content="index, follow" />
  <meta name="theme-color" content="#0f0f11" />
  <link rel="canonical" href="https://agentmesh.world" />
  
  <!-- Open Graph -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://agentmesh.world" />
  <meta property="og:title" content="MESH — Decentralized Multi-Agent Supply Chain Coordination" />
  <meta property="og:description" content="Autonomous AI agents coordinating supply chains through BFT-ordered messaging, LLM-powered negotiation, and cryptographic trust." />
  <meta property="og:image" content="https://agentmesh.world/og-image.png" />
  <meta property="og:site_name" content="MESH" />
  
  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="MESH — Decentralized Multi-Agent Supply Chain Coordination" />
  <meta name="twitter:description" content="Autonomous AI agents coordinating supply chains through BFT-ordered messaging, LLM-powered negotiation, and cryptographic trust." />
  <meta name="twitter:image" content="https://agentmesh.world/og-image.png" />
  
  <!-- JSON-LD -->
  {@html `<script type="application/ld+json">${JSON.stringify({
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "MESH",
    "description": "Decentralized Multi-Agent Supply Chain Coordination",
    "url": "https://agentmesh.world",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Cross-platform",
    "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" }
  })}</script>`}
</svelte:head>

<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import TourStyles from '$lib/tour/TourStyles.svelte';

  let mobileMenuOpen = false;
  let visibleSections = new Set<string>();
  let showTourButton = false;

  onMount(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            visibleSections.add(entry.target.id);
            visibleSections = visibleSections;
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    document.querySelectorAll('section[id]').forEach((section) => {
      observer.observe(section);
    });

    // Initialize tour
    initTour();

    return () => observer.disconnect();
  });

  async function initTour() {
    if (!browser) return;
    const { startLandingTour, shouldShowLandingTour } = await import('$lib/tour/driver');
    showTourButton = true;

    // Auto-start tour on first visit (with 1.5s delay for page to render)
    if (shouldShowLandingTour()) {
      setTimeout(() => startLandingTour(), 1500);
    }
  }

  async function handleTour() {
    if (!browser) return;
    const { startLandingTour } = await import('$lib/tour/driver');
    startLandingTour();
  }

  function scrollToSection(id: string) {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      mobileMenuOpen = false;
    }
  }

  const features = [
    {
      title: '5 Autonomous Agents',
      icon: 'dots',
      description: 'Buyer, Supplier, Logistics, Inspector, and Oracle agents operating independently with specialized capabilities and per-role reputation tracking.'
    },
    {
      title: 'LLM-Powered Decisions',
      icon: 'brain',
      description: 'Amazon Bedrock and OpenRouter integration with intelligent fallbacks. Dynamic negotiation, market analysis, and quality assessment driven by Claude 3.'
    },
    {
      title: 'Byzantine Fault Tolerance',
      icon: 'shield',
      description: 'BFT-ordered MQTT via 3-node FoxMQ cluster ensures message consistency even when nodes fail. Hashgraph-inspired consensus.'
    },
    {
      title: 'Self-Healing Mesh',
      icon: 'refresh',
      description: 'Automatic failure detection via heartbeat quorum, intelligent role redistribution, and graceful recovery with LLM-guided root cause analysis.'
    },
    {
      title: 'Cryptographic Identity',
      icon: 'key',
      description: 'Ed25519 key pairs for every agent. Per-message signing and verification. Zero-trust architecture with PyNaCl cryptographic primitives.'
    },
    {
      title: 'Escrow Settlement',
      icon: 'coin',
      description: 'MESH_CREDIT token with atomic multi-party escrow. Reputation-weighted settlement with automatic dispute resolution and burn mechanics.'
    }
  ];

  const protocolPhases = [
    { name: 'DISCOVER', status: 'completed', description: 'Find trading partners' },
    { name: 'REQUEST', status: 'completed', description: 'Submit purchase order' },
    { name: 'BID', status: 'completed', description: 'Suppliers submit offers' },
    { name: 'NEGOTIATE', status: 'completed', description: 'Counter-offer rounds' },
    { name: 'COMMIT', status: 'active', description: 'Lock escrow funds' },
    { name: 'EXECUTE', status: 'pending', description: 'Fulfill & ship goods' },
    { name: 'VERIFY', status: 'pending', description: 'Quality inspection' },
    { name: 'SETTLE', status: 'pending', description: 'Release payments' }
  ];

  const architectureLayers = [
    {
      title: 'FoxMQ BFT Cluster',
      description: '3-node MQTT 5.0 broker cluster with Byzantine fault tolerance and message ordering guarantees',
      color: '#60a5fa'
    },
    {
      title: 'Core Framework',
      description: 'Identity (Ed25519), Ledger, Reputation Engine, Peer Registry, State Machine, HLC Clock',
      color: '#4ade80'
    },
    {
      title: 'Agent System',
      description: '5 specialized roles with LLM-enhanced decision making, market-aware pricing, and adaptive strategies',
      color: '#ff6f00'
    },
    {
      title: 'Negotiation & Healing',
      description: 'Multi-round counter-offer engine, dispute arbitration, failure detection, role redistribution',
      color: '#c084fc'
    }
  ];

  const agentRoles = [
    { name: 'BUYER', color: '#ff6f00' },
    { name: 'SUPPLIER', color: '#4ade80' },
    { name: 'LOGISTICS', color: '#60a5fa' },
    { name: 'INSPECTOR', color: '#c084fc' },
    { name: 'ORACLE', color: '#fbbf24' }
  ];

  const demoAgents = [
    { role: 'buyer', name: 'buyer-001', status: 'online' },
    { role: 'supplier', name: 'supplier-001', status: 'online' },
    { role: 'logistics', name: 'logistics-001', status: 'online' },
    { role: 'inspector', name: 'inspector-001', status: 'online' },
    { role: 'oracle', name: 'oracle-001', status: 'online' }
  ];
</script>

<!-- Navigation -->
<nav class="navbar">
  <div class="nav-container">
    <a href="#hero" class="nav-logo" on:click|preventDefault={() => scrollToSection('hero')}>
      <svg class="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="5" r="2" fill="currentColor"/>
        <circle cx="5" cy="12" r="2" fill="currentColor"/>
        <circle cx="19" cy="12" r="2" fill="currentColor"/>
        <circle cx="8" cy="19" r="2" fill="currentColor"/>
        <circle cx="16" cy="19" r="2" fill="currentColor"/>
        <line x1="12" y1="7" x2="12" y2="17" stroke="currentColor" stroke-width="1"/>
        <line x1="7" y1="11" x2="11" y2="6" stroke="currentColor" stroke-width="1"/>
        <line x1="17" y1="11" x2="13" y2="6" stroke="currentColor" stroke-width="1"/>
        <line x1="7" y1="13" x2="10" y2="18" stroke="currentColor" stroke-width="1"/>
        <line x1="17" y1="13" x2="14" y2="18" stroke="currentColor" stroke-width="1"/>
        <line x1="10" y1="19" x2="14" y2="19" stroke="currentColor" stroke-width="1"/>
      </svg>
      <span class="logo-text">MESH</span>
    </a>

    <div class="nav-links" class:open={mobileMenuOpen}>
      <button class="nav-link" on:click={() => scrollToSection('features')}>FEATURES</button>
      <button class="nav-link" on:click={() => scrollToSection('protocol')}>PROTOCOL</button>
      <button class="nav-link" on:click={() => scrollToSection('architecture')}>ARCHITECTURE</button>
      <button class="nav-link" on:click={() => scrollToSection('demo')}>DEMO</button>
    </div>

    <a href="/dashboard" class="nav-cta">OPEN DASHBOARD</a>

    <button class="hamburger" on:click={() => mobileMenuOpen = !mobileMenuOpen} aria-label="Toggle menu">
      <span></span>
      <span></span>
      <span></span>
    </button>
  </div>
</nav>

<!-- Hero Section -->
<section id="hero" class="hero" class:visible={visibleSections.has('hero')}>
  <div class="hero-bg">
    <div class="mesh-grid"></div>
    <div class="glow-center"></div>
  </div>
  <div class="hero-content">
    <h1 class="hero-title">
      <span class="line">Decentralized <span class="accent">Multi-Agent</span></span>
      <span class="line">Supply Chain Coordination</span>
    </h1>
    <p class="hero-subtitle">
      Autonomous AI agents coordinating complex supply chain operations through Byzantine fault-tolerant messaging, 
      LLM-powered negotiation, and cryptographic trust — all without central authority.
    </p>
    <div class="hero-ctas">
      <button class="btn btn-primary" id="tour-demo-btn" on:click={() => scrollToSection('demo')}>View Live Demo</button>
      <a href="/docs" class="btn btn-outline">Read Documentation</a>
    </div>
    <p class="hero-tagline">Built for the Vertex Swarm Challenge</p>
  </div>
</section>

<!-- Features Section -->
<section id="features" class="features" class:visible={visibleSections.has('features')}>
  <div class="container">
    <div class="section-header">
      <span class="section-label">CORE CAPABILITIES</span>
      <h2 class="section-title">Intelligent Agent Mesh</h2>
    </div>
    <div class="features-grid">
      {#each features as feature}
        <div class="feature-card">
          <div class="feature-icon">
            {#if feature.icon === 'dots'}
              <div class="icon-dots">
                <span style="background: #ff6f00;"></span>
                <span style="background: #4ade80;"></span>
                <span style="background: #60a5fa;"></span>
                <span style="background: #c084fc;"></span>
                <span style="background: #fbbf24;"></span>
              </div>
            {:else if feature.icon === 'brain'}
              <span class="icon-symbol" style="color: #ff6f00;">◈</span>
            {:else if feature.icon === 'shield'}
              <span class="icon-symbol" style="color: #4ade80;">◆</span>
            {:else if feature.icon === 'refresh'}
              <span class="icon-symbol" style="color: #60a5fa;">↻</span>
            {:else if feature.icon === 'key'}
              <span class="icon-symbol" style="color: #c084fc;">⚷</span>
            {:else if feature.icon === 'coin'}
              <span class="icon-symbol" style="color: #fbbf24;">◎</span>
            {/if}
          </div>
          <h3 class="feature-title">{feature.title}</h3>
          <p class="feature-description">{feature.description}</p>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Protocol Section -->
<section id="protocol" class="protocol" class:visible={visibleSections.has('protocol')}>
  <div class="container">
    <div class="section-header">
      <span class="section-label">ORDER LIFECYCLE</span>
      <h2 class="section-title">8-Phase Protocol</h2>
    </div>
    <div class="protocol-pipeline">
      <div class="pipeline-line"></div>
      {#each protocolPhases as phase, i}
        <div class="phase" class:completed={phase.status === 'completed'} class:active={phase.status === 'active'} style="animation-delay: {i * 0.1}s">
          <div class="phase-node"></div>
          <span class="phase-name">{phase.name}</span>
          <span class="phase-description">{phase.description}</span>
        </div>
      {/each}
    </div>
    <p class="protocol-description">
      Orders flow through a deterministic state machine: agents discover opportunities, submit requests, 
      receive bids, negotiate terms, commit to contracts, execute deliveries, verify quality, and settle payments. 
      Each phase is cryptographically signed and ordered via BFT consensus.
    </p>
  </div>
</section>

<!-- Architecture Section -->
<section id="architecture" class="architecture" class:visible={visibleSections.has('architecture')}>
  <div class="container">
    <div class="section-header">
      <span class="section-label">SYSTEM ARCHITECTURE</span>
      <h2 class="section-title">Layered Design</h2>
    </div>
    <div class="architecture-layers">
      {#each architectureLayers as layer}
        <div class="layer-card" style="--layer-color: {layer.color}">
          <h3 class="layer-title">{layer.title}</h3>
          <p class="layer-description">{layer.description}</p>
        </div>
      {/each}
    </div>
    <div class="agent-strip">
      {#each agentRoles as role}
        <span class="agent-badge" style="--agent-color: {role.color}">{role.name}</span>
      {/each}
    </div>
  </div>
</section>

<!-- Demo Section -->
<section id="demo" class="demo" class:visible={visibleSections.has('demo')}>
  <div class="container">
    <div class="section-header">
      <span class="section-label">LIVE DEMONSTRATION</span>
      <h2 class="section-title">Watch Agents in Action</h2>
    </div>
    <div class="demo-panel">
      <div class="demo-metrics">
        <div class="metric">
          <span class="metric-value">5</span>
          <span class="metric-label">AGENTS</span>
        </div>
        <div class="metric-divider"></div>
        <div class="metric">
          <span class="metric-value">12</span>
          <span class="metric-label">ORDERS</span>
        </div>
        <div class="metric-divider"></div>
        <div class="metric">
          <span class="metric-value">98.2%</span>
          <span class="metric-label">UPTIME</span>
        </div>
        <div class="metric-divider"></div>
        <div class="metric">
          <span class="metric-value">&lt; 50ms</span>
          <span class="metric-label">LATENCY</span>
        </div>
      </div>
      <div class="demo-agents">
        {#each demoAgents as agent}
          <div class="demo-agent-card">
            <div class="demo-agent-header">
              <span class="demo-agent-role" style="color: {agent.role === 'buyer' ? '#ff6f00' : agent.role === 'supplier' ? '#4ade80' : agent.role === 'logistics' ? '#60a5fa' : agent.role === 'inspector' ? '#c084fc' : '#fbbf24'}">{agent.role.toUpperCase()}</span>
              <span class="demo-agent-status online">online</span>
            </div>
            <span class="demo-agent-name">{agent.name}</span>
          </div>
        {/each}
      </div>
      <div class="demo-order-flow">
        <div class="order-bar">
          <div class="order-progress" style="width: 75%;"></div>
        </div>
        <div class="order-labels">
          <span>DISCOVER</span>
          <span>COMMIT</span>
          <span>SETTLE</span>
        </div>
      </div>
    </div>
    <div class="demo-ctas">
      <a href="/dashboard" class="btn btn-primary" id="tour-launch-btn">Launch Dashboard</a>
      <a href="https://github.com" class="btn btn-outline" target="_blank" rel="noopener">View on GitHub</a>
    </div>
  </div>
</section>

<!-- Footer -->
<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-col footer-brand">
        <div class="footer-logo">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="5" r="2" fill="currentColor"/>
            <circle cx="5" cy="12" r="2" fill="currentColor"/>
            <circle cx="19" cy="12" r="2" fill="currentColor"/>
            <circle cx="8" cy="19" r="2" fill="currentColor"/>
            <circle cx="16" cy="19" r="2" fill="currentColor"/>
            <line x1="12" y1="7" x2="12" y2="17" stroke="currentColor" stroke-width="1"/>
            <line x1="7" y1="11" x2="11" y2="6" stroke="currentColor" stroke-width="1"/>
            <line x1="17" y1="11" x2="13" y2="6" stroke="currentColor" stroke-width="1"/>
            <line x1="7" y1="13" x2="10" y2="18" stroke="currentColor" stroke-width="1"/>
            <line x1="17" y1="13" x2="14" y2="18" stroke="currentColor" stroke-width="1"/>
            <line x1="10" y1="19" x2="14" y2="19" stroke="currentColor" stroke-width="1"/>
          </svg>
          <span class="logo-text">MESH</span>
        </div>
        <p class="footer-tagline">Decentralized Multi-Agent Supply Chain Coordination</p>
      </div>
      <div class="footer-col">
        <h4 class="footer-heading">Product</h4>
        <ul class="footer-links">
          <li><a href="/#features">Features</a></li>
          <li><a href="/dashboard">Dashboard</a></li>
          <li><a href="/docs">Documentation</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4 class="footer-heading">Developers</h4>
        <ul class="footer-links">
          <li><a href="https://github.com" target="_blank" rel="noopener">GitHub</a></li>
          <li><a href="/docs/sdk">TypeScript SDK</a></li>
          <li><a href="/docs/sdk">REST API</a></li>
          <li><a href="/docs/protocol">MQTT Protocol</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4 class="footer-heading">Protocol</h4>
        <ul class="footer-links">
          <li><a href="/docs/architecture">Architecture</a></li>
          <li><a href="/docs/protocol">Message Format</a></li>
          <li><a href="/docs/protocol">Topic Hierarchy</a></li>
          <li><a href="/docs/architecture">Settlement</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p class="footer-copyright">© 2026 MESH. Built for the Vertex Swarm Challenge on Tashi.</p>
      <p class="footer-domain">agentmesh.world</p>
    </div>
  </div>
</footer>

{#if showTourButton}
  <button class="tour-fab" on:click={handleTour} title="Take a guided tour">
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <circle cx="12" cy="12" r="10"/>
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
    <span>Tour</span>
  </button>
{/if}

<TourStyles />

<style>
  :global(html) {
    scroll-behavior: smooth;
  }

  :global(*) {
    box-sizing: border-box;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  :global(body) {
    margin: 0;
    padding: 0;
    background: #0f0f11;
    color: #f4f4f5;
    font-family: 'Chakra Petch', sans-serif;
  }

  /* CSS Variables */
  :root {
    --bg: #0f0f11;
    --bg-elevated: #1b1c1e;
    --bg-surface: #232427;
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.14);
    --text: #f4f4f5;
    --text-secondary: #9a9a9e;
    --text-dim: #6b6b70;
    --accent: #ff6f00;
    --accent-dim: rgba(255, 111, 0, 0.15);
    --accent-hover: #e66300;
    --green: #4ade80;
    --red: #ef4444;
    --font-heading: 'Chakra Petch', sans-serif;
    --font-mono: 'IBM Plex Mono', monospace;
  }

  /* Container */
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
  }

  /* Navigation */
  .navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 56px;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    z-index: 1000;
  }

  .nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .nav-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--text);
  }

  .logo-icon {
    width: 24px;
    height: 24px;
    color: var(--accent);
  }

  .logo-text {
    font-family: var(--font-heading);
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: 3px;
    color: var(--accent);
  }

  .nav-links {
    display: flex;
    align-items: center;
    gap: 32px;
  }

  .nav-link {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-secondary);
    background: none;
    border: none;
    cursor: pointer;
    transition: color 0.2s ease;
    padding: 8px 0;
  }

  .nav-link:hover {
    color: var(--text);
  }

  .nav-cta {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--accent);
    text-decoration: none;
    padding: 8px 16px;
    border: 1px solid var(--accent);
    border-radius: 3px;
    transition: all 0.2s ease;
  }

  .nav-cta:hover {
    background: var(--accent-dim);
  }

  .hamburger {
    display: none;
    flex-direction: column;
    gap: 5px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 8px;
  }

  .hamburger span {
    display: block;
    width: 20px;
    height: 2px;
    background: var(--text);
    transition: all 0.3s ease;
  }

  /* Hero Section */
  .hero {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 80px 24px;
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.6s ease, transform 0.6s ease;
  }

  .hero.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .hero-bg {
    position: absolute;
    inset: 0;
    overflow: hidden;
    pointer-events: none;
  }

  .mesh-grid {
    position: absolute;
    inset: 0;
    background-image: 
      radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0);
    background-size: 40px 40px;
  }

  .glow-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, var(--accent-dim) 0%, transparent 70%);
    opacity: 0.5;
  }

  .hero-content {
    position: relative;
    text-align: center;
    max-width: 800px;
  }

  .hero-title {
    font-family: var(--font-heading);
    font-weight: 700;
    font-size: clamp(1.8rem, 5vw, 2.8rem);
    line-height: 1.2;
    margin: 0 0 24px 0;
    color: var(--text);
  }

  .hero-title .line {
    display: block;
  }

  .hero-title .accent {
    color: var(--accent);
  }

  .hero-subtitle {
    font-family: var(--font-heading);
    font-weight: 400;
    font-size: 1.1rem;
    line-height: 1.6;
    color: var(--text-secondary);
    max-width: 640px;
    margin: 0 auto 32px auto;
  }

  .hero-ctas {
    display: flex;
    gap: 16px;
    justify-content: center;
    margin-bottom: 24px;
  }

  .btn {
    font-family: var(--font-mono);
    font-weight: 600;
    font-size: 0.8rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    text-decoration: none;
    padding: 14px 32px;
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
  }

  .btn-primary {
    background: var(--accent);
    color: var(--bg);
  }

  .btn-primary:hover {
    background: var(--accent-hover);
  }

  .btn-outline {
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
  }

  .btn-outline:hover {
    background: var(--accent-dim);
  }

  .hero-tagline {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-dim);
    margin: 0;
  }

  /* Section Common Styles */
  section {
    padding: 80px 0;
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.6s ease, transform 0.6s ease;
  }

  section.visible {
    opacity: 1;
    transform: translateY(0);
  }

  .section-header {
    text-align: center;
    margin-bottom: 48px;
  }

  .section-label {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-dim);
    display: block;
    margin-bottom: 12px;
  }

  .section-title {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 1.5rem;
    color: var(--text);
    margin: 0;
  }

  /* Features Section */
  .features {
    background: var(--bg);
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }

  .feature-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 24px;
    transition: all 0.2s ease;
  }

  .feature-card:hover {
    border-color: var(--border-strong);
    transform: translateY(-2px);
  }

  .feature-icon {
    height: 40px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
  }

  .icon-dots {
    display: flex;
    gap: 6px;
  }

  .icon-dots span {
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }

  .icon-symbol {
    font-size: 1.5rem;
  }

  .feature-title {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 1rem;
    color: var(--text);
    margin: 0 0 8px 0;
  }

  .feature-description {
    font-family: var(--font-heading);
    font-weight: 400;
    font-size: 0.85rem;
    line-height: 1.6;
    color: var(--text-secondary);
    margin: 0;
  }

  /* Protocol Section */
  .protocol {
    background: var(--bg-elevated);
  }

  .protocol-pipeline {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 8px;
    margin-bottom: 32px;
    position: relative;
    padding-top: 20px;
  }

  .pipeline-line {
    position: absolute;
    top: 26px;
    left: calc(100% / 16);
    right: calc(100% / 16);
    height: 2px;
    background: linear-gradient(90deg, 
      var(--green) 0%, 
      var(--green) 50%, 
      var(--text-dim) 50%, 
      var(--text-dim) 100%
    );
    z-index: 1;
  }

  .phase {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    position: relative;
    z-index: 2;
    opacity: 0;
    animation: phaseLightUp 0.5s ease forwards;
  }

  @keyframes phaseLightUp {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .phase-node {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: var(--text-dim);
    margin-bottom: 12px;
    position: relative;
  }

  .phase.completed .phase-node {
    background: var(--green);
  }

  .phase.active .phase-node {
    background: var(--accent);
    box-shadow: 0 0 16px var(--accent), 0 0 32px rgba(255, 111, 0, 0.4);
  }

  .phase-name {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 1px;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  .phase.completed .phase-name {
    color: var(--green);
  }

  .phase.active .phase-name {
    color: var(--accent);
  }

  .phase-description {
    font-family: var(--font-heading);
    font-size: 0.7rem;
    color: var(--text-dim);
    line-height: 1.4;
    max-width: 100px;
  }

  .protocol-description {
    font-family: var(--font-heading);
    font-weight: 400;
    font-size: 0.9rem;
    line-height: 1.6;
    color: var(--text-secondary);
    text-align: center;
    max-width: 700px;
    margin: 0 auto;
  }

  /* Architecture Section */
  .architecture {
    background: var(--bg);
  }

  .architecture-layers {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 32px;
  }

  .layer-card {
    background: var(--bg-surface);
    border-left: 3px solid var(--layer-color);
    border-radius: 0 3px 3px 0;
    padding: 20px 24px;
  }

  .layer-title {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 1rem;
    color: var(--text);
    margin: 0 0 4px 0;
  }

  .layer-description {
    font-family: var(--font-heading);
    font-weight: 400;
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
  }

  .agent-strip {
    display: flex;
    justify-content: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .agent-badge {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1px;
    color: var(--agent-color);
    padding: 6px 12px;
    border: 1px solid var(--agent-color);
    border-radius: 3px;
    opacity: 0.8;
  }

  /* Demo Section */
  .demo {
    background: var(--bg-elevated);
  }

  .demo-panel {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 24px;
    margin-bottom: 32px;
  }

  .demo-metrics {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 24px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
    flex-wrap: wrap;
  }

  .metric {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  .metric-value {
    font-family: var(--font-heading);
    font-weight: 700;
    font-size: 1.5rem;
    color: var(--accent);
  }

  .metric-label {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    color: var(--text-dim);
  }

  .metric-divider {
    width: 1px;
    height: 40px;
    background: var(--border);
  }

  .demo-agents {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 24px;
    flex-wrap: wrap;
  }

  .demo-agent-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: 3px;
    padding: 12px 16px;
    min-width: 120px;
  }

  .demo-agent-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
  }

  .demo-agent-role {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 1px;
  }

  .demo-agent-status {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    padding: 2px 6px;
    border-radius: 2px;
  }

  .demo-agent-status.online {
    background: rgba(74, 222, 128, 0.15);
    color: var(--green);
  }

  .demo-agent-name {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  .demo-order-flow {
    padding-top: 24px;
    border-top: 1px solid var(--border);
  }

  .order-bar {
    height: 6px;
    background: var(--bg-surface);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 8px;
  }

  .order-progress {
    height: 100%;
    background: linear-gradient(90deg, var(--green) 0%, var(--accent) 100%);
    border-radius: 3px;
    transition: width 0.5s ease;
  }

  .order-labels {
    display: flex;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--text-dim);
    letter-spacing: 1px;
  }

  .demo-ctas {
    display: flex;
    gap: 16px;
    justify-content: center;
  }

  /* Footer */
  .footer {
    background: var(--bg);
    border-top: 1px solid var(--border);
    padding: 48px 0 24px 0;
  }

  .footer-grid {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr;
    gap: 32px;
    margin-bottom: 32px;
  }

  .footer-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }

  .footer-tagline {
    font-family: var(--font-heading);
    font-size: 0.75rem;
    color: var(--text-dim);
    margin: 0;
  }

  .footer-heading {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 1px;
    color: var(--text);
    margin: 0 0 16px 0;
    text-transform: uppercase;
  }

  .footer-links {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .footer-links li {
    margin-bottom: 8px;
  }

  .footer-links a,
  .footer-links button {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-decoration: none;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    transition: color 0.2s ease;
  }

  .footer-links a:hover,
  .footer-links button:hover {
    color: var(--text);
  }

  .footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 24px;
    border-top: 1px solid var(--border);
  }

  .footer-copyright,
  .footer-domain {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-dim);
    margin: 0;
  }

  /* Responsive Design */
  @media (max-width: 900px) {
    .features-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .protocol-pipeline {
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      row-gap: 32px;
    }

    .pipeline-line {
      display: none;
    }

    .phase-description {
      font-size: 0.65rem;
      max-width: 80px;
    }

    .footer-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .demo-agents {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
    }
  }

  @media (max-width: 600px) {
    .nav-links {
      display: none;
      position: absolute;
      top: 56px;
      left: 0;
      right: 0;
      background: var(--bg);
      border-bottom: 1px solid var(--border);
      flex-direction: column;
      padding: 16px 24px;
      gap: 0;
    }

    .nav-links.open {
      display: flex;
    }

    .nav-link {
      padding: 12px 0;
      width: 100%;
      text-align: left;
    }

    .nav-cta {
      display: none;
    }

    .hamburger {
      display: flex;
    }

    .hero-title {
      font-size: 1.6rem;
    }

    .hero-ctas {
      flex-direction: column;
      align-items: center;
    }

    .btn {
      width: 100%;
      max-width: 280px;
    }

    .features-grid {
      grid-template-columns: 1fr;
    }

    .protocol-pipeline {
      grid-template-columns: repeat(2, 1fr);
      gap: 20px;
      row-gap: 24px;
    }

    .pipeline-line {
      display: none;
    }

    .phase {
      opacity: 1;
      animation: none;
    }

    .phase-node {
      margin-bottom: 8px;
    }

    .phase-name {
      font-size: 0.6rem;
      margin-bottom: 4px;
    }

    .phase-description {
      font-size: 0.65rem;
      max-width: 120px;
    }

    .footer-grid {
      grid-template-columns: 1fr;
      gap: 24px;
    }

    .footer-bottom {
      flex-direction: column;
      gap: 8px;
      text-align: center;
    }

    .demo-agents {
      grid-template-columns: repeat(2, 1fr);
    }

    .demo-metrics {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
    }

    .metric-divider {
      display: none;
    }

    .demo-ctas {
      flex-direction: column;
      align-items: center;
    }
  }

  /* Tour FAB */
  .tour-fab {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    background: #ff6f00;
    color: #0f0f11;
    border: none;
    border-radius: 50px;
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(255, 111, 0, 0.4);
    transition: all 0.2s ease;
  }
  .tour-fab:hover {
    background: #ff8f33;
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(255, 111, 0, 0.5);
  }
</style>
