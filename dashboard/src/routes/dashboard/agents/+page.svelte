<script lang="ts">
	import { onMount } from 'svelte';
	import { getAgents, getAgentStatus } from '$lib/api/agents';
	import type { Agent, AgentStatus } from '$lib/types/api';

	const WORKSPACE_ID = 'default';

	let agents: Agent[] = [];
	let loading = true;
	let error: string | null = null;
	let expandedAgentId: string | null = null;
	let agentStatusMap = new Map<string, AgentStatus[]>();
	let loadingStatus = new Set<string>();

	const roleColors: Record<string, string> = {
		buyer: '#ff6f00',
		supplier: '#4ade80',
		logistics: '#60a5fa',
		inspector: '#c084fc',
		oracle: '#fbbf24'
	};

	const statusColors: Record<string, string> = {
		online: '#4ade80',
		busy: '#fbbf24',
		suspect: '#ff6f00',
		dead: '#ef4444'
	};

	function getRoleColor(role: string): string {
		return roleColors[role.toLowerCase()] || '#9a9a9e';
	}

	function getStatusColor(status: string): string {
		return statusColors[status.toLowerCase()] || '#9a9a9e';
	}

	function formatBalance(balance: number): string {
		return `${balance.toLocaleString()} MESH`;
	}

	function formatRelativeTime(timestamp: string): string {
		const date = new Date(timestamp);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffSecs = Math.floor(diffMs / 1000);
		const diffMins = Math.floor(diffSecs / 60);
		const diffHours = Math.floor(diffMins / 60);
		const diffDays = Math.floor(diffHours / 24);

		if (diffDays > 0) return `${diffDays}d ago`;
		if (diffHours > 0) return `${diffHours}h ago`;
		if (diffMins > 0) return `${diffMins}m ago`;
		return 'just now';
	}

	function formatTimestamp(timestamp: string): string {
		const date = new Date(timestamp);
		return date.toLocaleString('en-US', {
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit'
		});
	}

	function truncateMeshId(meshId: string): string {
		if (meshId.length <= 16) return meshId;
		return `${meshId.slice(0, 8)}...${meshId.slice(-8)}`;
	}

	function parseCapabilities(capabilities: string): string[] {
		try {
			const parsed = JSON.parse(capabilities);
			return Array.isArray(parsed) ? parsed : [capabilities];
		} catch {
			return capabilities.split(',').map(c => c.trim()).filter(Boolean);
		}
	}

	async function loadAgents() {
		loading = true;
		error = null;
		try {
			const response = await getAgents(WORKSPACE_ID);
			agents = response.agents;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load agents';
		} finally {
			loading = false;
		}
	}

	async function toggleAgentDetails(agent: Agent) {
		if (expandedAgentId === agent.id) {
			expandedAgentId = null;
			return;
		}

		expandedAgentId = agent.id;

		if (!agentStatusMap.has(agent.id) && !loadingStatus.has(agent.id)) {
			loadingStatus.add(agent.id);
			loadingStatus = loadingStatus;
			try {
				const statusHistory = await getAgentStatus(WORKSPACE_ID, agent.id);
				agentStatusMap.set(agent.id, statusHistory);
				agentStatusMap = agentStatusMap;
			} catch (err) {
				console.error('Failed to load agent status:', err);
			} finally {
				loadingStatus.delete(agent.id);
				loadingStatus = loadingStatus;
			}
		}
	}

	function handleAgentKeyDown(event: KeyboardEvent, agent: Agent) {
		if (event.key === 'Enter') {
			toggleAgentDetails(agent);
		}
	}

	function getLatestStatus(agentId: string): AgentStatus | null {
		const history = agentStatusMap.get(agentId);
		return history && history.length > 0 ? history[0] : null;
	}

	onMount(() => {
		loadAgents();
	});
</script>

<svelte:head>
	<title>Agents — MESH Dashboard</title>
</svelte:head>

