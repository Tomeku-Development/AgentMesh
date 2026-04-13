<script lang="ts">
	import { onMount } from 'svelte';
	import { getPlatformAnalytics } from '$lib/api/billing';
	import type { PlatformAnalytics } from '$lib/types/api';

	// State
	let analytics: PlatformAnalytics | null = null;
	let loading = true;
	let error = '';
	let hoveredHour: number | null = null;

	// Plan colors
	const planColors: Record<string, string> = {
		starter: '#818cf8',
		pro: '#4ade80',
		enterprise: '#ff6f00',
		custom: '#fbbf24'
	};

	// Computed values
	$: maxHourlyCalls = analytics?.hourly_breakdown.length
		? Math.max(...analytics.hourly_breakdown.map(h => h.calls), 1)
		: 1;

	$: totalWorkspaces = analytics?.total_workspaces || 0;
	$: todayCalls = analytics?.today.llm_calls || 0;
	$: todayCost = analytics?.today.cost || 0;
	$: monthlyCost = analytics?.this_month.cost || 0;
	$: monthlyCalls = analytics?.this_month.llm_calls || 0;

	$: planDistributionTotal = analytics?.plan_distribution.reduce((sum, p) => sum + p.count, 0) || 0;

	onMount(async () => {
		await loadAnalytics();
	});

	async function loadAnalytics() {
		loading = true;
		error = '';
		try {
			analytics = await getPlatformAnalytics();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load analytics';
		} finally {
			loading = false;
		}
	}

	function getHeatmapColor(calls: number): string {
		const intensity = calls / maxHourlyCalls;
		const alpha = Math.max(0.1, intensity);
		return `rgba(255, 111, 0, ${alpha})`;
	}

	function formatCurrency(amount: number): string {
		return '$' + amount.toFixed(2);
	}

	function formatNumber(num: number): string {
		return num.toLocaleString();
	}

	function truncateId(id: string): string {
		return id.length > 12 ? id.slice(0, 6) + '...' + id.slice(-4) : id;
	}

	function getPlanPercentage(count: number): number {
		if (planDistributionTotal === 0) return 0;
		return Math.round((count / planDistributionTotal) * 100);
	}
</script>

<svelte:head>
	<title>Admin Analytics — MESH Dashboard</title>
</svelte:head>

