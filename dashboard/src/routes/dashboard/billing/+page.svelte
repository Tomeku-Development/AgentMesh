<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { activeWorkspaceId, activeWorkspace } from '$lib/stores/workspace';
	import {
		getUsageSummary,
		getQuotaStatus,
		getPlans,
		changePlan,
		exportUsageCsv
	} from '$lib/api/billing';
	import type { UsageSummary, SubscriptionPlan, QuotaStatus } from '$lib/types/api';

	// State
	let usage: UsageSummary | null = null;
	let quota: QuotaStatus | null = null;
	let plans: SubscriptionPlan[] = [];
	let loading = true;
	let error = '';
	let changingPlan = '';
	let showPlanModal = false;

	// Role colors for agent badges
	const roleColors: Record<string, string> = {
		buyer: '#ff6f00',
		supplier: '#4ade80',
		logistics: '#60a5fa',
		inspector: '#c084fc',
		oracle: '#fbbf24'
	};

	// Computed values
	$: workspaceId = get(activeWorkspaceId) || 'default';
	$: currentPlan = get(activeWorkspace)?.plan || 'starter';
	$: creditsPercent = quota
		? Math.min(100, (quota.credits_used / Math.max(1, quota.credits_limit)) * 100)
		: 0;
	$: dailyPercent = quota
		? Math.min(100, (quota.daily_requests / Math.max(1, quota.daily_limit)) * 100)
		: 0;
	$: maxChartValue = usage
		? Math.max(...usage.daily_breakdown.map((d) => d.calls), 1)
		: 1;

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = '';
		try {
			const [usageData, quotaData, plansData] = await Promise.all([
				getUsageSummary(workspaceId, 30),
				getQuotaStatus(workspaceId),
				getPlans()
			]);
			usage = usageData;
			quota = quotaData;
			plans = plansData.sort((a, b) => a.sort_order - b.sort_order);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load billing data';
		} finally {
			loading = false;
		}
	}

	async function handleChangePlan(planName: string) {
		changingPlan = planName;
		try {
			await changePlan(workspaceId, planName);
			// Reload to get updated quota
			await loadData();
			showPlanModal = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to change plan';
		} finally {
			changingPlan = '';
		}
	}

	function handleExportCsv() {
		exportUsageCsv(workspaceId, 30);
	}

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function formatShortDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	function formatCurrency(amount: number): string {
		return '$' + amount.toFixed(2);
	}

	function formatNumber(num: number): string {
		return num.toLocaleString();
	}

	function getPlanDisplayName(planName: string): string {
		const plan = plans.find((p) => p.name === planName);
		return plan?.display_name || planName.charAt(0).toUpperCase() + planName.slice(1);
	}
</script>

<svelte:head>
	<title>Billing & Usage — MESH Dashboard</title>
</svelte:head>

