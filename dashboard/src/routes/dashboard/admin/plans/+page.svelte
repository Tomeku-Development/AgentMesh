<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { getPlans } from '$lib/api/billing';
	import { activeWorkspace } from '$lib/stores/workspace';
	import type { SubscriptionPlan } from '$lib/types/api';

	// State
	let plans: SubscriptionPlan[] = [];
	let loading = true;
	let error = '';

	// Plan colors
	const planColors: Record<string, string> = {
		starter: '#818cf8',
		pro: '#4ade80',
		enterprise: '#ff6f00',
		custom: '#fbbf24'
	};

	// Feature matrix configuration
	const featureRows = [
		{ key: 'monthly_credits', label: 'Monthly Credits', format: 'number' },
		{ key: 'max_agents', label: 'Max Agents', format: 'number' },
		{ key: 'max_workspaces', label: 'Max Workspaces', format: 'number' },
		{ key: 'max_api_keys', label: 'API Keys', format: 'number' },
		{ key: 'llm_requests_per_day', label: 'Daily LLM Requests', format: 'number' },
		{ key: 'llm_tokens_per_month', label: 'Monthly Tokens', format: 'number' },
		{ key: 'priority_support', label: 'Priority Support', format: 'boolean' },
		{ key: 'custom_models', label: 'Custom Models', format: 'boolean' },
		{ key: 'sla', label: 'SLA Guarantee', format: 'boolean' },
		{ key: 'export_data', label: 'Export Data', format: 'boolean' },
		{ key: 'team_members', label: 'Team Members', format: 'number' }
	];

	$: currentPlan = get(activeWorkspace)?.plan || 'starter';
	$: sortedPlans = plans.sort((a, b) => a.sort_order - b.sort_order);

	onMount(async () => {
		await loadPlans();
	});

	async function loadPlans() {
		loading = true;
		error = '';
		try {
			plans = await getPlans();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load plans';
		} finally {
			loading = false;
		}
	}

	function formatNumber(num: number): string {
		return num.toLocaleString();
	}

	function formatCurrency(amount: number): string {
		return '$' + amount.toFixed(0);
	}

	function getFeatureValue(plan: SubscriptionPlan, key: string, format: string): string | boolean {
		// Check features_json first for boolean features
		if (format === 'boolean') {
			const featureValue = plan.features_json?.[key];
			if (typeof featureValue === 'boolean') return featureValue;
			// Fallback to key existence in features_json
			return key in (plan.features_json || {});
		}
		// For numeric features, check the plan property first
		const value = (plan as unknown as Record<string, number | string>)[key];
		if (typeof value === 'number') return formatNumber(value);
		// Fallback to features_json
		const jsonValue = plan.features_json?.[key];
		if (typeof jsonValue === 'number') return formatNumber(jsonValue);
		return '—';
	}

	function getPlanColor(planName: string): string {
		return planColors[planName] || '#888';
	}
</script>

<svelte:head>
	<title>Plan Management — MESH Dashboard</title>
</svelte:head>