<div class="agents-page">
	<!-- Page Header -->
	<header class="page-header">
		<div class="header-content">
			<div class="header-title-row">
				<div class="header-title">
					<h1>Agents</h1>
					<span class="agent-count-badge">{agents.length}</span>
				</div>
				<a href="/dashboard/connect/" class="connect-btn">+ Connect Agent</a>
			</div>
			<p class="header-subtitle">Manage and monitor autonomous agents in your workspace</p>
		</div>
	</header>

	<!-- Content -->
	<div class="page-content">
		{#if loading}
			<div class="loading-state">
				<div class="spinner"></div>
				<p>Loading agents...</p>
			</div>
		{:else if error}
			<div class="error-state">
				<div class="error-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
						<circle cx="12" cy="12" r="10" stroke="#ef4444" stroke-width="2"/>
						<path d="M12 8v5M12 16h.01" stroke="#ef4444" stroke-width="2" stroke-linecap="round"/>
					</svg>
				</div>
				<p class="error-message">{error}</p>
				<button class="retry-button" on:click={loadAgents}>Retry</button>
			</div>
		{:else if agents.length === 0}
			<div class="empty-state">
				<div class="empty-illustration">
					<svg width="64" height="64" viewBox="0 0 24 24" fill="none">
						<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="#6b6b70" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>
				<h3>No agents found</h3>
				<p>Connect your first agent using the SDK</p>
				<a href="/dashboard/connect/" class="connect-btn empty">Connect Your First Agent</a>
			</div>
		{:else}
			<div class="agents-table-container">
				<table class="agents-table">
					<thead>
						<tr>
							<th>Role</th>
							<th>Mesh ID</th>
							<th>Capabilities</th>
							<th>Balance</th>
							<th>Status</th>
							<th>Active Orders</th>
							<th>Created</th>
						</tr>
					</thead>
					<tbody>
						{#each agents as agent}
							{@const roleColor = getRoleColor(agent.agent_role)}
							{@const latestStatus = getLatestStatus(agent.id)}
							{@const statusColor = latestStatus ? getStatusColor(latestStatus.status) : '#9a9a9e'}
							<tr
								class="agent-row"
								class:expanded={expandedAgentId === agent.id}
								on:click={() => toggleAgentDetails(agent)}
								on:keydown={(e) => handleAgentKeyDown(e, agent)}
								role="button"
								tabindex="0"
							>
								<td>
									<span
										class="role-badge"
										style="background: {roleColor}26; color: {roleColor}"
									>
										{agent.agent_role}
									</span>
								</td>
								<td>
									<code class="mesh-id" title={agent.agent_mesh_id}>
										{truncateMeshId(agent.agent_mesh_id)}
									</code>
								</td>
								<td>
									<div class="capabilities-list">
										{#each parseCapabilities(agent.capabilities).slice(0, 3) as cap}
											<span class="capability-tag">{cap}</span>
										{/each}
										{#if parseCapabilities(agent.capabilities).length > 3}
											<span class="capability-tag more">
												+{parseCapabilities(agent.capabilities).length - 3}
											</span>
										{/if}
									</div>
								</td>
								<td>
									<span class="balance">{formatBalance(agent.initial_balance)}</span>
								</td>
								<td>
									<div class="status-indicator">
										<span class="status-dot" style="background: {statusColor}"></span>
										<span class="status-label" style="color: {statusColor}">
											{latestStatus?.status || 'unknown'}
										</span>
									</div>
								</td>
								<td>
									<span class="order-count">{latestStatus?.active_orders || 0}</span>
								</td>
								<td>
									<span class="created-time">{formatRelativeTime(agent.created_at)}</span>
								</td>
							</tr>
							{#if expandedAgentId === agent.id}
								<tr class="detail-row">
									<td colspan="7">
										<div class="agent-details">
											{#if loadingStatus.has(agent.id)}
												<div class="details-loading">
													<div class="spinner-small"></div>
													<p>Loading status history...</p>
												</div>
											{:else}
												{@const statusHistory = agentStatusMap.get(agent.id) || []}
												<div class="details-grid">
													<div class="detail-section">
														<h4>Status History</h4>
														{#if statusHistory.length > 0}
															<div class="status-timeline">
																{#each statusHistory.slice(0, 10) as status, i}
																	<div class="timeline-item">
																		<span class="timeline-dot" style="background: {getStatusColor(status.status)}"></span>
																		<div class="timeline-content">
																			<span class="timeline-status" style="color: {getStatusColor(status.status)}">
																				{status.status}
																			</span>
																			<span class="timeline-time">{formatTimestamp(status.recorded_at)}</span>
																		</div>
																		{#if i < statusHistory.length - 1}
																			<div class="timeline-line"></div>
																		{/if}
																	</div>
																{/each}
															</div>
														{:else}
															<p class="no-data">No status history available</p>
														{/if}
													</div>
													<div class="detail-metrics">
														<div class="metric-card">
															<span class="metric-label">Current Load</span>
															<div class="metric-value">
																<span class="metric-number">{latestStatus?.load || 0}%</span>
															</div>
															<div class="load-bar">
																<div
																	class="load-bar-fill"
																	style="width: {latestStatus?.load || 0}%; background: {getStatusColor(latestStatus?.status || 'unknown')}"
																></div>
															</div>
														</div>
														<div class="metric-card">
															<span class="metric-label">Active Orders</span>
															<span class="metric-number">{latestStatus?.active_orders || 0}</span>
														</div>
														<div class="metric-card">
															<span class="metric-label">Total Status Records</span>
															<span class="metric-number">{statusHistory.length}</span>
														</div>
													</div>
												</div>
											{/if}
										</div>
									</td>
								</tr>
							{/if}
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<style>
	.agents-page {
		padding: 28px;
		max-width: 1400px;
		margin: 0 auto;
	}

	/* ── Page Header ─────────────────────────── */
	.page-header {
		margin-bottom: 24px;
	}

	.header-content {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.header-title-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		flex-wrap: wrap;
	}

	.header-title {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.connect-btn {
		display: inline-flex;
		align-items: center;
		padding: 10px 20px;
		background: var(--accent);
		color: #fff;
		border-radius: 4px;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-decoration: none;
		transition: opacity 0.2s;
	}

	.connect-btn:hover {
		opacity: 0.9;
	}

	.connect-btn.empty {
		margin-top: 16px;
	}

	.header-title h1 {
		font-family: var(--font-heading);
		font-size: 1.75rem;
		font-weight: 600;
		color: var(--text);
		letter-spacing: 0.5px;
	}

	.agent-count-badge {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--accent);
		background: var(--accent-dim);
		padding: 4px 10px;
		border-radius: 12px;
	}

	.header-subtitle {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
	}

	/* ── Loading State ───────────────────────── */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 80px 20px;
		gap: 16px;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.spinner-small {
		width: 24px;
		height: 24px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.loading-state p {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
	}

	/* ── Error State ─────────────────────────── */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 60px 20px;
		gap: 16px;
		background: rgba(239, 68, 68, 0.05);
		border: 1px solid rgba(239, 68, 68, 0.2);
		border-radius: 8px;
	}

	.error-message {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: #ef4444;
		text-align: center;
	}

	.retry-button {
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 1px;
		color: var(--text);
		background: var(--bg-surface);
		border: 1px solid var(--border);
		padding: 10px 24px;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.retry-button:hover {
		background: var(--bg-elevated);
		border-color: var(--border-strong);
	}

	/* ── Empty State ─────────────────────────── */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 80px 20px;
		gap: 16px;
	}

	.empty-illustration {
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--bg-elevated);
		border-radius: 50%;
		border: 1px solid var(--border);
	}

	.empty-state h3 {
		font-family: var(--font-heading);
		font-size: 1.125rem;
		font-weight: 500;
		color: var(--text);
	}

	.empty-state p {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
	}

	/* ── Agents Table ────────────────────────── */
	.agents-table-container {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 8px;
		overflow: hidden;
	}

	.agents-table {
		width: 100%;
		border-collapse: collapse;
		font-family: var(--font-body);
		font-size: 0.8125rem;
	}

	.agents-table thead {
		background: var(--bg-surface);
	}

	.agents-table th {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 1px;
		color: var(--text-secondary);
		text-align: left;
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
		text-transform: uppercase;
	}

	.agents-table td {
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
		color: var(--text);
	}

	.agent-row {
		cursor: pointer;
		transition: background 0.15s;
	}

	.agent-row:hover {
		background: var(--bg-surface);
	}

	.agent-row.expanded {
		background: var(--bg-surface);
	}

	/* ── Role Badge ──────────────────────────── */
	.role-badge {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		padding: 4px 10px;
		border-radius: 4px;
	}

	/* ── Mesh ID ─────────────────────────────── */
	.mesh-id {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-secondary);
		background: var(--bg);
		padding: 4px 8px;
		border-radius: 4px;
		border: 1px solid var(--border);
	}

	/* ── Capabilities ────────────────────────── */
	.capabilities-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.capability-tag {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		color: var(--text-secondary);
		background: var(--bg);
		padding: 3px 8px;
		border-radius: 3px;
		border: 1px solid var(--border);
	}

	.capability-tag.more {
		color: var(--text-dim);
		background: transparent;
		border-style: dashed;
	}

	/* ── Balance ─────────────────────────────── */
	.balance {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--text);
		font-weight: 500;
	}

	/* ── Status Indicator ────────────────────── */
	.status-indicator {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.status-label {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
	}

	/* ── Order Count ─────────────────────────── */
	.order-count {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--text);
	}

	/* ── Created Time ────────────────────────── */
	.created-time {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-dim);
	}

	/* ── Detail Row ──────────────────────────── */
	.detail-row {
		background: var(--bg);
	}

	.detail-row td {
		padding: 0;
		border-bottom: 1px solid var(--border);
	}

	.agent-details {
		padding: 24px;
	}

	.details-loading {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 20px;
	}

	.details-loading p {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
	}

	.details-grid {
		display: grid;
		grid-template-columns: 1fr 280px;
		gap: 32px;
	}

	.detail-section h4 {
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 1px;
		color: var(--text-secondary);
		text-transform: uppercase;
		margin-bottom: 16px;
	}

	.no-data {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-dim);
		font-style: italic;
	}

	/* ── Status Timeline ─────────────────────── */
	.status-timeline {
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.timeline-item {
		position: relative;
		padding-left: 20px;
		padding-bottom: 16px;
	}

	.timeline-dot {
		position: absolute;
		left: 0;
		top: 4px;
		width: 8px;
		height: 8px;
		border-radius: 50%;
	}

	.timeline-line {
		position: absolute;
		left: 3px;
		top: 16px;
		bottom: 0;
		width: 2px;
		background: var(--border);
	}

	.timeline-content {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.timeline-status {
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
	}

	.timeline-time {
		font-family: var(--font-mono);
		font-size: 0.6875rem;
		color: var(--text-dim);
	}

	/* ── Detail Metrics ──────────────────────── */
	.detail-metrics {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.metric-card {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.metric-label {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.metric-value {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.metric-number {
		font-family: var(--font-mono);
		font-size: 1.5rem;
		font-weight: 600;
		color: var(--text);
	}

	.load-bar {
		width: 100%;
		height: 6px;
		background: var(--bg-surface);
		border-radius: 3px;
		overflow: hidden;
	}

	.load-bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	/* ── Responsive ──────────────────────────── */
	@media (max-width: 768px) {
		.agents-page {
			padding: 16px;
		}

		.agents-table-container {
			background: transparent;
			border: none;
		}

		.agents-table thead {
			display: none;
		}

		.agents-table tbody {
			display: flex;
			flex-direction: column;
			gap: 12px;
		}

		.agents-table tr {
			display: block;
			background: var(--bg-elevated);
			border: 1px solid var(--border);
			border-radius: 8px;
			overflow: hidden;
		}

		.agents-table td {
			display: flex;
			justify-content: space-between;
			align-items: center;
			padding: 12px 16px;
			border-bottom: 1px solid var(--border);
		}

		.agents-table td::before {
			content: attr(data-label);
			font-family: var(--font-heading);
			font-size: 0.6875rem;
			font-weight: 500;
			letter-spacing: 0.5px;
			color: var(--text-secondary);
			text-transform: uppercase;
		}

		.agents-table td:last-child {
			border-bottom: none;
		}

		.detail-row {
			display: block !important;
		}

		.detail-row td {
			display: block;
			padding: 0;
		}

		.agent-details {
			padding: 16px;
		}

		.details-grid {
			grid-template-columns: 1fr;
			gap: 24px;
		}
	}
</style>
