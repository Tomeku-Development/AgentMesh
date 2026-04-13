<script lang="ts">
	import type { MeshEvent } from '$lib/stores/websocket';

	export let events: MeshEvent[];

	function topicShort(topic: string): string {
		return topic.replace('mesh/', '');
	}

	function timeStr(ts: number): string {
		return new Date(ts * 1000).toLocaleTimeString('en-US', { hour12: false, fractionalSecondDigits: 1 });
	}

	function topicCategory(topic: string): string {
		if (topic.includes('discovery')) return 'disc';
		if (topic.includes('orders')) return 'order';
		if (topic.includes('shipping')) return 'ship';
		if (topic.includes('quality')) return 'qual';
		if (topic.includes('health')) return 'health';
		if (topic.includes('ledger')) return 'ledger';
		if (topic.includes('reputation')) return 'rep';
		if (topic.includes('market')) return 'market';
		return 'sys';
	}

	function categoryColor(cat: string): string {
		const colors: Record<string, string> = {
			disc: '#4ade80',
			order: '#ff6f00',
			ship: '#60a5fa',
			qual: '#c084fc',
			health: '#ef4444',
			ledger: '#fbbf24',
			rep: '#38bdf8',
			market: '#fbbf24',
			sys: '#6b6b70',
		};
		return colors[cat] || '#6b6b70';
	}
</script>

<div class="log-container">
	{#each events.slice(0, 50) as event, i (event.timestamp + event.topic + i)}
		{@const cat = topicCategory(event.topic)}
		<div class="log-entry">
			<span class="log-time">{timeStr(event.timestamp)}</span>
			<span class="log-category" style="color: {categoryColor(cat)}">{cat}</span>
			<span class="log-topic">{topicShort(event.topic)}</span>
			<span class="log-sender">{event.payload?.header?.sender_role || ''}</span>
		</div>
	{/each}
	{#if events.length === 0}
		<div class="empty-state">
			<p>Waiting for events...</p>
		</div>
	{/if}
</div>

<style>
	.log-container {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.65rem;
		max-height: 260px;
		overflow-y: auto;
	}
	/* Scrollbar styling */
	.log-container::-webkit-scrollbar {
		width: 4px;
	}
	.log-container::-webkit-scrollbar-track {
		background: transparent;
	}
	.log-container::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 2px;
	}

	.log-entry {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 4px 8px;
		border-bottom: 1px solid rgba(255, 255, 255, 0.03);
		transition: background 0.15s;
	}
	.log-entry:hover {
		background: rgba(255, 255, 255, 0.02);
	}
	.log-time {
		color: var(--text-dim, #6b6b70);
		min-width: 80px;
		font-size: 0.6rem;
	}
	.log-category {
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 1px;
		min-width: 45px;
		font-size: 0.55rem;
	}
	.log-topic {
		color: var(--text-secondary, #9a9a9e);
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.log-sender {
		color: var(--text-dim, #6b6b70);
		min-width: 65px;
		text-align: right;
		text-transform: capitalize;
		font-size: 0.6rem;
	}
	.empty-state {
		padding: 24px;
		text-align: center;
		color: var(--text-dim, #6b6b70);
	}
</style>
