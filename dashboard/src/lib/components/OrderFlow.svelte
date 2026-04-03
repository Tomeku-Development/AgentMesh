<script lang="ts">
	import type { OrderInfo } from '$lib/stores/orders';

	let { orders }: { orders: OrderInfo[] } = $props();

	const phases = ['bidding', 'negotiating', 'committed', 'fulfilling', 'shipping', 'inspecting', 'settled'];
	const phaseLabels = ['BID', 'NEG', 'CMT', 'FUL', 'SHP', 'INS', 'SET'];

	function phaseIndex(status: string): number {
		const idx = phases.indexOf(status);
		return idx >= 0 ? idx : 0;
	}

	function goodsShort(goods: string): string {
		return goods.replace('laptop_', '').replace('_', ' ');
	}
</script>

<div class="flow-container">
	{#if orders.length === 0}
		<div class="empty-state">
			<span class="empty-icon">&#9671;</span>
			<p>No active orders</p>
		</div>
	{/if}
	{#each orders.slice(0, 12) as order (order.id)}
		<div class="order-row" class:settled={order.status === 'settled'} class:failed={order.status === 'failed' || order.status === 'cancelled'}>
			<div class="order-meta">
				<span class="order-id">{order.id.slice(0, 8)}</span>
				<span class="order-goods">{order.quantity}x {goodsShort(order.goods)}</span>
				{#if order.agreedPrice > 0}
					<span class="order-price">${order.agreedPrice.toFixed(0)}/u</span>
				{/if}
			</div>
			<div class="pipeline">
				{#each phases as phase, i}
					<div class="phase-group">
						<div
							class="phase-node"
							class:complete={phaseIndex(order.status) > i}
							class:active={phase === order.status}
							class:failed={order.status === 'failed' || order.status === 'cancelled'}
						></div>
						{#if i < phases.length - 1}
							<div
								class="phase-connector"
								class:filled={phaseIndex(order.status) > i}
							></div>
						{/if}
					</div>
				{/each}
			</div>
			<div class="order-status" class:status-settled={order.status === 'settled'} class:status-failed={order.status === 'failed'}>
				{order.status}
			</div>
		</div>
	{/each}
</div>

<style>
	.flow-container {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.order-row {
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 8px 12px;
		background: var(--bg-surface, #232427);
		border: 1px solid var(--border, rgba(255,255,255,0.08));
		border-radius: 3px;
		transition: border-color 0.2s;
	}
	.order-row:hover {
		border-color: var(--border-strong, rgba(255,255,255,0.14));
	}
	.order-row.settled {
		border-left: 2px solid #4ade80;
	}
	.order-row.failed {
		border-left: 2px solid #ef4444;
		opacity: 0.6;
	}

	.order-meta {
		min-width: 130px;
	}
	.order-id {
		display: block;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.7rem;
		font-weight: 600;
		color: #ff6f00;
		letter-spacing: 0.5px;
	}
	.order-goods {
		display: block;
		font-family: 'Chakra Petch', sans-serif;
		font-size: 0.7rem;
		color: var(--text-secondary, #9a9a9e);
		text-transform: capitalize;
	}
	.order-price {
		display: block;
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.6rem;
		color: var(--text-dim, #6b6b70);
	}

	.pipeline {
		display: flex;
		align-items: center;
		flex: 1;
	}
	.phase-group {
		display: flex;
		align-items: center;
		flex: 1;
	}
	.phase-node {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: rgba(255, 255, 255, 0.1);
		border: 1.5px solid rgba(255, 255, 255, 0.15);
		flex-shrink: 0;
		transition: all 0.3s;
	}
	.phase-node.complete {
		background: #4ade80;
		border-color: #4ade80;
	}
	.phase-node.active {
		background: #ff6f00;
		border-color: #ff6f00;
		box-shadow: 0 0 8px rgba(255, 111, 0, 0.5);
	}
	.phase-node.failed {
		background: #ef4444;
		border-color: #ef4444;
	}
	.phase-connector {
		flex: 1;
		height: 1.5px;
		background: rgba(255, 255, 255, 0.08);
		margin: 0 2px;
		transition: background 0.3s;
	}
	.phase-connector.filled {
		background: #4ade80;
	}

	.order-status {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.6rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 1px;
		min-width: 75px;
		text-align: right;
		color: var(--text-dim, #6b6b70);
	}
	.status-settled {
		color: #4ade80;
	}
	.status-failed {
		color: #ef4444;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 32px;
		color: var(--text-dim, #6b6b70);
	}
	.empty-icon {
		font-size: 1.5rem;
		margin-bottom: 8px;
		opacity: 0.4;
	}
	.empty-state p {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.8rem;
	}
</style>
