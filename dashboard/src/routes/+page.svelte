<script lang="ts">
	import { onMount } from 'svelte';
	import { connect, connected, messageCount, events } from '$lib/stores/websocket';
	import { agentList, activeAgentCount, totalAgents } from '$lib/stores/agents';
	import { orderList, completedOrders } from '$lib/stores/orders';
	import { avgLatency, throughputSamples } from '$lib/stores/metrics';
	import AgentCard from '$lib/components/AgentCard.svelte';
	import OrderFlow from '$lib/components/OrderFlow.svelte';
	import MetricsPanel from '$lib/components/MetricsPanel.svelte';
	import EventLog from '$lib/components/EventLog.svelte';
	import ChaosControls from '$lib/components/ChaosControls.svelte';

	onMount(() => {
		const wsUrl = (typeof window !== 'undefined' && (window as any).__WS_URL) || 'ws://localhost:8080';
		connect(wsUrl);
	});
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

<div class="dashboard">
	<!-- Top navigation bar - matches Tashi nav style -->
	<nav class="topnav">
		<div class="nav-left">
			<div class="logo">
				<div class="logo-icon">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none">
						<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#ff6f00" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>
				<span class="logo-text">MESH</span>
			</div>
			<div class="nav-links">
				<span class="nav-link active">DASHBOARD</span>
				<span class="nav-link">AGENTS</span>
				<span class="nav-link">ORDERS</span>
				<span class="nav-link">LEDGER</span>
			</div>
		</div>
		<div class="nav-right">
			<div class="nav-stats">
				<span class="nav-stat">{$activeAgentCount}/{$totalAgents} Agents</span>
				<span class="nav-stat">{$completedOrders} Settled</span>
				<span class="nav-stat">{$messageCount} Msgs</span>
			</div>
			<div class="connection-badge" class:online={$connected} class:offline={!$connected}>
				<span class="connection-dot"></span>
				{$connected ? 'LIVE' : 'OFFLINE'}
			</div>
		</div>
	</nav>

	<!-- Main content -->
	<main>
		<!-- Metrics strip at top -->
		<section class="metrics-strip">
			<MetricsPanel />
		</section>

		<!-- Two-column layout -->
		<div class="content-grid">
			<!-- Left column -->
			<div class="column">
				<section class="panel">
					<div class="panel-header">
						<h2>Swarm Agents</h2>
						<span class="panel-badge">{$agentList.length}</span>
					</div>
					<div class="agent-grid">
						{#each $agentList as agent (agent.id)}
							<AgentCard {agent} />
						{/each}
						{#if $agentList.length === 0}
							<p class="empty-state">Waiting for agents to connect...</p>
						{/if}
					</div>
				</section>

				<section class="panel">
					<div class="panel-header">
						<h2>Chaos Controls</h2>
					</div>
					<ChaosControls agents={$agentList} />
				</section>
			</div>

			<!-- Right column -->
			<div class="column">
				<section class="panel">
					<div class="panel-header">
						<h2>Order Pipeline</h2>
						<span class="panel-badge">{$orderList.length}</span>
					</div>
					<OrderFlow orders={$orderList} />
				</section>

				<section class="panel events-panel">
					<div class="panel-header">
						<h2>Event Stream</h2>
						<span class="panel-badge">{$events.length}</span>
					</div>
					<EventLog events={$events} />
				</section>
			</div>
		</div>
	</main>
</div>

<style>
	.dashboard {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
	}

	/* ── Tashi-style navigation ──────────────── */
	.topnav {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0 28px;
		height: 56px;
		background: var(--bg);
		border-bottom: 1px solid var(--border);
		flex-shrink: 0;
	}
	.nav-left {
		display: flex;
		align-items: center;
		gap: 40px;
	}
	.logo {
		display: flex;
		align-items: center;
		gap: 10px;
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
	.nav-links {
		display: flex;
		gap: 24px;
	}
	.nav-link {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		font-weight: 500;
		letter-spacing: 1.5px;
		color: var(--text-secondary);
		cursor: pointer;
		transition: color 0.2s;
		padding: 4px 0;
	}
	.nav-link:hover {
		color: var(--text);
	}
	.nav-link.active {
		color: var(--text);
		border-bottom: 2px solid var(--accent);
		padding-bottom: 2px;
	}
	.nav-right {
		display: flex;
		align-items: center;
		gap: 24px;
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

	/* ── Main content ──────────────────────── */
	main {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		padding: 16px 20px;
		gap: 16px;
	}

	.metrics-strip {
		flex-shrink: 0;
	}

	.content-grid {
		flex: 1;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
		overflow: hidden;
	}

	.column {
		display: flex;
		flex-direction: column;
		gap: 16px;
		overflow: hidden;
	}

	/* ── Panel styling ─────────────────────── */
	.panel {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 16px 20px;
		overflow: auto;
		flex: 1;
	}
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 14px;
	}
	.panel-header h2 {
		font-family: var(--font-heading);
		font-size: 0.8rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 2px;
		color: var(--text-secondary);
	}
	.panel-badge {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		font-weight: 600;
		color: var(--accent);
		background: var(--accent-dim);
		padding: 2px 8px;
		border-radius: 2px;
		letter-spacing: 0.5px;
	}

	.agent-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 10px;
	}

	.events-panel {
		min-height: 200px;
	}

	.empty-state {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text-dim);
		padding: 20px;
		text-align: center;
	}
</style>