<div class="admin-page">
	<!-- Page Header -->
	<header class="page-header">
		<h1>Platform Analytics</h1>
		<p class="subtitle">Overview of platform usage and workspace activity</p>
	</header>

	{#if error}
		<div class="error-alert">
			<span>{error}</span>
			<button on:click={loadAnalytics}>Retry</button>
		</div>
	{/if}

	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<span>Loading analytics...</span>
		</div>
	{:else if analytics}
		<div class="analytics-content">
			<!-- Overview Cards -->
			<section class="overview-cards">
				<div class="stat-card">
					<div class="stat-icon workspaces">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
							<polyline points="9 22 9 12 15 12 15 22"/>
						</svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">Total Workspaces</span>
						<span class="stat-value">{formatNumber(totalWorkspaces)}</span>
					</div>
				</div>

				<div class="stat-card">
					<div class="stat-icon calls">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
						</svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">LLM Calls Today</span>
						<span class="stat-value">{formatNumber(todayCalls)}</span>
						<span class="stat-sub">{formatCurrency(todayCost)}</span>
					</div>
				</div>

				<div class="stat-card">
					<div class="stat-icon cost">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="12" y1="1" x2="12" y2="23"/>
							<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
						</svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">Monthly LLM Cost</span>
						<span class="stat-value mono">{formatCurrency(monthlyCost)}</span>
					</div>
				</div>

				<div class="stat-card">
					<div class="stat-icon tokens">
						<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<circle cx="12" cy="12" r="10"/>
							<line x1="2" y1="12" x2="22" y2="12"/>
							<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
						</svg>
					</div>
					<div class="stat-content">
						<span class="stat-label">Monthly LLM Calls</span>
						<span class="stat-value">{formatNumber(monthlyCalls)}</span>
					</div>
				</div>
			</section>

			<!-- Hourly Activity Heatmap -->
			<section class="heatmap-section">
				<h3>Hourly Activity (24h)</h3>
				<div class="heatmap-container">
					<div class="heatmap-grid">
						{#each Array(24) as _, hour}
							{@const hourData = analytics.hourly_breakdown.find(h => h.hour === hour)}
							{@const calls = hourData?.calls || 0}
							<div
								class="heatmap-cell"
								style="background-color: {getHeatmapColor(calls)}"
								on:mouseenter={() => hoveredHour = hour}
								on:mouseleave={() => hoveredHour = null}
							>
								{#if hoveredHour === hour}
									<div class="heatmap-tooltip">
										<span class="tooltip-hour">{hour}:00 - {hour}:59</span>
										<span class="tooltip-calls">{formatNumber(calls)} calls</span>
									</div>
								{/if}
							</div>
						{/each}
					</div>
					<div class="heatmap-labels">
						{#each [0, 6, 12, 18, 23] as label}
							<span class="heatmap-label">{label}:00</span>
						{/each}
					</div>
				</div>
				<div class="heatmap-legend">
					<span>Low</span>
					<div class="legend-gradient"></div>
					<span>High</span>
				</div>
			</section>

			<div class="bottom-grid">
				<!-- Top Consumers Table -->
				<section class="consumers-section">
					<h3>Top Consumers This Month</h3>
					{#if analytics.top_workspaces.length > 0}
						<div class="table-container">
							<table class="consumers-table">
								<thead>
									<tr>
										<th>Workspace ID</th>
										<th class="numeric">Calls</th>
										<th class="numeric">Cost</th>
									</tr>
								</thead>
								<tbody>
									{#each analytics.top_workspaces.slice(0, 10) as ws}
										<tr>
											<td class="mono truncate" title={ws.workspace_id}>
												{truncateId(ws.workspace_id)}
											</td>
											<td class="mono numeric">{formatNumber(ws.calls)}</td>
											<td class="mono numeric cost">{formatCurrency(ws.cost)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{:else}
						<div class="empty-state">No usage data available</div>
					{/if}
				</section>

				<!-- Plan Distribution -->
				<section class="plan-distribution-section">
					<h3>Plan Distribution</h3>
					{#if analytics.plan_distribution.length > 0}
						<div class="distribution-chart">
							{#each analytics.plan_distribution as plan}
								{@const percentage = getPlanPercentage(plan.count)}
								<div class="distribution-item">
									<div class="distribution-header">
										<span class="plan-name" style="color: {planColors[plan.plan] || '#888'}">
											{plan.plan.charAt(0).toUpperCase() + plan.plan.slice(1)}
										</span>
										<span class="plan-count">{formatNumber(plan.count)} ({percentage}%)</span>
									</div>
									<div class="distribution-bar">
										<div
											class="distribution-fill"
											style="width: {percentage}%; background-color: {planColors[plan.plan] || '#888'}"
										></div>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div class="empty-state">No plan data available</div>
					{/if}
				</section>
			</div>
		</div>
	{/if}
</div>

<style>
	.admin-page {
		padding: 28px;
		max-width: 1400px;
		margin: 0 auto;
	}

	/* Page Header */
	.page-header {
		margin-bottom: 24px;
	}

	h1 {
		font-family: var(--font-heading);
		font-size: 1.75rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 8px 0;
		letter-spacing: 1px;
	}

	.subtitle {
		font-size: 0.875rem;
		color: var(--text-dim);
		margin: 0;
	}

	h3 {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 20px 0;
		letter-spacing: 0.5px;
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
		letter-spacing: 0.5px;
	}

	.error-alert button:hover {
		background: rgba(239, 68, 68, 0.1);
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

	/* Overview Cards */
	.overview-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
		gap: 16px;
		margin-bottom: 24px;
	}

	.stat-card {
		display: flex;
		align-items: center;
		gap: 16px;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 20px;
	}

	.stat-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 48px;
		height: 48px;
		border-radius: 6px;
		flex-shrink: 0;
	}

	.stat-icon.workspaces {
		background: rgba(129, 140, 248, 0.1);
		color: #818cf8;
	}

	.stat-icon.calls {
		background: rgba(255, 111, 0, 0.1);
		color: var(--accent);
	}

	.stat-icon.cost {
		background: rgba(74, 222, 128, 0.1);
		color: var(--green);
	}

	.stat-icon.tokens {
		background: rgba(96, 165, 250, 0.1);
		color: #60a5fa;
	}

	.stat-content {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.stat-label {
		font-family: var(--font-heading);
		font-size: 0.7rem;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.stat-value {
		font-family: var(--font-heading);
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text);
	}

	.stat-value.mono {
		font-family: var(--font-mono);
	}

	.stat-sub {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--accent);
	}

	/* Heatmap Section */
	.heatmap-section {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
		margin-bottom: 24px;
	}

	.heatmap-container {
		margin-bottom: 12px;
	}

	.heatmap-grid {
		display: grid;
		grid-template-columns: repeat(24, 1fr);
		gap: 2px;
		height: 60px;
	}

	.heatmap-cell {
		position: relative;
		border-radius: 2px;
		cursor: pointer;
		transition: transform 0.15s;
	}

	.heatmap-cell:hover {
		transform: scale(1.1);
		z-index: 1;
	}

	.heatmap-tooltip {
		position: absolute;
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%);
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 8px 12px;
		margin-bottom: 8px;
		white-space: nowrap;
		z-index: 10;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.tooltip-hour {
		font-family: var(--font-heading);
		font-size: 0.7rem;
		color: var(--text-secondary);
	}

	.tooltip-calls {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text);
	}

	.heatmap-labels {
		display: flex;
		justify-content: space-between;
		margin-top: 8px;
		padding: 0 2px;
	}

	.heatmap-label {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--text-dim);
	}

	.heatmap-legend {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 8px;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-dim);
	}

	.legend-gradient {
		width: 100px;
		height: 8px;
		background: linear-gradient(to right, rgba(255, 111, 0, 0.1), rgba(255, 111, 0, 1));
		border-radius: 4px;
	}

	/* Bottom Grid */
	.bottom-grid {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 24px;
	}

	/* Consumers Section */
	.consumers-section {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
	}

	.table-container {
		overflow-x: auto;
	}

	.consumers-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.consumers-table th {
		font-family: var(--font-heading);
		font-size: 0.65rem;
		font-weight: 500;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		text-align: left;
		padding: 10px 0;
		border-bottom: 1px solid var(--border);
	}

	.consumers-table th.numeric {
		text-align: right;
	}

	.consumers-table td {
		padding: 12px 0;
		border-bottom: 1px solid var(--border);
		color: var(--text);
	}

	.consumers-table tbody tr:last-child td {
		border-bottom: none;
	}

	.consumers-table tbody tr:hover {
		background: var(--bg-elevated);
	}

	.mono {
		font-family: var(--font-mono);
		font-size: 0.85rem;
	}

	.numeric {
		text-align: right;
	}

	.cost {
		color: var(--accent);
	}

	.truncate {
		max-width: 150px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* Plan Distribution */
	.plan-distribution-section {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
	}

	.distribution-chart {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.distribution-item {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.distribution-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.plan-name {
		font-family: var(--font-heading);
		font-size: 0.85rem;
		font-weight: 600;
		text-transform: capitalize;
	}

	.plan-count {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text-secondary);
	}

	.distribution-bar {
		height: 8px;
		background: var(--bg);
		border-radius: 4px;
		overflow: hidden;
	}

	.distribution-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	/* Empty State */
	.empty-state {
		color: var(--text-dim);
		font-size: 0.875rem;
		text-align: center;
		padding: 32px;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.bottom-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.admin-page {
			padding: 16px;
		}

		.overview-cards {
			grid-template-columns: 1fr;
		}

		.heatmap-grid {
			height: 40px;
		}
	}
</style>
