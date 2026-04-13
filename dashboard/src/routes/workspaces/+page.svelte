<svelte:head>
	<title>Workspaces — MESH</title>
</svelte:head>

<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { getWorkspaces, createWorkspace } from '$lib/api/workspaces';
	import { getMe } from '$lib/api/auth';
	import { setActiveWorkspace } from '$lib/stores/workspace';
	import { currentUser } from '$lib/stores/auth';
	import type { Workspace } from '$lib/types/api';

	let workspaces: Workspace[] = [];
	let loading = true;
	let error = '';
	let showCreate = false;
	let newName = '';
	let newSlug = '';
	let creating = false;

	onMount(async () => {
		// Load user if not set
		try {
			const user = await getMe();
			currentUser.set(user);
		} catch {
			goto('/auth/login');
			return;
		}
		// Load workspaces
		try {
			const res = await getWorkspaces();
			workspaces = res.workspaces;
			// Auto-show create form if no workspaces
			if (workspaces.length === 0) {
				showCreate = true;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load workspaces';
		} finally {
			loading = false;
		}
	});

	async function handleCreate() {
		if (!newName.trim()) return;
		creating = true;
		try {
			const workspace = await createWorkspace({
				name: newName.trim(),
				slug: newSlug.trim() || undefined
			});
			workspaces = [...workspaces, workspace];
			showCreate = false;
			newName = '';
			newSlug = '';
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create workspace';
		} finally {
			creating = false;
		}
	}

	function selectWorkspace(ws: Workspace) {
		setActiveWorkspace(ws);
		goto('/dashboard/');
	}

	function handleKeyDown(event: KeyboardEvent, ws: Workspace) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			selectWorkspace(ws);
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
</script>

<div class="page">
	<div class="header">
		<h1 class="title">Your Workspaces</h1>
		<p class="subtitle">Select a workspace or create a new one</p>
	</div>

	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading workspaces...</p>
		</div>
	{:else if error}
		<div class="error-alert">
			<p>{error}</p>
			<button class="retry-btn" on:click={() => window.location.reload()}>Retry</button>
		</div>
	{:else}
		<div class="workspaces-grid">
			{#each workspaces as ws}
				<div class="workspace-card" on:click={() => selectWorkspace(ws)} on:keydown={(e) => handleKeyDown(e, ws)} role="button" tabindex="0">
					<h3 class="workspace-name">{ws.name}</h3>
					<code class="workspace-slug">{ws.slug}</code>
					<div class="workspace-meta">
						<span class="plan-badge">{ws.plan.toUpperCase()}</span>
						<span class="max-agents">Up to {ws.max_agents} agents</span>
					</div>
					<div class="workspace-date">
						Created {formatDate(ws.created_at)}
					</div>
				</div>
			{/each}
		</div>

		{#if workspaces.length === 0}
			<div class="empty-state">
				<div class="empty-icon">
					<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
					</svg>
				</div>
				<h3 class="empty-title">No workspaces yet</h3>
				<p class="empty-desc">Create your first workspace to get started</p>
			</div>
		{/if}

		{#if showCreate}
			<div class="create-card">
				<h3 class="create-title">Create Workspace</h3>
				<div class="form-group">
					<label for="name">Name *</label>
					<input
						type="text"
						id="name"
						bind:value={newName}
						placeholder="My Workspace"
						required
					/>
				</div>
				<div class="form-group">
					<label for="slug">Slug</label>
					<input
						type="text"
						id="slug"
						bind:value={newSlug}
						placeholder="my-workspace"
					/>
					<span class="hint">Auto-generated from name if empty</span>
				</div>
				<div class="form-actions">
					<button
						class="create-btn"
						on:click={handleCreate}
						disabled={creating || !newName.trim()}
					>
						{#if creating}
							<span class="btn-spinner"></span>
							Creating...
						{:else}
							Create
						{/if}
					</button>
					{#if workspaces.length > 0}
						<button class="cancel-btn" on:click={() => showCreate = false}>
							Cancel
						</button>
					{/if}
				</div>
			</div>
		{:else}
			<button class="show-create-btn" on:click={() => showCreate = true}>
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="12" y1="5" x2="12" y2="19"/>
					<line x1="5" y1="12" x2="19" y2="12"/>
				</svg>
				Create New Workspace
			</button>
		{/if}
	{/if}
</div>

<style>
	.page {
		max-width: 700px;
		margin: 0 auto;
	}

	.header {
		text-align: center;
		margin-bottom: 40px;
	}

	.title {
		font-family: var(--font-heading);
		font-size: 2rem;
		font-weight: 600;
		color: var(--text);
		margin-bottom: 8px;
	}

	.subtitle {
		font-family: var(--font-body);
		font-size: 1rem;
		color: var(--text-secondary);
	}

	/* ── Loading state ───────────────────────── */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
		padding: 60px 0;
		color: var(--text-secondary);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 2px solid var(--border);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* ── Error state ─────────────────────────── */
	.error-alert {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		border-radius: 8px;
		padding: 20px;
		text-align: center;
		color: var(--red);
		margin-bottom: 24px;
	}

	.retry-btn {
		margin-top: 12px;
		padding: 8px 16px;
		background: transparent;
		border: 1px solid var(--red);
		color: var(--red);
		border-radius: 4px;
		cursor: pointer;
		font-family: var(--font-body);
		font-size: 0.85rem;
		transition: background 0.2s;
	}

	.retry-btn:hover {
		background: rgba(239, 68, 68, 0.1);
	}

	/* ── Workspaces grid ────────────────────── */
	.workspaces-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 16px;
		margin-bottom: 24px;
	}

	@media (max-width: 600px) {
		.workspaces-grid {
			grid-template-columns: 1fr;
		}
	}

	.workspace-card {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 24px;
		cursor: pointer;
		transition: border-color 0.2s, transform 0.2s;
	}

	.workspace-card:hover {
		border-color: var(--accent);
		transform: translateY(-2px);
	}

	.workspace-name {
		font-family: var(--font-heading);
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text);
		margin-bottom: 4px;
	}

	.workspace-slug {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text-dim);
		background: transparent;
	}

	.workspace-meta {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-top: 12px;
		margin-bottom: 8px;
	}

	.plan-badge {
		font-family: var(--font-mono);
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 1px;
		padding: 4px 10px;
		background: var(--accent-dim);
		color: var(--accent);
		border-radius: 2px;
	}

	.max-agents {
		font-family: var(--font-body);
		font-size: 0.8rem;
		color: var(--text-secondary);
	}

	.workspace-date {
		font-family: var(--font-body);
		font-size: 0.75rem;
		color: var(--text-dim);
	}

	/* ── Empty state ─────────────────────────── */
	.empty-state {
		text-align: center;
		padding: 40px 0;
	}

	.empty-icon {
		color: var(--text-dim);
		margin-bottom: 16px;
		opacity: 0.5;
	}

	.empty-title {
		font-family: var(--font-heading);
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text);
		margin-bottom: 8px;
	}

	.empty-desc {
		font-family: var(--font-body);
		font-size: 0.9rem;
		color: var(--text-secondary);
	}

	/* ── Create workspace form ──────────────── */
	.create-card {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 24px;
		margin-top: 24px;
	}

	.create-title {
		font-family: var(--font-heading);
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--text);
		margin-bottom: 20px;
	}

	.form-group {
		margin-bottom: 16px;
	}

	.form-group label {
		display: block;
		font-family: var(--font-body);
		font-size: 0.85rem;
		color: var(--text-secondary);
		margin-bottom: 6px;
	}

	.form-group input {
		width: 100%;
		padding: 10px 12px;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		color: var(--text);
		font-family: var(--font-body);
		font-size: 0.9rem;
		transition: border-color 0.2s;
	}

	.form-group input:focus {
		outline: none;
		border-color: var(--accent);
	}

	.hint {
		display: block;
		font-family: var(--font-body);
		font-size: 0.75rem;
		color: var(--text-dim);
		margin-top: 4px;
	}

	.form-actions {
		display: flex;
		gap: 12px;
		margin-top: 20px;
	}

	.create-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 20px;
		background: var(--accent);
		border: none;
		border-radius: 4px;
		color: white;
		font-family: var(--font-body);
		font-size: 0.9rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}

	.create-btn:hover:not(:disabled) {
		background: var(--accent-hover);
	}

	.create-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	.cancel-btn {
		padding: 10px 20px;
		background: transparent;
		border: 1px solid var(--border);
		border-radius: 4px;
		color: var(--text-secondary);
		font-family: var(--font-body);
		font-size: 0.9rem;
		cursor: pointer;
		transition: color 0.2s, border-color 0.2s;
	}

	.cancel-btn:hover {
		color: var(--text);
		border-color: var(--text-secondary);
	}

	/* ── Show create button ─────────────────── */
	.show-create-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		width: 100%;
		padding: 16px;
		background: transparent;
		border: 1px dashed var(--border);
		border-radius: 8px;
		color: var(--text-secondary);
		font-family: var(--font-body);
		font-size: 0.9rem;
		cursor: pointer;
		transition: color 0.2s, border-color 0.2s;
		margin-top: 24px;
	}

	.show-create-btn:hover {
		color: var(--accent);
		border-color: var(--accent);
	}
</style>
