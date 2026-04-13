<script lang="ts">
	import { onMount } from 'svelte';
	import { getCapabilities, createCapability, deleteCapability } from '$lib/api/capabilities';
	import { activeWorkspaceId } from '$lib/stores/workspace';
	import { get } from 'svelte/store';
	import type { Capability } from '$lib/types/api';

	const categories = ['domain', 'process', 'iot', 'logistics', 'quality', 'market'] as const;
	const roles = ['buyer', 'supplier', 'logistics', 'inspector', 'oracle'] as const;

	const categoryColors: Record<string, string> = {
		domain: '#ff6f00',
		process: '#4ade80',
		iot: '#60a5fa',
		logistics: '#818cf8',
		quality: '#c084fc',
		market: '#fbbf24'
	};

	const roleColors: Record<string, string> = {
		buyer: '#ff6f00',
		supplier: '#4ade80',
		logistics: '#60a5fa',
		inspector: '#c084fc',
		oracle: '#fbbf24'
	};

	let capabilities: Capability[] = [];
	let loading = true;
	let error = '';
	let searchQuery = '';
	let selectedCategory = 'all';
	let showAddForm = false;

	// Form state
	let newName = '';
	let newDisplayName = '';
	let newCategory = 'domain';
	let newDescription = '';
	let newRoles: string[] = [];
	let isSubmitting = false;
	let confirmDelete: string | null = null;
	let isDeleting = false;

	$: workspaceId = get(activeWorkspaceId) || 'default';

	// Filtered capabilities
	$: filteredCapabilities = capabilities.filter(cap => {
		const matchesSearch = searchQuery === '' || 
			cap.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			cap.display_name.toLowerCase().includes(searchQuery.toLowerCase());
		const matchesCategory = selectedCategory === 'all' || cap.category === selectedCategory;
		return matchesSearch && matchesCategory;
	});

	// Group by category for counts
	$: categoryCounts = categories.reduce((acc, cat) => {
		acc[cat] = capabilities.filter(c => c.category === cat).length;
		return acc;
	}, {} as Record<string, number>);

	onMount(async () => {
		await loadCapabilities();
	});

	async function loadCapabilities() {
		loading = true;
		error = '';
		try {
			capabilities = await getCapabilities();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load capabilities';
		} finally {
			loading = false;
		}
	}

	function toggleRole(role: string) {
		if (newRoles.includes(role)) {
			newRoles = newRoles.filter(r => r !== role);
		} else {
			newRoles = [...newRoles, role];
		}
	}

	async function handleCreate() {
		if (!newName || !newDisplayName || newRoles.length === 0) return;
		
		isSubmitting = true;
		try {
			const created = await createCapability(workspaceId, {
				name: newName,
				display_name: newDisplayName,
				category: newCategory,
				description: newDescription,
				applicable_roles: newRoles
			});
			capabilities = [...capabilities, created];
			resetForm();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create capability';
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDelete(capId: string) {
		isDeleting = true;
		try {
			await deleteCapability(workspaceId, capId);
			capabilities = capabilities.filter(c => c.id !== capId);
			confirmDelete = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete capability';
		} finally {
			isDeleting = false;
		}
	}

	function resetForm() {
		newName = '';
		newDisplayName = '';
		newCategory = 'domain';
		newDescription = '';
		newRoles = [];
		showAddForm = false;
	}

	function parseApplicableRoles(roles: string): string[] {
		if (!roles) return [];
		return roles.split(',').map(r => r.trim()).filter(Boolean);
	}
</script>

<svelte:head>
	<title>Capabilities — MESH Dashboard</title>
</svelte:head>

<div class="capabilities-page">
	<div class="page-header">
		<div class="header-left">
			<h1>Capabilities</h1>
			<p class="subtitle">Manage agent capabilities and permissions</p>
		</div>
		<div class="header-right">
			<a href="/dashboard/settings/" class="back-link">← Back to Settings</a>
		</div>
	</div>

	{#if error}
		<div class="error-alert">
			<span>{error}</span>
			<button on:click={loadCapabilities}>Retry</button>
		</div>
	{/if}

	<!-- Stats -->
	<div class="stats-bar">
		<span class="stat-total">{capabilities.length} capabilities</span>
		<div class="stat-breakdown">
			{#each categories as cat}
				{#if categoryCounts[cat] > 0}
					<span class="stat-chip" style="--cat-color: {categoryColors[cat]}">
						{categoryCounts[cat]} {cat}
					</span>
				{/if}
			{/each}
		</div>
	</div>

	<!-- Filters -->
	<div class="filters-bar">
		<div class="category-tabs">
			<button
				class="cat-tab"
				class:active={selectedCategory === 'all'}
				on:click={() => selectedCategory = 'all'}
			>
				All
			</button>
			{#each categories as cat}
				<button
					class="cat-tab"
					class:active={selectedCategory === cat}
					style="--cat-color: {categoryColors[cat]}"
					on:click={() => selectedCategory = cat}
				>
					{cat}
				</button>
			{/each}
		</div>
		<input
			type="text"
			class="search-input"
			placeholder="Search capabilities..."
			bind:value={searchQuery}
		/>
	</div>

	<!-- Add Form -->
	<div class="add-section">
		{#if showAddForm}
			<div class="add-form">
				<h3>Add Custom Capability</h3>
				<div class="form-grid">
					<div class="form-group">
						<label for="cap-name">Name</label>
						<input
							id="cap-name"
							type="text"
							bind:value={newName}
							placeholder="e.g., quality_inspect"
						/>
					</div>
					<div class="form-group">
						<label for="cap-display">Display Name</label>
						<input
							id="cap-display"
							type="text"
							bind:value={newDisplayName}
							placeholder="e.g., Quality Inspection"
						/>
					</div>
					<div class="form-group">
						<label for="cap-category">Category</label>
						<select id="cap-category" bind:value={newCategory}>
							{#each categories as cat}
								<option value={cat}>{cat}</option>
							{/each}
						</select>
					</div>
					<div class="form-group full-width">
						<label for="cap-desc">Description</label>
						<textarea
							id="cap-desc"
							bind:value={newDescription}
							placeholder="Describe what this capability enables..."
							rows="2"
						></textarea>
					</div>
					<div class="form-group full-width">
						<label>Applicable Roles</label>
						<div class="roles-grid">
							{#each roles as role}
								<label class="role-checkbox" style="--role-color: {roleColors[role]}">
									<input
										type="checkbox"
										checked={newRoles.includes(role)}
										on:change={() => toggleRole(role)}
									/>
									<span class="role-label">{role}</span>
								</label>
							{/each}
						</div>
					</div>
				</div>
				<div class="form-actions">
					<button
						class="btn-primary"
						on:click={handleCreate}
						disabled={isSubmitting || !newName || !newDisplayName || newRoles.length === 0}
					>
						{isSubmitting ? 'Creating...' : 'Create Capability'}
					</button>
					<button class="btn-secondary" on:click={resetForm} disabled={isSubmitting}>
						Cancel
					</button>
				</div>
			</div>
		{:else}
			<button class="add-btn" on:click={() => showAddForm = true}>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="12" y1="5" x2="12" y2="19"/>
					<line x1="5" y1="12" x2="19" y2="12"/>
				</svg>
				Add Custom Capability
			</button>
		{/if}
	</div>

	<!-- Loading -->
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<span>Loading capabilities...</span>
		</div>
	{:else if filteredCapabilities.length === 0}
		<div class="empty-state">
			<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
				<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
			</svg>
			<h3>No capabilities found</h3>
			<p>{searchQuery ? 'Try a different search term.' : 'Add your first custom capability to get started.'}</p>
			{#if !searchQuery}
				<button class="add-btn" on:click={() => showAddForm = true}>
					Add Custom Capability
				</button>
			{/if}
		</div>
	{:else}
		<div class="capabilities-grid">
			{#each filteredCapabilities as cap}
				<div class="cap-card">
					<div class="cap-header">
						<span class="cap-name">{cap.display_name}</span>
						<span class="cap-category-badge" style="--cat-color: {categoryColors[cap.category] || '#9a9a9e'}">
							{cap.category}
						</span>
					</div>
					<p class="cap-description">{cap.description || 'No description'}</p>
					<div class="cap-meta">
						<code class="cap-id">{cap.name}</code>
						{#if cap.is_system}
							<span class="system-badge">SYSTEM</span>
						{/if}
					</div>
					<div class="cap-roles">
						{#each parseApplicableRoles(cap.applicable_roles) as role}
							<span class="role-badge" style="--role-color: {roleColors[role] || '#9a9a9e'}">
								{role}
							</span>
						{/each}
					</div>
					<div class="cap-actions">
						{#if !cap.is_system}
							{#if confirmDelete === cap.id}
								<div class="confirm-delete">
									<span>Delete?</span>
									<button
										class="btn-danger-sm"
										on:click={() => handleDelete(cap.id)}
										disabled={isDeleting}
									>
										Yes
									</button>
									<button
										class="btn-secondary-sm"
										on:click={() => confirmDelete = null}
										disabled={isDeleting}
									>
										No
									</button>
								</div>
							{:else}
								<button class="btn-delete" on:click={() => confirmDelete = cap.id}>
									<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
										<polyline points="3 6 5 6 21 6"/>
										<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
									</svg>
									Delete
								</button>
							{/if}
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.capabilities-page {
		padding: 32px 40px;
		max-width: 1400px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 24px;
	}

	h1 {
		font-family: var(--font-heading);
		font-size: 2rem;
		font-weight: 700;
		color: var(--text);
		margin: 0 0 8px 0;
		letter-spacing: 1px;
	}

	.subtitle {
		color: var(--text-secondary);
		font-size: 0.875rem;
		margin: 0;
	}

	.back-link {
		color: var(--text-secondary);
		text-decoration: none;
		font-size: 0.875rem;
		transition: color 0.2s;
	}

	.back-link:hover {
		color: var(--accent);
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

	/* Stats Bar */
	.stats-bar {
		display: flex;
		align-items: center;
		gap: 16px;
		margin-bottom: 20px;
	}

	.stat-total {
		font-family: var(--font-heading);
		font-size: 0.875rem;
		color: var(--text-secondary);
	}

	.stat-breakdown {
		display: flex;
		gap: 8px;
	}

	.stat-chip {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		padding: 3px 8px;
		border-radius: 2px;
		background: color-mix(in srgb, var(--cat-color) 15%, transparent);
		color: var(--cat-color);
	}

	/* Filters Bar */
	.filters-bar {
		display: flex;
		gap: 16px;
		margin-bottom: 24px;
		align-items: center;
	}

	.category-tabs {
		display: flex;
		gap: 4px;
		flex-wrap: wrap;
	}

	.cat-tab {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 8px 14px;
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 500;
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.2s;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.cat-tab:hover {
		border-color: var(--border-strong);
		color: var(--text);
	}

	.cat-tab.active {
		background: color-mix(in srgb, var(--cat-color, var(--accent)) 15%, var(--bg-elevated));
		border-color: var(--cat-color, var(--accent));
		color: var(--cat-color, var(--accent));
	}

	.search-input {
		flex: 1;
		max-width: 300px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 10px 14px;
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text);
		transition: border-color 0.2s;
	}

	.search-input:focus {
		outline: none;
		border-color: var(--accent);
	}

	.search-input::placeholder {
		color: var(--text-dim);
	}

	/* Add Section */
	.add-section {
		margin-bottom: 24px;
	}

	.add-btn {
		display: flex;
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
		cursor: pointer;
		transition: background 0.2s;
	}

	.add-btn:hover {
		background: var(--accent-hover);
	}

	.add-form {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
	}

	.add-form h3 {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 20px 0;
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 16px;
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.form-group.full-width {
		grid-column: 1 / -1;
	}

	.form-group label {
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 500;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.form-group input,
	.form-group select,
	.form-group textarea {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 10px 12px;
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text);
		transition: border-color 0.2s;
	}

	.form-group input:focus,
	.form-group select:focus,
	.form-group textarea:focus {
		outline: none;
		border-color: var(--accent);
	}

	.form-group select {
		cursor: pointer;
	}

	.form-group textarea {
		resize: vertical;
		min-height: 60px;
	}

	.roles-grid {
		display: flex;
		gap: 16px;
		flex-wrap: wrap;
	}

	.role-checkbox {
		display: flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
	}

	.role-checkbox input[type="checkbox"] {
		width: 16px;
		height: 16px;
		accent-color: var(--role-color);
		cursor: pointer;
	}

	.role-label {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text);
	}

	.form-actions {
		display: flex;
		gap: 12px;
		margin-top: 20px;
	}

	.btn-primary,
	.btn-secondary {
		padding: 10px 20px;
		border-radius: 3px;
		font-family: var(--font-heading);
		font-size: 0.8rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-primary {
		background: var(--accent);
		color: #fff;
		border: none;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--accent-hover);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: transparent;
		color: var(--text-secondary);
		border: 1px solid var(--border);
	}

	.btn-secondary:hover:not(:disabled) {
		border-color: var(--border-strong);
		color: var(--text);
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
		width: 20px;
		height: 20px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
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
		color: var(--text-dim);
		text-align: center;
	}

	.empty-state svg {
		margin-bottom: 16px;
		opacity: 0.5;
	}

	.empty-state h3 {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-secondary);
		margin: 0 0 8px 0;
	}

	.empty-state p {
		font-size: 0.875rem;
		margin: 0 0 20px 0;
	}

	/* Capabilities Grid */
	.capabilities-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 16px;
	}

	.cap-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 12px;
		transition: border-color 0.2s;
	}

	.cap-card:hover {
		border-color: var(--border-strong);
	}

	.cap-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 12px;
	}

	.cap-name {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text);
	}

	.cap-category-badge {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		font-weight: 600;
		padding: 3px 8px;
		border-radius: 2px;
		background: color-mix(in srgb, var(--cat-color) 15%, transparent);
		color: var(--cat-color);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		flex-shrink: 0;
	}

	.cap-description {
		font-size: 0.8125rem;
		color: var(--text-secondary);
		margin: 0;
		line-height: 1.5;
	}

	.cap-meta {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.cap-id {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-dim);
		background: var(--bg-elevated);
		padding: 4px 8px;
		border-radius: 2px;
	}

	.system-badge {
		font-family: var(--font-heading);
		font-size: 0.6rem;
		font-weight: 600;
		color: var(--text-dim);
		background: var(--bg-elevated);
		padding: 2px 6px;
		border-radius: 2px;
		letter-spacing: 0.5px;
	}

	.cap-roles {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}

	.role-badge {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		padding: 3px 8px;
		border-radius: 2px;
		background: color-mix(in srgb, var(--role-color) 15%, transparent);
		color: var(--role-color);
	}

	.cap-actions {
		display: flex;
		justify-content: flex-end;
		margin-top: auto;
		padding-top: 8px;
		border-top: 1px solid var(--border);
	}

	.btn-delete {
		display: flex;
		align-items: center;
		gap: 6px;
		background: transparent;
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: var(--red);
		padding: 6px 12px;
		border-radius: 3px;
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn-delete:hover {
		background: rgba(239, 68, 68, 0.1);
	}

	.confirm-delete {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.confirm-delete span {
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	.btn-danger-sm,
	.btn-secondary-sm {
		padding: 4px 10px;
		border-radius: 2px;
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 500;
		cursor: pointer;
	}

	.btn-danger-sm {
		background: var(--red);
		border: none;
		color: #fff;
	}

	.btn-secondary-sm {
		background: transparent;
		border: 1px solid var(--border);
		color: var(--text-secondary);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.capabilities-page {
			padding: 16px;
		}

		.page-header {
			flex-direction: column;
			gap: 16px;
		}

		.filters-bar {
			flex-direction: column;
			align-items: stretch;
		}

		.search-input {
			max-width: none;
		}

		.form-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