<div class="plans-page">
	<!-- Page Header -->
	<header class="page-header">
		<h1>Plan Management</h1>
		<p class="subtitle">Compare and manage subscription plans</p>
	</header>

	{#if error}
		<div class="error-alert">
			<span>{error}</span>
			<button on:click={loadPlans}>Retry</button>
		</div>
	{/if}

	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<span>Loading plans...</span>
		</div>
	{:else}
		<div class="plans-content">
			<!-- Feature Comparison Matrix -->
			<section class="matrix-section">
				<h3>Feature Comparison</h3>
				<div class="matrix-container">
					<table class="feature-matrix">
						<thead>
							<tr>
								<th class="feature-header">Feature</th>
								{#each sortedPlans as plan}
									<th
										class="plan-header"
										class:current={plan.name === currentPlan}
										style="--plan-color: {getPlanColor(plan.name)}"
									>
										<span class="plan-name">{plan.display_name}</span>
										{#if plan.name === currentPlan}
											<span class="current-badge">Current</span>
										{/if}
									</th>
								{/each}
							</tr>
						</thead>
						<tbody>
							{#each featureRows as feature}
								<tr>
									<td class="feature-label">{feature.label}</td>
									{#each sortedPlans as plan}
										<td class="feature-value" class:current={plan.name === currentPlan}>
											{#if feature.format === 'boolean'}
												{@const value = getFeatureValue(plan, feature.key, feature.format)}
												{#if value}
													<svg class="check-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke={getPlanColor(plan.name)} stroke-width="2">
														<polyline points="20 6 9 17 4 12"/>
													</svg>
												{:else}
													<span class="dash">—</span>
												{/if}
											{:else}
												<span class="mono">{getFeatureValue(plan, feature.key, feature.format)}</span>
											{/if}
										</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>

			<!-- Plan Cards -->
			<section class="cards-section">
				<h3>Plan Details</h3>
				<div class="plans-grid">
					{#each sortedPlans as plan}
						<div
							class="plan-card"
							class:current={plan.name === currentPlan}
							style="--plan-color: {getPlanColor(plan.name)}"
						>
							{#if plan.name === currentPlan}
								<span class="card-current-badge">Current</span>
							{/if}
							<div class="card-header">
								<h4>{plan.display_name}</h4>
								<div class="card-price">
									<span class="price-value">{formatCurrency(plan.monthly_price)}</span>
									<span class="price-period">/mo</span>
								</div>
							</div>
							<p class="card-description">{plan.description}</p>
							<ul class="card-features">
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
						</div>
					{/each}
				</div>
			</section>
		</div>
	{/if}
</div>

<style>
	.plans-page {
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

	h3 {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 20px 0;
		letter-spacing: 0.5px;
	}

	h4 {
		font-family: var(--font-heading);
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--text);
		margin: 0;
		letter-spacing: 0.5px;
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

	/* Matrix Section */
	.matrix-section {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
		margin-bottom: 24px;
	}

	.matrix-container {
		overflow-x: auto;
	}

	.feature-matrix {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
		min-width: 600px;
	}

	.feature-matrix th {
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-align: center;
		padding: 16px 12px;
		border-bottom: 1px solid var(--border);
		background: var(--bg-elevated);
	}

	.feature-matrix th.feature-header {
		text-align: left;
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.feature-matrix th.plan-header {
		color: var(--plan-color, var(--text));
		position: relative;
	}

	.feature-matrix th.plan-header.current {
		background: rgba(255, 111, 0, 0.08);
		border-bottom: 2px solid var(--accent);
	}

	.plan-name {
		display: block;
		margin-bottom: 4px;
	}

	.current-badge {
		display: inline-block;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		color: var(--accent);
		background: rgba(255, 111, 0, 0.15);
		padding: 2px 8px;
		border-radius: 2px;
	}

	.feature-matrix td {
		padding: 14px 12px;
		border-bottom: 1px solid var(--border);
		text-align: center;
	}

	.feature-matrix td.feature-label {
		text-align: left;
		color: var(--text-secondary);
		font-family: var(--font-heading);
		font-size: 0.8rem;
	}

	.feature-matrix td.feature-value {
		color: var(--text);
	}

	.feature-matrix td.feature-value.current {
		background: rgba(255, 111, 0, 0.05);
	}

	.feature-matrix tbody tr:hover td {
		background: var(--bg-elevated);
	}

	.feature-matrix tbody tr:hover td.current {
		background: rgba(255, 111, 0, 0.08);
	}

	.check-icon {
		margin: 0 auto;
	}

	.dash {
		color: var(--text-dim);
	}

	.mono {
		font-family: var(--font-mono);
		font-size: 0.85rem;
	}

	/* Cards Section */
	.cards-section {
		margin-bottom: 24px;
	}

	.plans-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 16px;
	}

	.plan-card {
		background: var(--bg-surface);
		border: 2px solid var(--border);
		border-radius: 6px;
		padding: 24px;
		position: relative;
		transition: border-color 0.2s;
	}

	.plan-card.current {
		border-color: var(--plan-color, var(--accent));
	}

	.card-current-badge {
		position: absolute;
		top: -10px;
		right: 16px;
		background: var(--plan-color, var(--accent));
		color: #fff;
		font-family: var(--font-heading);
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		padding: 4px 12px;
		border-radius: 2px;
	}

	.card-header {
		margin-bottom: 12px;
	}

	.card-price {
		margin-top: 8px;
	}

	.price-value {
		font-family: var(--font-mono);
		font-size: 1.75rem;
		font-weight: 600;
		color: var(--plan-color, var(--text));
	}

	.price-period {
		font-family: var(--font-mono);
		font-size: 0.9rem;
		color: var(--text-secondary);
		font-weight: 400;
	}

	.card-description {
		font-size: 0.85rem;
		color: var(--text-dim);
		margin: 0 0 20px 0;
		line-height: 1.5;
	}

	.card-features {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.card-features li {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: 10px;
	}

	.card-features li svg {
		color: var(--green);
		flex-shrink: 0;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.plans-page {
			padding: 16px;
		}

		.plans-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
