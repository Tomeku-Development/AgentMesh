<script lang="ts">
	import { currentUser, logout } from '$lib/stores/auth';
</script>

<svelte:head>
	<style>
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
			--red: #ef4444;
			--font-heading: 'Chakra Petch', sans-serif;
			--font-mono: 'IBM Plex Mono', monospace;
			--font-body: 'Chakra Petch', sans-serif;
		}
		* { box-sizing: border-box; margin: 0; padding: 0; }
		body {
			background: var(--bg);
			color: var(--text);
			font-family: var(--font-body);
			-webkit-font-smoothing: antialiased;
			-moz-osx-font-smoothing: grayscale;
		}
	</style>
</svelte:head>

<div class="workspaces-shell">
	<!-- Top bar with logo, greeting, and logout -->
	<header class="top-bar">
		<div class="top-bar-left">
			<a href="/" class="logo">
				<div class="logo-icon">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none">
						<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#ff6f00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>
				<span class="logo-text">MESH</span>
			</a>
		</div>
		{#if $currentUser}
			<div class="user-greeting">
				Hello, {$currentUser.display_name}
			</div>
		{/if}
		<div class="top-bar-right">
			<button class="logout-link" on:click={logout}>
				Logout
			</button>
		</div>
	</header>

	<!-- Page content -->
	<main class="content">
		<slot />
	</main>
</div>

<style>
	.workspaces-shell {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		background: var(--bg);
	}

	/* ── Top bar ─────────────────────────────── */
	.top-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0 28px;
		height: 56px;
		background: var(--bg-elevated);
		border-bottom: 1px solid var(--border);
		flex-shrink: 0;
	}

	.top-bar-left {
		display: flex;
		align-items: center;
	}

	.top-bar-right {
		display: flex;
		align-items: center;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 10px;
		text-decoration: none;
	}

	.logo-icon {
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.logo-text {
		font-family: var(--font-heading);
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--text);
		letter-spacing: 3px;
	}

	.user-greeting {
		font-family: var(--font-body);
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.logout-link {
		font-family: var(--font-body);
		font-size: 0.85rem;
		color: var(--text-secondary);
		background: transparent;
		border: none;
		cursor: pointer;
		padding: 8px 16px;
		border-radius: 4px;
		transition: color 0.2s, background 0.2s;
	}

	.logout-link:hover {
		color: var(--text);
		background: var(--bg-surface);
	}

	/* ── Content area ────────────────────────── */
	.content {
		flex: 1;
		padding: 48px 28px;
		background: var(--bg);
	}
</style>
