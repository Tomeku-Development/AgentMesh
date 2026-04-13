<script lang="ts">
	import { onMount } from 'svelte';
	import { connect } from '$lib/stores/websocket';
	import { agentList } from '$lib/stores/agents';
	import { orderList } from '$lib/stores/orders';
	import { events } from '$lib/stores/websocket';
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
</style>
