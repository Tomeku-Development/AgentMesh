<script lang="ts">
	import { onMount } from 'svelte';
	import { getOrders, getOrderEvents } from '$lib/api/orders';
	import { activeWorkspaceId } from '$lib/stores/workspace';
	import type { Order, OrderEvent } from '$lib/types/api';

	$: workspaceId = $activeWorkspaceId || 'default';
	const LIMIT = 20;

	// State
	let orders: Order[] = [];
	let total = 0;
	let loading = true;
	let error: string | null = null;
	let selectedStatus = '';
	let page = 0;
	let expandedOrderId: string | null = null;
	let orderEvents: Map<string, OrderEvent[]> = new Map();
	let loadingEvents = false;

	const statuses = [
		{ value: '', label: 'All' },
		{ value: 'requested', label: 'Requested' },
		{ value: 'bidding', label: 'Bidding' },
		{ value: 'awarded', label: 'Awarded' },
		{ value: 'executing', label: 'Executing' },
		{ value: 'completed', label: 'Completed' },
		{ value: 'disputed', label: 'Disputed' }
	];

	const statusColors: Record<string, string> = {
		requested: '#9a9a9e',
		bidding: '#60a5fa',
		awarded: '#fbbf24',
		executing: '#ff6f00',
		completed: '#4ade80',
		disputed: '#ef4444'
	};

	async function fetchOrders() {
		loading = true;
		error = null;
		try {
			const response = await getOrders(workspaceId, {
				status: selectedStatus || undefined,
				limit: LIMIT,
				offset: page * LIMIT
			});
			orders = response.orders;
			total = response.total;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load orders';
		} finally {
			loading = false;
		}
	}

	async function toggleOrderExpand(orderId: string) {
		if (expandedOrderId === orderId) {
			expandedOrderId = null;
			return;
		}
		expandedOrderId = orderId;
		
		if (!orderEvents.has(orderId)) {
			loadingEvents = true;
			try {
				const events = await getOrderEvents(workspaceId, orderId);
				orderEvents.set(orderId, events);
			} catch (e) {
				console.error('Failed to load order events:', e);
				orderEvents.set(orderId, []);
			} finally {
				loadingEvents = false;
			}
		}
	}

	function formatPrice(price: number | null): string {
		if (price === null) return '—';
		return `${price.toFixed(2)} MESH`;
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function truncateId(id: string): string {
		if (id.length <= 12) return id;
		return `${id.slice(0, 8)}...${id.slice(-4)}`;
	}

	function handleStatusChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		selectedStatus = target.value;
		page = 0;
		fetchOrders();
	}

	function prevPage() {
		if (page > 0) {
			page--;
			fetchOrders();
		}
	}

	function nextPage() {
		if ((page + 1) * LIMIT < total) {
			page++;
			fetchOrders();
		}
	}

	$: showingFrom = page * LIMIT + 1;
	$: showingTo = Math.min((page + 1) * LIMIT, total);
	$: hasPrev = page > 0;
	$: hasNext = (page + 1) * LIMIT < total;

	onMount(() => {
		fetchOrders();
	});
</script>

<svelte:head>
	<title>Orders — MESH Dashboard</title>
</svelte:head>

