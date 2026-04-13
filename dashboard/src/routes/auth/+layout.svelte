<style>
  :global(body) {
    margin: 0;
    background: #0f0f11;
  }

  .auth-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    font-family: 'Chakra Petch', sans-serif;
    background: #0f0f11;
    color: #f4f4f5;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: #f4f4f5;
    margin-bottom: 32px;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    color: #ff6f00;
  }

  .logo-text {
    font-family: 'Chakra Petch', sans-serif;
    font-weight: 700;
    font-size: 1.5rem;
    letter-spacing: 4px;
    color: #ff6f00;
  }
</style>

<div class="auth-shell">
  <a href="/" class="logo">
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
  <slot />
</div>
