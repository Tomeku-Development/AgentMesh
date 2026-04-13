<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { get } from 'svelte/store';
	import { connected } from '$lib/stores/websocket';
	import { activeAgentCount, totalAgents } from '$lib/stores/agents';
	import { completedOrders } from '$lib/stores/orders';
	import { messageCount } from '$lib/stores/websocket';
	import { isAuthenticated, currentUser, accessToken, logout } from '$lib/stores/auth';
	import { activeWorkspace, activeWorkspaceId } from '$lib/stores/workspace';
	import { getMe } from '$lib/api/auth';
	import { getWorkspace } from '$lib/api/workspaces';

	const tabs = [
		{ label: 'DASHBOARD', href: '/dashboard/' },
		{ label: 'AGENTS', href: '/dashboard/agents/' },
		{ label: 'ORDERS', href: '/dashboard/orders/' },
		{ label: 'LEDGER', href: '/dashboard/ledger/' },
		{ label: 'SETTINGS', href: '/dashboard/settings/' }
	];

	$: pathname = String($page.url.pathname);

	let authChecked = false;

	onMount(async () => {
		const token = get(accessToken);
		if (!token) {
			goto('/auth/login');
			return;
		}

		// Load user if not in store
		if (!get(currentUser)) {
			try {
				const user = await getMe();
				currentUser.set(user);
			} catch {
				goto('/auth/login');
				return;
			}
		}

		// Load workspace if ID exists but object doesn't
		const wsId = get(activeWorkspaceId);
		if (wsId && !get(activeWorkspace)) {
			try {
				const ws = await getWorkspace(wsId);
				activeWorkspace.set(ws);
			} catch {
				goto('/workspaces');
				return;
			}
		}

		// If no workspace selected, redirect to workspace selector
		if (!get(activeWorkspaceId)) {
			goto('/workspaces');
			return;
		}

		authChecked = true;
	});

	function handleLogout() {
		logout();
	}
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
			--green: #4ade80;
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

{#if authChecked}
	<div class="dashboard-shell">
		<!-- Top bar with logo and workspace -->
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
			<div class="top-bar-right">
				<div class="nav-stats">
					<span class="nav-stat">{$activeAgentCount}/{$totalAgents} Agents</span>
					<span class="nav-stat">{$completedOrders} Settled</span>
					<span class="nav-stat">{$messageCount} Msgs</span>
				</div>
				<div class="connection-badge" class:online={$connected} class:offline={!$connected}>
					<span class="connection-dot"></span>
					{$connected ? 'LIVE' : 'OFFLINE'}
				</div>
				<div class="workspace-badge">{$activeWorkspace?.name ?? 'WORKSPACE'}</div>
				<div class="user-menu">
					<span class="user-name">{$currentUser?.display_name ?? $currentUser?.email ?? ''}</span>
					<button class="logout-btn" on:click={handleLogout}>LOGOUT</button>
				</div>
			</div>
		</header>

		<!-- Tab navigation -->
		<nav class="tab-bar">
			{#each tabs as tab}
				<a
					href={tab.href}
					class="nav-link"
					class:active={tab.href === '/dashboard/' ? (pathname === '/dashboard/' || pathname === '/dashboard') : pathname.startsWith(tab.href) || pathname.startsWith(tab.href.slice(0, -1))}
				>
					{tab.label}
				</a>
			{/each}
		</nav>

		<!-- Page content -->
		<main class="content">
			<slot />
		</main>
	</div>
{:else}
	<div class="loading-screen">
		<div class="spinner"></div>
	</div>
{/if}

<style>
	.dashboard-shell {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
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
		gap: 20px;
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

	.nav-stats {
		display: flex;
		gap: 20px;
	}

	.nav-stat {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-dim);
		letter-spacing: 0.5px;
	}

	.connection-badge {
		display: flex;
		align-items: center;
		gap: 6px;
		font-family: var(--font-mono);
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 1.5px;
		padding: 5px 12px;
		border-radius: 2px;
	}

	.connection-badge.online {
		background: rgba(74, 222, 128, 0.1);
		color: var(--green);
		border: 1px solid rgba(74, 222, 128, 0.2);
	}

	.connection-badge.offline {
		background: rgba(239, 68, 68, 0.1);
		color: var(--red);
		border: 1px solid rgba(239, 68, 68, 0.2);
	}

	.connection-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: currentColor;
	}

	.connection-badge.online .connection-dot {
		box-shadow: 0 0 6px currentColor;
	}

	.workspace-badge {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 1.5px;
		color: var(--text-secondary);
		padding: 5px 12px;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 2px;
	}

	.user-menu {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.user-name {
		font-family: var(--font-body);
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	.logout-btn {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 1px;
		color: var(--text-dim);
		background: transparent;
		border: 1px solid var(--border);
		padding: 5px 10px;
		border-radius: 2px;
		cursor: pointer;
		transition: color 0.2s, border-color 0.2s;
	}

	.logout-btn:hover {
		color: var(--red);
		border-color: var(--red);
	}

	/* ── Loading screen ───────────────────────── */
	.loading-screen {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100vh;
		background: var(--bg);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* ── Tab bar ─────────────────────────────── */
	.tab-bar {
		display: flex;
		gap: 24px;
		padding: 0 28px;
		height: 44px;
		align-items: center;
		background: var(--bg);
		border-bottom: 1px solid var(--border);
		flex-shrink: 0;
	}

	.nav-link {
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 2px;
		color: var(--text-secondary);
		text-decoration: none;
		padding: 12px 0;
		border-bottom: 2px solid transparent;
		transition: color 0.2s;
	}

	.nav-link:hover {
		color: var(--text);
	}

	.nav-link.active {
		color: var(--text);
		border-bottom-color: var(--accent);
	}

	/* ── Content area ────────────────────────── */
	.content {
		flex: 1;
		overflow: auto;
		background: var(--bg);
	}
</style>
