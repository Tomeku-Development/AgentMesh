<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { activeWorkspaceId } from '$lib/stores/workspace';
	import { getBillingHistory } from '$lib/api/billing';
	import type { BillingEntry } from '$lib/types/api';

	// State
	let entries: BillingEntry[] = [];
	let loading = true;
	let error = '';

	$: workspaceId = get(activeWorkspaceId) || 'default';

	onMount(async () => {
		await loadHistory();
	});

	async function loadHistory() {
		loading = true;
		error = '';
		try {
			entries = await getBillingHistory(workspaceId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load billing history';
		} finally {
			loading = false;
		}
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatAmount(amount: number, currency: string): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: currency.toUpperCase()
		}).format(amount);
	}

	function getStatusColor(status: string): string {
		switch (status.toLowerCase()) {
			case 'paid':
			case 'completed':
			case 'success':
				return 'var(--green)';
			case 'pending':
			case 'processing':
				return '#fbbf24';
			case 'failed':
			case 'cancelled':
			case 'refunded':
				return 'var(--red)';
			default:
				return 'var(--text-secondary)';
		}
	}

	function formatStatus(status: string): string {
		return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
	}
</script>

<svelte:head>
	<title>Payment History — MESH Dashboard</title>
</svelte:head>

<div class="history-page">
	<!-- Page Header -->
	<header class="page-header">
		<div class="header-left">
			<a href="/dashboard/billing/" class="back-link">
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="19" y1="12" x2="5" y2="12"/>
					<polyline points="12 19 5 12 12 5"/>
				</svg>
				Back to Billing
			</a>
			<h1>Payment History</h1>
			<p class="subtitle">View your transaction and invoice history</p>
		</div>
	</header>

	{#if error}
		<div class="error-alert">
			<span>{error}</span>
			<button on:click={loadHistory}>Retry</button>
		</div>
	{/if}

	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<span>Loading payment history...</span>
		</div>
	{:else if entries.length === 0}
		<div class="empty-state">
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/>
				<line x1="1" y1="10" x2="23" y2="10"/>
			</svg>
			<h3>No payment history yet</h3>
			<p>Your billing transactions will appear here once you make a payment.</p>
			<a href="/dashboard/billing/" class="back-btn">Return to Billing</a>
		</div>
	{:else}
		<div class="table-container">
			<table class="history-table">
				<thead>
					<tr>
						<th>Date</th>
						<th>Type</th>
						<th>Description</th>
						<th>Amount</th>
						<th>Status</th>
					</tr>
				</thead>
				<tbody>
					{#each entries as entry}
						<tr>
							<td class="date-cell">{formatDate(entry.created_at)}</td>
							<td>
								<span class="type-badge">{entry.type}</span>
							</td>
							<td class="description-cell">{entry.description || '—'}</td>
							<td class="amount-cell">{formatAmount(entry.amount, entry.currency)}</td>
							<td>
								<span 
									class="status-badge"
									style="background: {getStatusColor(entry.status)}15; color: {getStatusColor(entry.status)}; border-color: {getStatusColor(entry.status)}30;"
								>
									{formatStatus(entry.status)}
								</span>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<style>
	.history-page {
		padding: 28px;
		max-width: 1200px;
		margin: 0 auto;
	}

	/* Page Header */
	.page-header {
		margin-bottom: 24px;
	}

	.header-left {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		color: var(--text-secondary);
		font-size: 0.8rem;
		text-decoration: none;
		transition: color 0.2s;
		width: fit-content;
	}

	.back-link:hover {
		color: var(--accent);
	}

	h1 {
		font-family: var(--font-heading);
		font-size: 1.75rem;
		font-weight: 600;
		color: var(--text);
		margin: 0;
		letter-spacing: 1px;
	}

	.subtitle {
		font-size: 0.875rem;
		color: var(--text-dim);
		margin: 0;
	}

	/* Error Alert */
	.error-alert {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		border-radius: 4px;
		padding: 12px 16px;
		margin-bottom: 24px;
		color: var(--red);
		font-size: 0.875rem;
	}

	.error-alert button {
		background: transparent;
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: var(--red);
		padding: 6px 12px;
		border-radius: 3px;
		cursor: pointer;
		font-family: var(--font-heading);
		font-size: 0.75rem;
	}

	/* Loading State */
	.loading-state {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		padding: 64px;
		color: var(--text-secondary);
	}

	.spinner {
		width: 24px;
		height: 24px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 64px 32px;
		text-align: center;
		color: var(--text-dim);
	}

	.empty-state svg {
		margin-bottom: 16px;
		opacity: 0.5;
	}

	.empty-state h3 {
		font-family: var(--font-heading);
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--text-secondary);
		margin: 0 0 8px 0;
	}

	.empty-state p {
		font-size: 0.875rem;
		margin: 0 0 24px 0;
		max-width: 320px;
	}

	.back-btn {
		display: inline-flex;
		align-items: center;
		gap: 8px;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 3px;
		padding: 10px 20px;
		font-family: var(--font-heading);
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-decoration: none;
		transition: background 0.2s;
	}

	.back-btn:hover {
		background: var(--accent-hover);
	}

	/* Table */
	.table-container {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		overflow: hidden;
	}

	.history-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.history-table th {
		background: var(--bg-elevated);
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 1px;
		text-align: left;
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
	}

	.history-table td {
		padding: 16px;
		border-bottom: 1px solid var(--border);
		color: var(--text);
	}

	.history-table tbody tr:last-child td {
		border-bottom: none;
	}

	.history-table tbody tr:hover {
		background: rgba(255, 255, 255, 0.02);
	}

	.date-cell {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.type-badge {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		font-weight: 500;
		background: var(--accent-dim);
		color: var(--accent);
		padding: 4px 10px;
		border-radius: 2px;
		text-transform: uppercase;
		letter-spacing: 0.3px;
	}

	.description-cell {
		max-width: 300px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.amount-cell {
		font-family: var(--font-mono);
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--text);
	}

	.status-badge {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		font-weight: 500;
		padding: 4px 10px;
		border-radius: 2px;
		border: 1px solid;
		text-transform: uppercase;
		letter-spacing: 0.3px;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.history-page {
			padding: 16px;
		}

		.history-table {
			font-size: 0.8rem;
		}

		.history-table th,
		.history-table td {
			padding: 12px;
		}

		.description-cell {
			max-width: 150px;
		}
	}
</style>
