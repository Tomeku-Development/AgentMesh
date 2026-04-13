<script lang="ts">
  import { page } from '$app/stores';

  $: currentPath = $page.url.pathname;

  const navSections = [
    {
      title: 'Getting Started',
      links: [
        { label: 'Overview', href: '/docs/getting-started/' },
        { label: 'Quickstart', href: '/docs/getting-started/#quickstart' },
        { label: 'Authentication', href: '/docs/getting-started/#authentication' }
      ]
    },
    {
      title: 'Architecture',
      links: [
        { label: 'System Overview', href: '/docs/architecture/' },
        { label: 'Agent Roles', href: '/docs/architecture/#agent-roles' },
        { label: 'Security', href: '/docs/architecture/#security' },
        { label: 'Economic Model', href: '/docs/architecture/#economic-model' },
        { label: 'Self-Healing', href: '/docs/architecture/#self-healing' }
      ]
    },
    {
      title: 'Protocol',
      links: [
        { label: 'Order Lifecycle', href: '/docs/protocol/' },
        { label: 'Negotiation', href: '/docs/protocol/#negotiation' },
        { label: 'MQTT Topics', href: '/docs/protocol/#mqtt-topics' },
        { label: 'Message Format', href: '/docs/protocol/#message-format' },
        { label: 'WebSocket', href: '/docs/protocol/#websocket' }
      ]
    },
    {
      title: 'SDK',
      links: [
        { label: 'TypeScript SDK', href: '/docs/sdk/' },
        { label: 'Examples', href: '/docs/sdk/#examples' },
        { label: 'CLI Tools', href: '/docs/sdk/#cli-tools' }
      ]
    }
  ];

  function isActiveLink(href: string): boolean {
    if (href.includes('#')) {
      const basePath = href.split('#')[0];
      return currentPath === basePath || currentPath === basePath.slice(0, -1);
    }
    return currentPath === href || currentPath === href.slice(0, -1);
  }

  function isActiveSection(sectionLinks: { label: string; href: string }[]): boolean {
    return sectionLinks.some(link => {
      const basePath = link.href.split('#')[0];
      return currentPath.startsWith(basePath) || currentPath.startsWith(basePath.slice(0, -1));
    });
  }

  let mobileMenuOpen = false;

  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }
</script>