<div class="billing-page">
	<!-- Page Header -->
	<header class="page-header">
		<h1>Billing & Usage</h1>
		<p class="subtitle">Monitor your workspace usage, credits, and subscription</p>
	</header>

	{#if error}
		<div class="error-alert">
			<span>{error}</span>
			<button on:click={loadData}>Retry</button>
		</div>
	{/if}

	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<span>Loading billing data...</span>
		</div>
	{:else}
		<div class="billing-content">
			<!-- Current Plan Card -->
			<section class="plan-card">
				<div class="plan-header">
					<div class="plan-info">
						<h2>{getPlanDisplayName(currentPlan)}</h2>
						{#if plans.find(p => p.name === currentPlan)}
							<span class="plan-price">
								{formatCurrency(plans.find(p => p.name === currentPlan)?.monthly_price || 0)}/mo
							</span>
						{/if}
					</div>
					<button class="change-plan-btn" on:click={() => showPlanModal = true}>
						Change Plan
					</button>
				</div>

				<div class="usage-bars">
					<div class="usage-row">
						<div class="usage-label">
							<span>Credits</span>
							<span class="usage-value">
								{formatNumber(quota?.credits_used || 0)} / {formatNumber(quota?.credits_limit || 0)}
							</span>
						</div>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {creditsPercent}%"></div>
						</div>
						<span class="usage-percent">{creditsPercent.toFixed(0)}%</span>
					</div>

					<div class="usage-row">
						<div class="usage-label">
							<span>Daily Requests</span>
							<span class="usage-value">
								{formatNumber(quota?.daily_requests || 0)} / {formatNumber(quota?.daily_limit || 0)}
							</span>
						</div>
						<div class="progress-bar">
							<div class="progress-fill secondary" style="width: {dailyPercent}%"></div>
						</div>
						<span class="usage-percent">{dailyPercent.toFixed(0)}%</span>
					</div>
				</div>

				<div class="plan-meta">
					{#if usage}
						<span>Period: {formatShortDate(usage.period_start)} — {formatShortDate(usage.period_end)}</span>
					{/if}
					<span class="credits-remaining">
						{formatNumber(quota?.credits_remaining || 0)} credits remaining
					</span>
				</div>
			</section>

			<!-- Quick Actions -->
			<section class="quick-actions">
				<button class="action-btn" on:click={handleExportCsv}>
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
						<polyline points="7 10 12 15 17 10"/>
						<line x1="12" y1="15" x2="12" y2="3"/>
					</svg>
					Export CSV
				</button>
				<a href="/dashboard/billing/history/" class="action-link">
					<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="12" cy="12" r="10"/>
						<polyline points="12 6 12 12 16 14"/>
					</svg>
					Payment History
				</a>
			</section>

			<!-- Usage Chart -->
			<section class="chart-section">
				<h3>Daily LLM Usage (Last 30 Days)</h3>
				{#if usage && usage.daily_breakdown.length > 0}
					<div class="bar-chart">
						{#each usage.daily_breakdown as day, i}
							<div class="bar-container">
								<div 
									class="bar" 
									style="height: {(day.calls / maxChartValue) * 100}%"
									title="{formatDate(day.date)}: {day.calls} calls"
								>
									<span class="bar-tooltip">{day.calls}</span>
								</div>
								{#if i % 5 === 0}
									<span class="bar-label">{formatDate(day.date).split(' ')[0]}</span>
								{/if}
							</div>
						{/each}
					</div>
				{:else}
					<div class="empty-chart">No usage data available</div>
				{/if}
			</section>

			<!-- Cost Breakdown Tables -->
			<section class="breakdown-section">
				<h3>Cost Breakdown</h3>
				<div class="breakdown-grid">
					<!-- By Agent Role -->
					<div class="breakdown-card">
						<h4>By Agent Role</h4>
						{#if usage && usage.by_agent_role.length > 0}
							<table class="breakdown-table">
								<thead>
									<tr>
										<th>Role</th>
										<th>Calls</th>
										<th>Tokens</th>
										<th>Cost</th>
									</tr>
								</thead>
								<tbody>
									{#each usage.by_agent_role as item}
										<tr>
											<td>
												<span 
													class="role-badge"
													style="background: {roleColors[item.role] || '#666'}20; color: {roleColors[item.role] || '#666'}; border-color: {roleColors[item.role] || '#666'}40;"
												>
													{item.role}
												</span>
											</td>
											<td class="mono">{formatNumber(item.calls)}</td>
											<td class="mono">{formatNumber(item.tokens)}</td>
											<td class="mono cost">{formatCurrency(item.cost)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						{:else}
							<div class="empty-table">No data</div>
						{/if}
					</div>

					<!-- By Model -->
					<div class="breakdown-card">
						<h4>By Model</h4>
						{#if usage && usage.by_model.length > 0}
							<table class="breakdown-table">
								<thead>
									<tr>
										<th>Model</th>
										<th>Calls</th>
										<th>Tokens</th>
										<th>Cost</th>
									</tr>
								</thead>
								<tbody>
									{#each usage.by_model as item}
										<tr>
											<td class="model-name">{item.model}</td>
											<td class="mono">{formatNumber(item.calls)}</td>
											<td class="mono">{formatNumber(item.tokens)}</td>
											<td class="mono cost">{formatCurrency(item.cost)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						{:else}
							<div class="empty-table">No data</div>
						{/if}
					</div>

					<!-- By Prompt Type -->
					<div class="breakdown-card">
						<h4>By Prompt Type</h4>
						{#if usage && usage.by_prompt_type.length > 0}
							<table class="breakdown-table">
								<thead>
									<tr>
										<th>Type</th>
										<th>Calls</th>
										<th>Cost</th>
									</tr>
								</thead>
								<tbody>
									{#each usage.by_prompt_type as item}
										<tr>
											<td>{item.type}</td>
											<td class="mono">{formatNumber(item.calls)}</td>
											<td class="mono cost">{formatCurrency(item.cost)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						{:else}
							<div class="empty-table">No data</div>
						{/if}
					</div>
				</div>
			</section>

			<!-- Plan Comparison -->
			{#if currentPlan !== 'enterprise'}
				<section class="plans-section">
					<h3>Available Plans</h3>
					<div class="plans-grid">
						{#each plans.filter(p => p.is_active) as plan}
							<div class="plan-card-comparison" class:current={plan.name === currentPlan}>
								{#if plan.name === currentPlan}
									<span class="current-badge">Current</span>
								{/if}
								<h4>{plan.display_name}</h4>
								<div class="plan-price-lg">{formatCurrency(plan.monthly_price)}<span>/mo</span></div>
								<ul class="features-list">
									<li>
										<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
											<polyline points="20 6 9 17 4 12"/>
										</svg>
										{formatNumber(plan.monthly_credits)} credits/mo
									</li>
									<li>
										<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
											<polyline points="20 6 9 17 4 12"/>
										</svg>
										Up to {plan.max_agents} agents
									</li>
									<li>
										<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
											<polyline points="20 6 9 17 4 12"/>
										</svg>
										{formatNumber(plan.llm_requests_per_day)} requests/day
									</li>
									<li>
										<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
											<polyline points="20 6 9 17 4 12"/>
										</svg>
										{plan.max_workspaces} workspace{plan.max_workspaces > 1 ? 's' : ''}
									</li>
								</ul>
								{#if plan.name !== currentPlan}
									<button 
										class="upgrade-btn" 
										on:click={() => handleChangePlan(plan.name)}
										disabled={changingPlan !== ''}
									>
										{#if changingPlan === plan.name}
											<div class="btn-spinner"></div>
										{:else}
											{plan.sort_order > (plans.find(p => p.name === currentPlan)?.sort_order || 0) ? 'Upgrade' : 'Downgrade'}
										{/if}
									</button>
								{:else}
									<div class="current-plan-indicator">Current Plan</div>
								{/if}
							</div>
						{/each}
					</div>
				</section>
			{/if}
		</div>
	{/if}
</div>

<style>
	.billing-page {
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

	/* Current Plan Card */
	.plan-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
		margin-bottom: 24px;
	}

	.plan-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 24px;
	}

	.plan-info h2 {
		font-family: var(--font-heading);
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--text);
		margin: 0 0 4px 0;
		letter-spacing: 1px;
	}

	.plan-price {
		font-family: var(--font-mono);
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	.change-plan-btn {
		background: transparent;
		border: 1px solid var(--border);
		color: var(--text-secondary);
		padding: 8px 16px;
		border-radius: 3px;
		cursor: pointer;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		letter-spacing: 0.5px;
		transition: all 0.2s;
	}

	.change-plan-btn:hover {
		border-color: var(--accent);
		color: var(--accent);
	}

	/* Usage Bars */
	.usage-bars {
		margin-bottom: 20px;
	}

	.usage-row {
		display: grid;
		grid-template-columns: 200px 1fr 60px;
		gap: 16px;
		align-items: center;
		margin-bottom: 16px;
	}

	.usage-label {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.usage-label span:first-child {
		font-family: var(--font-heading);
		font-size: 0.75rem;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.usage-value {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text-dim);
	}

	.progress-bar {
		height: 8px;
		background: var(--bg);
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: var(--accent);
		border-radius: 4px;
		transition: width 0.3s ease;
	}

	.progress-fill.secondary {
		background: #60a5fa;
	}

	.usage-percent {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text-secondary);
		text-align: right;
	}

	.plan-meta {
		display: flex;
		justify-content: space-between;
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-dim);
	}

	.credits-remaining {
		color: var(--accent);
	}

	/* Quick Actions */
	.quick-actions {
		display: flex;
		gap: 12px;
		margin-bottom: 24px;
	}

	.action-btn,
	.action-link {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		color: var(--text-secondary);
		padding: 10px 16px;
		border-radius: 3px;
		cursor: pointer;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		letter-spacing: 0.5px;
		text-decoration: none;
		transition: all 0.2s;
	}

	.action-btn:hover,
	.action-link:hover {
		border-color: var(--accent);
		color: var(--accent);
	}

	/* Bar Chart */
	.chart-section {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
		margin-bottom: 24px;
	}

	h3 {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 20px 0;
		letter-spacing: 0.5px;
	}

	.bar-chart {
		display: flex;
		align-items: flex-end;
		gap: 4px;
		height: 180px;
		padding-top: 20px;
	}

	.bar-container {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		height: 100%;
		position: relative;
	}

	.bar {
		width: 100%;
		max-width: 20px;
		background: var(--accent);
		border-radius: 2px 2px 0 0;
		position: relative;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.bar:hover {
		opacity: 0.8;
	}

	.bar-tooltip {
		position: absolute;
		bottom: 100%;
		left: 50%;
		transform: translateX(-50%);
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		padding: 4px 8px;
		border-radius: 3px;
		font-family: var(--font-mono);
		font-size: 0.65rem;
		color: var(--text);
		white-space: nowrap;
		opacity: 0;
		pointer-events: none;
		transition: opacity 0.2s;
		margin-bottom: 4px;
	}

	.bar:hover .bar-tooltip {
		opacity: 1;
	}

	.bar-label {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		color: var(--text-dim);
		margin-top: 8px;
	}

	.empty-chart {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 120px;
		color: var(--text-dim);
		font-size: 0.875rem;
	}

	/* Breakdown Section */
	.breakdown-section {
		margin-bottom: 24px;
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 16px;
	}

	.breakdown-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 20px;
	}

	.breakdown-card h4 {
		font-family: var(--font-heading);
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--text-secondary);
		margin: 0 0 16px 0;
		letter-spacing: 0.5px;
		text-transform: uppercase;
	}

	.breakdown-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8125rem;
	}

	.breakdown-table th {
		font-family: var(--font-heading);
		font-size: 0.65rem;
		font-weight: 500;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		text-align: left;
		padding: 8px 0;
		border-bottom: 1px solid var(--border);
	}

	.breakdown-table td {
		padding: 10px 0;
		border-bottom: 1px solid var(--border);
		color: var(--text);
	}

	.breakdown-table tbody tr:last-child td {
		border-bottom: none;
	}

	.mono {
		font-family: var(--font-mono);
		font-size: 0.8rem;
	}

	.cost {
		color: var(--accent);
	}

	.role-badge {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		font-weight: 500;
		padding: 3px 8px;
		border-radius: 2px;
		border: 1px solid;
		text-transform: uppercase;
		letter-spacing: 0.3px;
	}

	.model-name {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		max-width: 120px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.empty-table {
		color: var(--text-dim);
		font-size: 0.8rem;
		text-align: center;
		padding: 24px;
	}

	/* Plans Section */
	.plans-section {
		margin-bottom: 24px;
	}

	.plans-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 16px;
	}

	.plan-card-comparison {
		background: var(--bg-surface);
		border: 2px solid var(--border);
		border-radius: 6px;
		padding: 24px;
		position: relative;
		transition: border-color 0.2s;
	}

	.plan-card-comparison.current {
		border-color: var(--accent);
	}

	.current-badge {
		position: absolute;
		top: -10px;
		right: 16px;
		background: var(--accent);
		color: #fff;
		font-family: var(--font-heading);
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		padding: 4px 12px;
		border-radius: 2px;
	}

	.plan-card-comparison h4 {
		font-family: var(--font-heading);
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 8px 0;
		letter-spacing: 0.5px;
	}

	.plan-price-lg {
		font-family: var(--font-mono);
		font-size: 1.75rem;
		font-weight: 600;
		color: var(--text);
		margin-bottom: 20px;
	}

	.plan-price-lg span {
		font-size: 0.9rem;
		color: var(--text-secondary);
		font-weight: 400;
	}

	.features-list {
		list-style: none;
		padding: 0;
		margin: 0 0 20px 0;
	}

	.features-list li {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: 10px;
	}

	.features-list li svg {
		color: var(--green);
		flex-shrink: 0;
	}

	.upgrade-btn {
		width: 100%;
		background: var(--accent);
		border: none;
		color: #fff;
		padding: 12px;
		border-radius: 3px;
		cursor: pointer;
		font-family: var(--font-heading);
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		transition: background 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 42px;
	}

	.upgrade-btn:hover:not(:disabled) {
		background: var(--accent-hover);
	}

	.upgrade-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	.current-plan-indicator {
		width: 100%;
		text-align: center;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		color: var(--accent);
		padding: 12px;
		background: rgba(255, 111, 0, 0.1);
		border-radius: 3px;
		letter-spacing: 0.5px;
	}

	.btn-spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: #fff;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.billing-page {
			padding: 16px;
		}

		.usage-row {
			grid-template-columns: 1fr;
			gap: 8px;
		}

		.usage-percent {
			text-align: left;
		}

		.plan-meta {
			flex-direction: column;
			gap: 8px;
		}

		.quick-actions {
			flex-direction: column;
		}

		.breakdown-grid {
			grid-template-columns: 1fr;
		}

		.plans-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
