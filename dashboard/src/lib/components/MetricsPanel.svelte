<script lang="ts">
	import { messageCount } from '$lib/stores/websocket';
	import { activeAgentCount, totalAgents } from '$lib/stores/agents';
	import { completedOrders } from '$lib/stores/orders';
	import { avgLatency, throughputSamples } from '$lib/stores/metrics';
</script>

<div class="metrics-row">
	<div class="metric">
		<span class="metric-value accent">{$activeAgentCount}</span>
		<span class="metric-label">Active Agents</span>
	</div>
	<div class="metric-divider"></div>
	<div class="metric">
		<span class="metric-value">{$totalAgents}</span>
		<span class="metric-label">Total Agents</span>
	</div>
	<div class="metric-divider"></div>
	<div class="metric">
		<span class="metric-value accent">{$completedOrders}</span>
		<span class="metric-label">Orders Settled</span>
	</div>
	<div class="metric-divider"></div>
	<div class="metric">
		<span class="metric-value">{$messageCount}</span>
		<span class="metric-label">Messages</span>
	</div>
	<div class="metric-divider"></div>
	<div class="metric">
		<span class="metric-value">{$avgLatency.toFixed(1)}<span class="metric-unit">ms</span></span>
		<span class="metric-label">Avg Latency</span>
	</div>
	<div class="metric-divider"></div>
	<div class="metric">
		<span class="metric-value">
			{$throughputSamples.length > 0 ? $throughputSamples[$throughputSamples.length - 1].toFixed(1) : '0.0'}<span class="metric-unit">/s</span>
		</span>
		<span class="metric-label">Throughput</span>
	</div>
</div>

<style>
	.metrics-row {
		display: flex;
		align-items: center;
		gap: 0;
		background: var(--bg-elevated, #1b1c1e);
		border: 1px solid var(--border, rgba(255,255,255,0.08));
		border-radius: 3px;
		padding: 14px 8px;
	}
	.metric {
		flex: 1;
		text-align: center;
		padding: 0 12px;
	}
	.metric-divider {
		width: 1px;
		height: 32px;
		background: var(--border, rgba(255,255,255,0.08));
		flex-shrink: 0;
	}
	.metric-value {
		display: block;
		font-family: 'Chakra Petch', sans-serif;
		font-size: 1.6rem;
		font-weight: 700;
		color: var(--text, #f4f4f5);
		line-height: 1;
	}
	.metric-value.accent {
		color: #ff6f00;
	}
	.metric-unit {
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--text-dim, #6b6b70);
	}
	.metric-label {
		display: block;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.55rem;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 1.5px;
		color: var(--text-dim, #6b6b70);
		margin-top: 4px;
	}
</style>