<div class="docs-layout">
  <!-- Top Navigation Bar -->
  <nav class="docs-navbar">
    <div class="nav-container">
      <a href="/" class="nav-logo">
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

      <div class="nav-breadcrumb">
        <span class="breadcrumb-text">Documentation</span>
      </div>

      <div class="nav-actions">
        <a href="/" class="nav-back-link">← Back to Home</a>
      </div>

      <button class="mobile-menu-toggle" on:click={toggleMobileMenu} aria-label="Toggle menu">
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
      </button>
    </div>
  </nav>

  <!-- Main Content Area -->
  <div class="docs-main">
    <!-- Sidebar -->
    <aside class="docs-sidebar" class:open={mobileMenuOpen}>
      <nav class="sidebar-nav">
        {#each navSections as section}
          <div class="nav-section" class:active={isActiveSection(section.links)}>
            <h4 class="section-title">{section.title}</h4>
            <ul class="section-links">
              {#each section.links as link}
                <li>
                  <a 
                    href={link.href} 
                    class="sidebar-link" 
                    class:active={isActiveLink(link.href)}
                    on:click={() => mobileMenuOpen = false}
                  >
                    {link.label}
                  </a>
                </li>
              {/each}
            </ul>
          </div>
        {/each}
      </nav>
    </aside>

    <!-- Content Area -->
    <main class="docs-content">
      <div class="content-wrapper">
        <slot />
      </div>
    </main>
  </div>
</div>

<style>
  :global(*) {
    box-sizing: border-box;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

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
    --font-heading: 'Chakra Petch', sans-serif;
    --font-mono: 'IBM Plex Mono', monospace;
  }

  .docs-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-heading);
  }

  /* Navigation Bar */
  .docs-navbar {
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
    max-width: 100%;
    height: 100%;
    padding: 0 24px;
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

  .nav-breadcrumb {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .breadcrumb-text {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text-dim);
  }

  .nav-actions {
    display: flex;
    align-items: center;
  }

  .nav-back-link {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text-secondary);
    text-decoration: none;
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 3px;
    transition: all 0.2s ease;
  }

  .nav-back-link:hover {
    color: var(--text);
    border-color: var(--border-strong);
  }

  .mobile-menu-toggle {
    display: none;
    flex-direction: column;
    gap: 5px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 8px;
  }

  .hamburger-line {
    display: block;
    width: 20px;
    height: 2px;
    background: var(--text);
    transition: all 0.3s ease;
  }

  /* Main Layout */
  .docs-main {
    display: flex;
    padding-top: 56px;
    min-height: 100vh;
  }

  /* Sidebar */
  .docs-sidebar {
    position: fixed;
    top: 56px;
    left: 0;
    bottom: 0;
    width: 240px;
    background: var(--bg-elevated);
    border-right: 1px solid var(--border);
    overflow-y: auto;
    padding: 24px 0;
    z-index: 100;
  }

  .sidebar-nav {
    padding: 0 8px;
  }

  .nav-section {
    margin-bottom: 8px;
  }

  .section-title {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 0;
    padding: 16px 16px 8px 16px;
  }

  .nav-section:first-child .section-title {
    margin-top: 0;
  }

  .section-links {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .sidebar-link {
    display: block;
    font-family: var(--font-heading);
    font-size: 0.85rem;
    font-weight: 400;
    color: var(--text-secondary);
    text-decoration: none;
    padding: 8px 16px;
    border-left: 2px solid transparent;
    transition: all 0.2s ease;
  }

  .sidebar-link:hover {
    color: var(--text);
    background: var(--accent-dim);
  }

  .sidebar-link.active {
    color: var(--accent);
    background: var(--accent-dim);
    border-left-color: var(--accent);
  }

  /* Content Area */
  .docs-content {
    flex: 1;
    margin-left: 240px;
    padding: 0;
    min-width: 0;
  }

  .content-wrapper {
    max-width: 860px;
    padding: 40px 48px;
    margin: 0 auto;
  }

  /* Content Typography Styles */
  :global(.docs-content h1) {
    font-family: var(--font-heading);
    font-weight: 700;
    font-size: 1.8rem;
    color: var(--text);
    margin: 0 0 8px 0;
  }

  :global(.docs-content h2) {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 1.3rem;
    color: var(--text);
    margin: 48px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }

  :global(.docs-content h3) {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: 1.05rem;
    color: var(--text);
    margin: 32px 0 12px 0;
  }

  :global(.docs-content p) {
    font-family: var(--font-heading);
    font-weight: 400;
    font-size: 0.95rem;
    color: var(--text-secondary);
    line-height: 1.7;
    margin: 0 0 16px 0;
  }

  :global(.docs-content pre) {
    font-family: var(--font-mono);
    font-size: 0.85rem;
    background: var(--bg-surface);
    padding: 16px;
    border-radius: 3px;
    border: 1px solid var(--border);
    overflow-x: auto;
    margin: 16px 0;
  }

  :global(.docs-content code) {
    font-family: var(--font-mono);
    font-size: 0.85rem;
    background: var(--bg-surface);
    padding: 2px 6px;
    border-radius: 2px;
  }

  :global(.docs-content pre code) {
    background: transparent;
    padding: 0;
  }

  :global(.docs-content ul),
  :global(.docs-content ol) {
    margin: 0 0 16px 20px;
    padding: 0;
    line-height: 1.8;
  }

  :global(.docs-content ul) {
    list-style-type: disc;
  }

  :global(.docs-content ol) {
    list-style-type: decimal;
  }

  :global(.docs-content li) {
    font-family: var(--font-heading);
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-bottom: 4px;
  }

  :global(.docs-content table) {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
  }

  :global(.docs-content th) {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    font-weight: 600;
    text-align: left;
    background: var(--bg-surface);
    color: var(--text);
    padding: 12px 16px;
    border: 1px solid var(--border);
  }

  :global(.docs-content td) {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--text-secondary);
    padding: 12px 16px;
    border: 1px solid var(--border);
  }

  :global(.docs-content a) {
    color: var(--accent);
    text-decoration: none;
  }

  :global(.docs-content a:hover) {
    text-decoration: underline;
  }

  :global(.docs-content blockquote) {
    border-left: 3px solid var(--accent);
    padding-left: 16px;
    margin: 16px 0;
    font-style: italic;
    color: var(--text-dim);
  }

  :global(.docs-content blockquote p) {
    margin: 0;
  }

  :global(.docs-content hr) {
    border: none;
    border-top: 1px solid var(--border);
    margin: 32px 0;
  }

  /* Responsive Design */
  @media (max-width: 900px) {
    .docs-sidebar {
      transform: translateX(-100%);
      transition: transform 0.3s ease;
    }

    .docs-sidebar.open {
      transform: translateX(0);
    }

    .docs-content {
      margin-left: 0;
    }

    .content-wrapper {
      padding: 32px 24px;
    }

    .mobile-menu-toggle {
      display: flex;
    }

    .nav-back-link {
      display: none;
    }
  }

  @media (max-width: 600px) {
    .content-wrapper {
      padding: 24px 16px;
    }

    :global(.docs-content h1) {
      font-size: 1.5rem;
    }

    :global(.docs-content h2) {
      font-size: 1.15rem;
    }

    :global(.docs-content h3) {
      font-size: 1rem;
    }

    :global(.docs-content p),
    :global(.docs-content li) {
      font-size: 0.9rem;
    }
  }
</style>
