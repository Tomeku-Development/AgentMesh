<svelte:head>
  <title>Create Account — MESH</title>
</svelte:head>

<script lang="ts">
  import { register } from '$lib/api/auth';
  import { setTokens } from '$lib/stores/auth';
  import { goto } from '$app/navigation';

  let display_name = '';
  let email = '';
  let password = '';
  let confirmPassword = '';
  let error = '';
  let loading = false;

  function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  async function handleSubmit() {
    error = '';

    if (!display_name.trim()) {
      error = 'Display name is required';
      return;
    }

    if (!validateEmail(email)) {
      error = 'Please enter a valid email address';
      return;
    }

    if (password.length < 6) {
      error = 'Password must be at least 6 characters';
      return;
    }

    if (password !== confirmPassword) {
      error = 'Passwords do not match';
      return;
    }

    loading = true;
    try {
      const tokens = await register({ email, password, display_name });
      setTokens(tokens.access_token, tokens.refresh_token);
      goto('/workspaces');
    } catch (err) {
      error = err instanceof Error ? err.message : 'Registration failed';
    } finally {
      loading = false;
    }
  }
</script>

<style>
  .auth-card {
    max-width: 420px;
    width: 100%;
    background: #1b1c1e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 32px;
  }

  .auth-title {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 1.5rem;
    font-weight: 600;
    color: #f4f4f5;
    margin: 0 0 8px 0;
  }

  .auth-subtitle {
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.9rem;
    color: #9a9a9e;
    margin: 0 0 32px 0;
  }

  .form-group {
    margin-bottom: 20px;
  }

  .form-label {
    display: block;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.8rem;
    color: #9a9a9e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
  }

  .form-input {
    width: 100%;
    padding: 12px 16px;
    background: #232427;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    color: #f4f4f5;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.95rem;
    outline: none;
    transition: border-color 0.2s ease;
    box-sizing: border-box;
  }

  .form-input::placeholder {
    color: #6b6b70;
  }

  .form-input:focus {
    border-color: #ff6f00;
  }

  .submit-btn {
    width: 100%;
    padding: 14px;
    background: #ff6f00;
    border: none;
    border-radius: 4px;
    color: #0f0f11;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: brightness 0.2s ease;
  }

  .submit-btn:hover:not(:disabled) {
    filter: brightness(1.1);
  }

  .submit-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .error-alert {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
    padding: 12px;
    border-radius: 4px;
    margin-bottom: 20px;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.85rem;
  }

  .auth-link {
    text-align: center;
    margin-top: 24px;
    font-family: 'Chakra Petch', sans-serif;
    font-size: 0.85rem;
    color: #9a9a9e;
  }

  .auth-link a {
    color: #ff6f00;
    text-decoration: none;
  }

  .auth-link a:hover {
    text-decoration: underline;
  }
</style>

<div class="auth-card">
  <h1 class="auth-title">Create Account</h1>
  <p class="auth-subtitle">Start building autonomous supply chains</p>

  {#if error}
    <div class="error-alert">{error}</div>
  {/if}

  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label class="form-label" for="display_name">Display Name</label>
      <input
        type="text"
        id="display_name"
        class="form-input"
        bind:value={display_name}
        placeholder="Your name"
        required
      />
    </div>

    <div class="form-group">
      <label class="form-label" for="email">Email</label>
      <input
        type="email"
        id="email"
        class="form-input"
        bind:value={email}
        placeholder="you@example.com"
        required
      />
    </div>

    <div class="form-group">
      <label class="form-label" for="password">Password</label>
      <input
        type="password"
        id="password"
        class="form-input"
        bind:value={password}
        placeholder="At least 6 characters"
        required
      />
    </div>

    <div class="form-group">
      <label class="form-label" for="confirmPassword">Confirm Password</label>
      <input
        type="password"
        id="confirmPassword"
        class="form-input"
        bind:value={confirmPassword}
        placeholder="Re-enter your password"
        required
      />
    </div>

    <button type="submit" class="submit-btn" disabled={loading}>
      {loading ? 'Creating account...' : 'Create Account'}
    </button>
  </form>

  <div class="auth-link">
    Already have an account? <a href="/auth/login">Sign In</a>
  </div>
</div>
