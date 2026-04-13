<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { connect } from '$lib/stores/websocket';
	import { agentList } from '$lib/stores/agents';
	import { orderList } from '$lib/stores/orders';
	import { events } from '$lib/stores/websocket';
	import AgentCard from '$lib/components/AgentCard.svelte';
	import OrderFlow from '$lib/components/OrderFlow.svelte';
	import MetricsPanel from '$lib/components/MetricsPanel.svelte';
	import EventLog from '$lib/components/EventLog.svelte';
	import ChaosControls from '$lib/components/ChaosControls.svelte';

	let demoActive = false;

	onMount(async () => {
		if (!browser) return;

		const wsUrl = (typeof window !== 'undefined' && (window as any).__WS_URL) || 'ws://localhost:8080';
		connect(wsUrl);

		// After a delay, if not connected, auto-start demo mode
		setTimeout(async () => {
			const { connected } = await import('$lib/stores/websocket');
			const { get } = await import('svelte/store');
			if (!get(connected)) {
				const { startDemo } = await import('$lib/demo/demoEngine');
				const { agents } = await import('$lib/stores/agents');
				const { orders } = await import('$lib/stores/orders');
				const { events: wsEvents, connected: wsConnected, messageCount } = await import('$lib/stores/websocket');
				const { latencySamples, throughputSamples } = await import('$lib/stores/metrics');
				startDemo({
					agents,
					orders,
					events: wsEvents,
					connected: wsConnected,
					messageCount,
					latencySamples,
					throughputSamples
				});
				demoActive = true;
			}
		}, 3000);
	});

	onDestroy(() => {
		if (browser && demoActive) {
			import('$lib/demo/demoEngine').then(m => m.stopDemo());
		}
	});

	function dismissDemo() {
		if (browser) {
			import('$lib/demo/demoEngine').then(m => m.stopDemo());
			demoActive = false;
		}
	}
</script>

{#if demoActive}
	<div class="demo-banner">
		<span class="demo-badge">DEMO MODE</span>
		<span class="demo-text">Viewing simulated data — connect a backend for live trading</span>
		<button class="demo-dismiss" on:click={dismissDemo}>×</button>
	</div>
{/if}

<!-- Main content -->
<div class="dashboard-content">
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
				<div class="agent-grid" id="tour-agents">
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
</div>

<style>
	.dashboard-content {
		display: flex;
		flex-direction: column;
		height: 100%;
		padding: 16px 20px;
		gap: 16px;
		overflow: hidden;
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

	.demo-banner {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 8px 16px;
		background: rgba(255, 111, 0, 0.1);
		border: 1px solid rgba(255, 111, 0, 0.3);
		border-radius: 8px;
		margin: 16px 20px 0;
	}

	.demo-badge {
		padding: 2px 8px;
		background: #ff6f00;
		color: #0f0f11;
		border-radius: 4px;
		font-family: 'Chakra Petch', sans-serif;
		font-weight: 700;
		font-size: 0.75rem;
		letter-spacing: 0.05em;
	}

	.demo-text {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.8rem;
		color: #888;
	}

	.demo-dismiss {
		margin-left: auto;
		background: none;
		border: none;
		color: #666;
		font-size: 1.2rem;
		cursor: pointer;
	}

	.demo-dismiss:hover {
		color: #ff6f00;
	}
</style>
