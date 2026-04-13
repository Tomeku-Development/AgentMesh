<script lang="ts">
	import { onMount } from 'svelte';
	import { getTransactions } from '$lib/api/ledger';
	import type { LedgerEntry, LedgerListResponse } from '$lib/types/api';

	// State
	let transactions: LedgerEntry[] = [];
	let loading = false;
	let error: string | null = null;
	let typeFilter = 'all';
	let page = 1;
	const limit = 25;
	let total = 0;

	const workspaceId = 'default';

	// Transaction type options
	const txTypes = [
		{ value: 'all', label: 'All' },
		{ value: 'transfer', label: 'Transfer' },
		{ value: 'escrow_lock', label: 'Escrow Lock' },
		{ value: 'escrow_release', label: 'Escrow Release' },
		{ value: 'settlement', label: 'Settlement' },
		{ value: 'burn', label: 'Burn' }
	];

	// Type badge colors
	const typeColors: Record<string, string> = {
		transfer: '#60a5fa',
		escrow_lock: '#fbbf24',
		escrow_release: '#4ade80',
		settlement: '#ff6f00',
		burn: '#ef4444'
	};

	// Computed summary stats
	$: totalVolume = transactions.reduce((sum, tx) => sum + tx.amount, 0);
	$: uniqueAgents = new Set([
		...transactions.map(tx => tx.from_agent),
		...transactions.map(tx => tx.to_agent)
	]).size;

	// Filtered transactions
	$: filteredTransactions = typeFilter === 'all' 
		? transactions 
		: transactions.filter(tx => tx.tx_type === typeFilter);

	// Paginated transactions
	$: paginatedTransactions = filteredTransactions.slice((page - 1) * limit, page * limit);
	$: totalFiltered = filteredTransactions.length;
	$: startIdx = (page - 1) * limit + 1;
	$: endIdx = Math.min(page * limit, totalFiltered);
	$: totalPages = Math.ceil(totalFiltered / limit);

	onMount(async () => {
		await loadTransactions();
	});

	async function loadTransactions() {
		loading = true;
		error = null;
		try {
			const response: LedgerListResponse = await getTransactions(workspaceId, { limit: 1000 });
			transactions = response.entries;
			total = response.total;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load transactions';
		} finally {
			loading = false;
		}
	}

	function formatAmount(amount: number, type: string): string {
		const formatted = amount.toFixed(2);
		if (type === 'burn') return `-${formatted}`;
		return formatted;
	}

	function getAmountColor(type: string): string {
		if (type === 'burn') return 'var(--red)';
		if (type === 'transfer' || type === 'escrow_release') return 'var(--green)';
		return 'var(--text)';
	}

	function truncateId(id: string, length = 12): string {
		if (id.length <= length) return id;
		return id.slice(0, length) + '...';
	}

	function formatTimestamp(timestamp: string): string {
		const date = new Date(timestamp);
		return date.toLocaleString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatTxType(type: string): string {
		return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
	}

	function goToPage(newPage: number) {
		if (newPage >= 1 && newPage <= totalPages) {
			page = newPage;
		}
	}

	function handleFilterChange() {
		page = 1;
	}
</script>

<svelte:head>
	<title>Ledger — MESH Dashboard</title>
</svelte:head>

<div class="ledger-page">
	<!-- Page Header -->
	<header class="page-header">
		<h1 class="page-title">Ledger</h1>
		<p class="page-subtitle">Double-entry transaction ledger for MESH_CREDIT operations</p>
	</header>

	<!-- Summary Stats -->
	<div class="stats-row">
		<div class="stat-card">
			<div class="stat-value" style="color: var(--accent);">{totalFiltered}</div>
			<div class="stat-label">Total Transactions</div>
		</div>
		<div class="stat-card">
			<div class="stat-value" style="color: var(--accent);">{totalVolume.toFixed(2)}</div>
			<div class="stat-label">Total Volume</div>
		</div>
		<div class="stat-card">
			<div class="stat-value" style="color: var(--accent);">{uniqueAgents}</div>
			<div class="stat-label">Unique Agents</div>
		</div>
	</div>

	<!-- Filter Bar -->
	<div class="filter-bar">
		<div class="filter-group">
			<label for="type-filter">Transaction Type</label>
			<select 
				id="type-filter" 
				bind:value={typeFilter} 
				on:change={handleFilterChange}
				class="filter-select"
			>
				{#each txTypes as type}
					<option value={type.value}>{type.label}</option>
				{/each}
			</select>
		</div>
	</div>

	<!-- Loading State -->
	{#if loading}
		<div class="state-message">
			<div class="spinner"></div>
			<span>Loading transactions...</span>
		</div>
	<!-- Error State -->
	{:else if error}
		<div class="state-message error">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<circle cx="12" cy="12" r="10"/>
				<line x1="12" y1="8" x2="12" y2="12"/>
				<line x1="12" y1="16" x2="12.01" y2="16"/>
			</svg>
			<span>{error}</span>
			<button class="retry-btn" on:click={loadTransactions}>Retry</button>
		</div>
	<!-- Empty State -->
	{:else if filteredTransactions.length === 0}
		<div class="state-message">
			<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
				<rect x="2" y="5" width="20" height="14" rx="2"/>
				<line x1="2" y1="10" x2="22" y2="10"/>
			</svg>
			<span>No transactions found</span>
		</div>
	<!-- Transactions Table -->
	{:else}
		<div class="table-container">
			<table class="transactions-table">
				<thead>
					<tr>
						<th>Tx ID</th>
						<th>Type</th>
						<th>From Agent</th>
						<th>To Agent</th>
						<th>Amount</th>
						<th>Order ID</th>
						<th>Memo</th>
						<th>Timestamp</th>
					</tr>
				</thead>
				<tbody>
					{#each paginatedTransactions as tx}
						<tr>
							<td class="mono truncate" title={tx.tx_id}>
								{truncateId(tx.tx_id)}
							</td>
							<td>
								<span 
									class="type-badge"
									style="background: {typeColors[tx.tx_type] || 'var(--text-dim)'}20; color: {typeColors[tx.tx_type] || 'var(--text-dim)'}; border-color: {typeColors[tx.tx_type] || 'var(--text-dim)'}40;"
								>
									{formatTxType(tx.tx_type)}
								</span>
							</td>
							<td class="mono truncate" title={tx.from_agent}>
								{truncateId(tx.from_agent)}
							</td>
							<td class="mono truncate" title={tx.to_agent}>
								{truncateId(tx.to_agent)}
							</td>
							<td class="mono amount" style="color: {getAmountColor(tx.tx_type)};">
								{formatAmount(tx.amount, tx.tx_type)} MC
							</td>
							<td>
								{#if tx.order_id}
									<a href="/dashboard/orders/?order={tx.order_id}" class="order-link">
										{truncateId(tx.order_id, 8)}
									</a>
								{:else}
									<span class="dim">—</span>
								{/if}
							</td>
							<td class="truncate" title={tx.memo || ''}>
								<span class="dim">{tx.memo || '—'}</span>
							</td>
							<td class="timestamp">{formatTimestamp(tx.recorded_at)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		<div class="pagination">
			<span class="pagination-info">Showing {startIdx}-{endIdx} of {totalFiltered}</span>
			<div class="pagination-controls">
				<button 
					class="page-btn" 
					on:click={() => goToPage(page - 1)}
					disabled={page === 1}
				>
					Previous
				</button>
				<button 
					class="page-btn" 
					on:click={() => goToPage(page + 1)}
					disabled={page >= totalPages}
				>
					Next
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.ledger-page {
		padding: 28px;
		max-width: 1400px;
		margin: 0 auto;
	}

	/* ── Page Header ─────────────────────────── */
	.page-header {
		margin-bottom: 24px;
	}

	.page-title {
		font-family: var(--font-heading);
		font-size: 1.75rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 8px 0;
		letter-spacing: 1px;
	}

	.page-subtitle {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-dim);
		margin: 0;
	}

	/* ── Stats Row ───────────────────────────── */
	.stats-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 16px;
		margin-bottom: 24px;
	}

	.stat-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 20px;
	}

	.stat-value {
		font-family: var(--font-heading);
		font-size: 1.75rem;
		font-weight: 600;
		margin-bottom: 4px;
	}

	.stat-label {
		font-family: var(--font-body);
		font-size: 0.75rem;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	/* ── Filter Bar ──────────────────────────── */
	.filter-bar {
		display: flex;
		gap: 16px;
		margin-bottom: 20px;
		padding: 16px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
	}

	.filter-group {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.filter-group label {
		font-family: var(--font-body);
		font-size: 0.7rem;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.filter-select {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text);
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 8px 12px;
		min-width: 160px;
		cursor: pointer;
	}

	.filter-select:focus {
		outline: none;
		border-color: var(--accent);
	}

	.filter-select option {
		background: var(--bg-surface);
		color: var(--text);
	}

	/* ── State Messages ──────────────────────── */
	.state-message {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 48px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		color: var(--text-secondary);
		font-family: var(--font-body);
		font-size: 0.875rem;
	}

	.state-message.error {
		color: var(--red);
		background: rgba(239, 68, 68, 0.05);
		border-color: rgba(239, 68, 68, 0.2);
	}

	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.retry-btn {
		font-family: var(--font-body);
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--text);
		background: var(--accent);
		border: none;
		border-radius: 4px;
		padding: 8px 16px;
		cursor: pointer;
		margin-left: 8px;
		transition: background 0.2s;
	}

	.retry-btn:hover {
		background: var(--accent-hover);
	}

	/* ── Table ───────────────────────────────── */
	.table-container {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		overflow: hidden;
		overflow-x: auto;
	}

	.transactions-table {
		width: 100%;
		border-collapse: collapse;
		font-family: var(--font-body);
		font-size: 0.8125rem;
	}

	.transactions-table thead {
		background: var(--bg-surface);
	}

	.transactions-table th {
		font-family: var(--font-heading);
		font-weight: 500;
		font-size: 0.7rem;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 1px;
		padding: 14px 16px;
		text-align: left;
		border-bottom: 1px solid var(--border);
		white-space: nowrap;
	}

	.transactions-table td {
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
		color: var(--text);
		white-space: nowrap;
	}

	.transactions-table tbody tr:last-child td {
		border-bottom: none;
	}

	.transactions-table tbody tr:hover {
		background: rgba(255, 255, 255, 0.02);
	}

	.mono {
		font-family: var(--font-mono);
	}

	.truncate {
		max-width: 140px;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.dim {
		color: var(--text-dim);
	}

	.type-badge {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		font-weight: 500;
		padding: 4px 10px;
		border-radius: 2px;
		border: 1px solid;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		white-space: nowrap;
	}

	.amount {
		font-weight: 500;
	}

	.order-link {
		color: var(--accent);
		text-decoration: none;
		font-family: var(--font-mono);
		font-size: 0.75rem;
	}

	.order-link:hover {
		text-decoration: underline;
	}

	.timestamp {
		color: var(--text-secondary);
		font-family: var(--font-mono);
		font-size: 0.75rem;
	}

	/* ── Pagination ──────────────────────────── */
	.pagination {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 20px;
		padding: 16px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
	}

	.pagination-info {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-dim);
	}

	.pagination-controls {
		display: flex;
		gap: 8px;
	}

	.page-btn {
		font-family: var(--font-body);
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--text);
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 8px 16px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.page-btn:hover:not(:disabled) {
		background: var(--border);
		border-color: var(--border-strong);
	}

	.page-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	/* ── Responsive ──────────────────────────── */
	@media (max-width: 768px) {
		.ledger-page {
			padding: 16px;
		}

		.stats-row {
			grid-template-columns: 1fr;
		}

		.filter-bar {
			flex-direction: column;
		}

		.transactions-table {
			font-size: 0.75rem;
		}

		.transactions-table th,
		.transactions-table td {
			padding: 10px 12px;
		}

		.truncate {
			max-width: 80px;
		}

		.pagination {
			flex-direction: column;
			gap: 12px;
			text-align: center;
		}
	}
</style>
