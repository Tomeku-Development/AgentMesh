<script lang="ts">
	import type { AgentInfo } from '$lib/stores/agents';
	import { roleColor, statusColor, roleIcon } from '$lib/utils/colors';

	export let agent: AgentInfo;

	function uptimeStr(seconds: number): string {
		if (seconds < 60) return `${seconds.toFixed(0)}s`;
		return `${(seconds / 60).toFixed(1)}m`;
	}
</script>

<div class="card" class:dead={agent.status === 'dead'} class:suspect={agent.status === 'suspect'}>
	<div class="card-top">
		<div class="role-badge" style="background: {roleColor(agent.role)}">
			{roleIcon(agent.role)}
		</div>
		<div class="card-info">
			<span class="role-name">{agent.role}</span>
			<span class="agent-id">{agent.id.slice(0, 12)}</span>
		</div>
		<div class="status-indicator" style="background: {statusColor(agent.status)}">
			{agent.status}
		</div>
	</div>
	<div class="card-stats">
		<div class="stat">
			<span class="stat-value">{(agent.load * 100).toFixed(0)}%</span>
			<span class="stat-label">LOAD</span>
		</div>
		<div class="stat">
			<span class="stat-value">{agent.activeOrders}</span>
			<span class="stat-label">ORDERS</span>
		</div>
		<div class="stat">
			<span class="stat-value">{uptimeStr(agent.uptime)}</span>
			<span class="stat-label">UPTIME</span>
		</div>
	</div>
	<!-- Load bar -->
	<div class="load-track">
		<div
			class="load-fill"
			style="width: {agent.load * 100}%; background: {agent.load > 0.8 ? '#ef4444' : agent.load > 0.5 ? '#fbbf24' : '#4ade80'}"
		></div>
	</div>
</div>

<style>
	.card {
		background: var(--bg-surface, #232427);
		border: 1px solid var(--border, rgba(255,255,255,0.08));
		border-radius: 3px;
		padding: 14px 16px 10px;
		transition: border-color 0.2s, transform 0.15s;
	}
	.card:hover {
		border-color: var(--border-strong, rgba(255,255,255,0.14));
		transform: translateY(-1px);
	}
	.card.dead {
		opacity: 0.4;
		border-color: rgba(239, 68, 68, 0.3);
	}
	.card.suspect {
		border-color: rgba(239, 68, 68, 0.4);
	}

	.card-top {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-bottom: 12px;
	}
	.role-badge {
		width: 28px;
		height: 28px;
		border-radius: 3px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: 'Chakra Petch', sans-serif;
		font-weight: 700;
		font-size: 0.75rem;
		color: #0f0f11;
		flex-shrink: 0;
	}
	.card-info {
		flex: 1;
		min-width: 0;
	}
	.role-name {
		display: block;
		font-family: 'Chakra Petch', sans-serif;
		font-weight: 600;
		font-size: 0.8rem;
		text-transform: capitalize;
		color: var(--text, #f4f4f5);
		letter-spacing: 0.5px;
	}
	.agent-id {
		display: block;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.6rem;
		color: var(--text-dim, #6b6b70);
		letter-spacing: 0.5px;
	}
	.status-indicator {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.55rem;
		font-weight: 600;
		letter-spacing: 1px;
		text-transform: uppercase;
		padding: 3px 8px;
		border-radius: 2px;
		color: #0f0f11;
		flex-shrink: 0;
	}

	.card-stats {
		display: flex;
		gap: 0;
		margin-bottom: 10px;
	}
	.stat {
		flex: 1;
		text-align: center;
	}
	.stat-value {
		display: block;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--text, #f4f4f5);
	}
	.stat-label {
		display: block;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.5rem;
		letter-spacing: 1.5px;
		color: var(--text-dim, #6b6b70);
		margin-top: 2px;
	}

	.load-track {
		width: 100%;
		height: 3px;
		background: rgba(255, 255, 255, 0.06);
		border-radius: 1px;
		overflow: hidden;
	}
	.load-fill {
		height: 100%;
		border-radius: 1px;
		transition: width 0.4s ease;
	}
</style>