<div class="orders-page">
	<!-- Page header -->
	<header class="page-header">
		<div class="header-content">
			<h1>Orders</h1>
			<p class="subtitle">Track procurement orders through the supply chain protocol</p>
		</div>
		<div class="order-count-badge">
			<span class="count">{total}</span>
			<span class="label">Total</span>
		</div>
	</header>

	<!-- Filter bar -->
	<div class="filter-bar">
		<div class="filter-group">
			<label for="status-filter">Status</label>
			<select id="status-filter" bind:value={selectedStatus} on:change={handleStatusChange}>
				{#each statuses as status}
					<option value={status.value}>{status.label}</option>
				{/each}
			</select>
		</div>
	</div>

	<!-- Loading state -->
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<span>Loading orders...</span>
		</div>

	<!-- Error state -->
	{:else if error}
		<div class="error-state">
			<div class="error-icon">⚠</div>
			<p class="error-message">{error}</p>
			<button class="retry-btn" on:click={fetchOrders}>Retry</button>
		</div>

	<!-- Empty state -->
	{:else if orders.length === 0}
		<div class="empty-state">
			<div class="empty-icon">📋</div>
			<h3>No orders found</h3>
			<p>Orders will appear here once agents start trading.</p>
		</div>

	<!-- Orders table -->
	{:else}
		<div class="table-container">
			<table class="orders-table">
				<thead>
					<tr>
						<th>Order ID</th>
						<th>Goods</th>
						<th>Quantity</th>
						<th>Max Price</th>
						<th>Status</th>
						<th>Winner Supplier</th>
						<th>Agreed Price</th>
						<th>Bids</th>
						<th>Created</th>
					</tr>
				</thead>
				<tbody>
					{#each orders as order (order.id)}
						<tr class:expanded={expandedOrderId === order.id}>
							<td class="order-id" on:click={() => toggleOrderExpand(order.id)}>
								<span class="expand-icon" class:rotated={expandedOrderId === order.id}>▶</span>
								{truncateId(order.id)}
							</td>
							<td>{order.goods}</td>
							<td>{order.quantity}</td>
							<td class="mono">{formatPrice(order.max_price_per_unit)}</td>
							<td>
								<span class="status-badge" style="background-color: {statusColors[order.current_status] || '#9a9a9e'}">
									{order.current_status}
								</span>
							</td>
							<td class="mono">{order.winner_supplier_id ? truncateId(order.winner_supplier_id) : '—'}</td>
							<td class="mono">{formatPrice(order.agreed_price_per_unit)}</td>
							<td>{order.bid_count}</td>
							<td>{formatDate(order.created_at)}</td>
						</tr>
						{#if expandedOrderId === order.id}
							<tr class="event-row">
								<td colspan="9">
									<div class="event-timeline">
										{#if loadingEvents}
											<div class="events-loading">Loading events...</div>
										{:else if orderEvents.get(order.id)?.length === 0}
											<div class="no-events">No events recorded</div>
										{:else}
											{#each orderEvents.get(order.id) || [] as event (event.id)}
												<div class="timeline-event">
													<div class="event-dot" style="background-color: {statusColors[event.event_type] || 'var(--accent)'}"></div>
													<div class="event-content">
														<span class="event-type">{event.event_type}</span>
														<span class="event-agent">{truncateId(event.agent_id)}</span>
														<span class="event-time">{formatDate(event.occurred_at)}</span>
														{#if event.payload_json}
															<pre class="event-payload">{event.payload_json}</pre>
														{/if}
													</div>
												</div>
											{/each}
										{/if}
									</div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		<div class="pagination">
			<span class="pagination-info">Showing {showingFrom}-{showingTo} of {total}</span>
			<div class="pagination-controls">
				<button class="pagination-btn" disabled={!hasPrev} on:click={prevPage}>Previous</button>
				<button class="pagination-btn" disabled={!hasNext} on:click={nextPage}>Next</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.orders-page {
		padding: 24px 28px;
		height: 100%;
		display: flex;
		flex-direction: column;
		gap: 20px;
		overflow: auto;
	}

	/* ── Page Header ─────────────────────────────────────── */
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
	}

	.header-content h1 {
		font-family: var(--font-heading);
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--text);
		margin: 0;
		letter-spacing: 1px;
	}

	.subtitle {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
		margin-top: 4px;
	}

	.order-count-badge {
		display: flex;
		flex-direction: column;
		align-items: center;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 8px 16px;
	}

	.order-count-badge .count {
		font-family: var(--font-mono);
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--accent);
	}

	.order-count-badge .label {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	/* ── Filter Bar ──────────────────────────────────────── */
	.filter-bar {
		display: flex;
		gap: 16px;
		align-items: center;
	}

	.filter-group {
		display: flex;
		gap: 8px;
		align-items: center;
	}

	.filter-group label {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.filter-group select {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 8px 12px;
		color: var(--text);
		font-family: var(--font-mono);
		font-size: 0.8rem;
		cursor: pointer;
		outline: none;
		transition: border-color 0.2s;
	}

	.filter-group select:hover {
		border-color: var(--text-dim);
	}

	.filter-group select:focus {
		border-color: var(--accent);
	}

	/* ── Loading State ───────────────────────────────────── */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 16px;
		padding: 60px;
		color: var(--text-secondary);
		font-family: var(--font-mono);
		font-size: 0.85rem;
	}

	.spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* ── Error State ─────────────────────────────────────── */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
		padding: 40px;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		border-radius: 4px;
	}

	.error-icon {
		font-size: 2rem;
	}

	.error-message {
		font-family: var(--font-mono);
		font-size: 0.85rem;
		color: var(--red);
		text-align: center;
	}

	.retry-btn {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		color: var(--text);
		font-family: var(--font-mono);
		font-size: 0.75rem;
		padding: 8px 16px;
		border-radius: 3px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.retry-btn:hover {
		background: var(--accent);
		border-color: var(--accent);
	}

	/* ── Empty State ─────────────────────────────────────── */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
		padding: 60px;
		color: var(--text-dim);
	}

	.empty-icon {
		font-size: 3rem;
		opacity: 0.5;
	}

	.empty-state h3 {
		font-family: var(--font-heading);
		font-size: 1.1rem;
		color: var(--text-secondary);
		margin: 0;
	}

	.empty-state p {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		margin: 0;
	}

	/* ── Table ────────────────────────────────────────────── */
	.table-container {
		flex: 1;
		overflow: auto;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
	}

	.orders-table {
		width: 100%;
		border-collapse: collapse;
		font-family: var(--font-mono);
		font-size: 0.8rem;
	}

	.orders-table thead {
		background: var(--bg-elevated);
		position: sticky;
		top: 0;
		z-index: 1;
	}

	.orders-table th {
		text-align: left;
		padding: 12px 16px;
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 1.5px;
		color: var(--text-secondary);
		border-bottom: 1px solid var(--border);
		white-space: nowrap;
	}

	.orders-table td {
		padding: 12px 16px;
		border-bottom: 1px solid var(--border);
		color: var(--text);
		vertical-align: middle;
	}

	.orders-table tbody tr:hover {
		background: rgba(255, 111, 0, 0.05);
	}

	.orders-table tbody tr.expanded {
		background: rgba(255, 111, 0, 0.08);
	}

	.order-id {
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.expand-icon {
		font-size: 0.65rem;
		color: var(--text-dim);
		transition: transform 0.2s;
	}

	.expand-icon.rotated {
		transform: rotate(90deg);
		color: var(--accent);
	}

	.mono {
		font-family: var(--font-mono);
	}

	/* ── Status Badge ─────────────────────────────────────── */
	.status-badge {
		display: inline-block;
		padding: 4px 10px;
		border-radius: 2px;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #0f0f11;
	}

	/* ── Event Timeline ───────────────────────────────────── */
	.event-row td {
		padding: 0;
		background: rgba(0, 0, 0, 0.2);
	}

	.event-timeline {
		padding: 16px 24px 16px 60px;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.events-loading,
	.no-events {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-dim);
		padding: 8px;
	}

	.timeline-event {
		display: flex;
		gap: 12px;
		position: relative;
	}

	.timeline-event::before {
		content: '';
		position: absolute;
		left: 4px;
		top: 16px;
		bottom: -12px;
		width: 1px;
		background: var(--border);
	}

	.timeline-event:last-child::before {
		display: none;
	}

	.event-dot {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		flex-shrink: 0;
		margin-top: 4px;
	}

	.event-content {
		display: flex;
		flex-wrap: wrap;
		gap: 8px 16px;
		align-items: flex-start;
		flex: 1;
	}

	.event-type {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--text);
		text-transform: uppercase;
	}

	.event-agent {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--accent);
	}

	.event-time {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-dim);
	}

	.event-payload {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-secondary);
		background: var(--bg-surface);
		padding: 8px 12px;
		border-radius: 3px;
		overflow-x: auto;
		width: 100%;
		margin: 4px 0;
		white-space: pre-wrap;
		word-break: break-all;
	}

	/* ── Pagination ───────────────────────────────────────── */
	.pagination {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-top: 12px;
	}

	.pagination-info {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	.pagination-controls {
		display: flex;
		gap: 8px;
	}

	.pagination-btn {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		color: var(--text);
		font-family: var(--font-mono);
		font-size: 0.75rem;
		padding: 6px 14px;
		border-radius: 3px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.pagination-btn:hover:not(:disabled) {
		background: var(--accent);
		border-color: var(--accent);
		color: #0f0f11;
	}

	.pagination-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	/* ── Responsive ───────────────────────────────────────── */
	@media (max-width: 1024px) {
		.orders-page {
			padding: 16px;
		}

		.orders-table th,
		.orders-table td {
			padding: 10px 12px;
		}
	}

	@media (max-width: 768px) {
		.page-header {
			flex-direction: column;
			gap: 16px;
		}

		.table-container {
			overflow-x: auto;
		}

		.orders-table {
			min-width: 800px;
		}

		.pagination {
			flex-direction: column;
			gap: 12px;
		}
	}
</style>
