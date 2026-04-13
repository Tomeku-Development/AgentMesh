<script lang="ts">
	import { onMount } from 'svelte';
	import { getAPIKeys, createAPIKey, revokeAPIKey } from '$lib/api/apikeys';
	import { activeWorkspaceId } from '$lib/stores/workspace';
	import { get } from 'svelte/store';
	import type { APIKey, APIKeyCreated } from '$lib/types/api';

	let keys: APIKey[] = [];
	let loading = true;
	let error = '';
	let showGenerate = false;
	let newKeyName = 'Default';
	let newKeyScopes: string[] = ['read', 'write'];
	let newKeyExpiry: number | null = null;
	let generating = false;
	let generatedKey: APIKeyCreated | null = null;
	let revoking: string | null = null;
	let confirmRevoke: string | null = null;

	$: workspaceId = get(activeWorkspaceId) || 'default';

	onMount(async () => {
		await loadKeys();
	});

	async function loadKeys() {
		loading = true;
		error = '';
		try {
			const response = await getAPIKeys(workspaceId);
			keys = response.keys || [];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load API keys';
		} finally {
			loading = false;
		}
	}

	async function handleGenerate() {
		generating = true;
		try {
			const response = await createAPIKey(workspaceId, {
				name: newKeyName,
				scopes: newKeyScopes,
				expires_in_days: newKeyExpiry
			});
			generatedKey = response;
			showGenerate = false;
			newKeyName = 'Default';
			newKeyScopes = ['read', 'write'];
			newKeyExpiry = null;
			await loadKeys();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to generate API key';
		} finally {
			generating = false;
		}
	}

	async function handleRevoke(keyId: string) {
		revoking = keyId;
		try {
			await revokeAPIKey(workspaceId, keyId);
			keys = keys.filter(k => k.id !== keyId);
			confirmRevoke = null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to revoke API key';
		} finally {
			revoking = null;
		}
	}

	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
	}

	function toggleScope(scope: string) {
		if (newKeyScopes.includes(scope)) {
			newKeyScopes = newKeyScopes.filter(s => s !== scope);
		} else {
			newKeyScopes = [...newKeyScopes, scope];
		}
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return 'Never';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
	}

	function isExpired(dateStr: string | null): boolean {
		if (!dateStr) return false;
		return new Date(dateStr) < new Date();
	}

	function formatScopes(scopes: string): string[] {
		return scopes ? scopes.split(',').map(s => s.trim()) : [];
	}
</script>

<svelte:head>
	<title>Settings — MESH Dashboard</title>
</svelte:head>

<div class="settings-page">
	<h1>Settings</h1>

	<section class="api-keys-section">
		<h2>API Keys</h2>
		<p class="subtitle">Manage API keys for SDK and IoT agent connections</p>

		{#if generatedKey}
			<div class="generated-key-banner">
				<div class="banner-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
					</svg>
				</div>
				<div class="banner-content">
					<h3>Your API key has been generated</h3>
					<p>Copy it now — it won't be shown again.</p>
					<div class="raw-key-display">
						<code>{generatedKey.raw_key}</code>
						<button class="copy-btn" on:click={() => { if (generatedKey) copyToClipboard(generatedKey.raw_key); }}>
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
								<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
							</svg>
							Copy
						</button>
					</div>
				</div>
				<button class="dismiss-btn" on:click={() => generatedKey = null}>
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<line x1="18" y1="6" x2="6" y2="18"/>
						<line x1="6" y1="6" x2="18" y2="18"/>
					</svg>
				</button>
			</div>
		{/if}

		{#if error}
			<div class="error-alert">
				<span>{error}</span>
				<button on:click={loadKeys}>Retry</button>
			</div>
		{/if}

		{#if loading}
			<div class="loading-state">
				<div class="spinner"></div>
				<span>Loading API keys...</span>
			</div>
		{:else}
			<div class="generate-section">
				{#if showGenerate}
					<div class="generate-form">
						<div class="form-row">
							<label for="key-name">Key Name</label>
							<input
								id="key-name"
								type="text"
								bind:value={newKeyName}
								placeholder="Enter key name"
							/>
						</div>
						<div class="form-row">
							<span class="form-label">Scopes</span>
							<div class="scope-checkboxes" id="scopes-group">
								<label class="checkbox-label">
									<input
										type="checkbox"
										checked={newKeyScopes.includes('read')}
										on:change={() => toggleScope('read')}
									/>
									<span>read</span>
								</label>
								<label class="checkbox-label">
									<input
										type="checkbox"
										checked={newKeyScopes.includes('write')}
										on:change={() => toggleScope('write')}
									/>
									<span>write</span>
								</label>
								<label class="checkbox-label">
									<input
										type="checkbox"
										checked={newKeyScopes.includes('admin')}
										on:change={() => toggleScope('admin')}
									/>
									<span>admin</span>
								</label>
							</div>
						</div>
						<div class="form-row">
							<label for="expiry">Expiry</label>
							<select id="expiry" bind:value={newKeyExpiry}>
								<option value={null}>Never</option>
								<option value={30}>30 days</option>
								<option value={90}>90 days</option>
								<option value={365}>1 year</option>
							</select>
						</div>
						<div class="form-actions">
							<button
								class="generate-btn"
								on:click={handleGenerate}
								disabled={generating || newKeyScopes.length === 0}
							>
								{generating ? 'Generating...' : 'Generate Key'}
							</button>
							<button class="cancel-btn" on:click={() => showGenerate = false} disabled={generating}>
								Cancel
							</button>
						</div>
					</div>
				{:else}
					<button class="generate-new-btn" on:click={() => showGenerate = true}>
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<line x1="12" y1="5" x2="12" y2="19"/>
							<line x1="5" y1="12" x2="19" y2="12"/>
						</svg>
						Generate New Key
					</button>
				{/if}
			</div>

			{#if keys.length === 0 && !showGenerate}
				<div class="empty-state">
					<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/>
					</svg>
					<h3>No API keys</h3>
					<p>Generate your first API key to connect SDK and IoT agents.</p>
				</div>
			{:else if keys.length > 0}
				<div class="table-container">
					<table class="keys-table">
						<thead>
							<tr>
								<th>Name</th>
								<th>Key Prefix</th>
								<th>Scopes</th>
								<th>Created</th>
								<th>Expires</th>
								<th>Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each keys as key}
								<tr>
									<td class="name-cell">{key.name}</td>
									<td class="prefix-cell">
										<code>{key.key_prefix}...</code>
									</td>
									<td class="scopes-cell">
										{#each formatScopes(key.scopes) as scope}
											<span class="scope-tag">{scope}</span>
										{/each}
									</td>
									<td class="date-cell">{formatDate(key.created_at)}</td>
									<td class="date-cell" class:expired={isExpired(key.expires_at)}>
										{formatDate(key.expires_at)}
										{#if isExpired(key.expires_at)}
											<span class="expired-label">(expired)</span>
										{/if}
									</td>
									<td class="actions-cell">
										{#if confirmRevoke === key.id}
											<div class="confirm-revoke">
												<span>Are you sure?</span>
												<button
													class="confirm-yes"
													on:click={() => handleRevoke(key.id)}
													disabled={revoking === key.id}
												>
													Yes
												</button>
												<button
													class="confirm-no"
													on:click={() => confirmRevoke = null}
													disabled={revoking === key.id}
												>
													No
												</button>
											</div>
										{:else}
											<button
												class="revoke-btn"
												on:click={() => confirmRevoke = key.id}
												disabled={revoking === key.id}
											>
												{#if revoking === key.id}
													<div class="btn-spinner"></div>
												{:else}
													Revoke
												{/if}
											</button>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{/if}
	</section>
</div>

<style>
	.settings-page {
		padding: 32px 40px;
		max-width: 1200px;
		margin: 0 auto;
	}

	h1 {
		font-family: var(--font-heading);
		font-size: 2rem;
		font-weight: 700;
		color: var(--text);
		margin-bottom: 32px;
		letter-spacing: 1px;
	}

	h2 {
		font-family: var(--font-heading);
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text);
		margin-bottom: 8px;
		letter-spacing: 0.5px;
	}

	.subtitle {
		color: var(--text-secondary);
		font-size: 0.875rem;
		margin-bottom: 24px;
	}

	/* Generated Key Banner */
	.generated-key-banner {
		display: flex;
		align-items: flex-start;
		gap: 16px;
		background: rgba(74, 222, 128, 0.08);
		border: 1px solid rgba(74, 222, 128, 0.2);
		border-radius: 4px;
		padding: 20px;
		margin-bottom: 24px;
	}

	.banner-icon {
		color: var(--green);
		flex-shrink: 0;
	}

	.banner-content {
		flex: 1;
	}

	.banner-content h3 {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--green);
		margin-bottom: 4px;
	}

	.banner-content p {
		color: var(--text-secondary);
		font-size: 0.875rem;
		margin-bottom: 12px;
	}

	.raw-key-display {
		display: flex;
		align-items: center;
		gap: 12px;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 12px 16px;
	}

	.raw-key-display code {
		font-family: var(--font-mono);
		font-size: 0.875rem;
		color: var(--text);
		word-break: break-all;
		flex: 1;
	}

	.copy-btn {
		display: flex;
		align-items: center;
		gap: 6px;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 3px;
		padding: 8px 16px;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		cursor: pointer;
		transition: background 0.2s;
		flex-shrink: 0;
	}

	.copy-btn:hover {
		background: var(--accent-hover);
	}

	.dismiss-btn {
		background: transparent;
		border: none;
		color: var(--text-dim);
		cursor: pointer;
		padding: 4px;
		transition: color 0.2s;
	}

	.dismiss-btn:hover {
		color: var(--text);
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
		padding: 48px;
		color: var(--text-secondary);
		font-size: 0.875rem;
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

	/* Generate Section */
	.generate-section {
		margin-bottom: 24px;
	}

	.generate-new-btn {
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

	.generate-new-btn:hover {
		background: var(--accent-hover);
	}

	.generate-form {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 24px;
	}

	.form-row {
		margin-bottom: 20px;
	}

	.form-row:last-of-type {
		margin-bottom: 0;
	}

	.form-row label,
	.form-label {
		display: block;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--text-secondary);
		letter-spacing: 0.5px;
		margin-bottom: 8px;
		text-transform: uppercase;
	}

	.form-row input[type="text"],
	.form-row select {
		width: 100%;
		max-width: 300px;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 10px 14px;
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text);
		transition: border-color 0.2s;
	}

	.form-row input[type="text"]:focus,
	.form-row select:focus {
		outline: none;
		border-color: var(--accent);
	}

	.form-row select {
		cursor: pointer;
	}

	.scope-checkboxes {
		display: flex;
		gap: 20px;
		flex-wrap: wrap;
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
	}

	.checkbox-label input[type="checkbox"] {
		width: 16px;
		height: 16px;
		accent-color: var(--accent);
		cursor: pointer;
	}

	.checkbox-label span {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		color: var(--text);
	}

	.form-actions {
		display: flex;
		gap: 12px;
		margin-top: 24px;
	}

	.generate-btn {
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
		transition: background 0.2s, opacity 0.2s;
	}

	.generate-btn:hover:not(:disabled) {
		background: var(--accent-hover);
	}

	.generate-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.cancel-btn {
		background: transparent;
		color: var(--text-secondary);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 10px 20px;
		font-family: var(--font-heading);
		font-size: 0.8rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		cursor: pointer;
		transition: border-color 0.2s, color 0.2s;
	}

	.cancel-btn:hover:not(:disabled) {
		border-color: var(--border-strong);
		color: var(--text);
	}

	.cancel-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
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
		margin-bottom: 8px;
	}

	.empty-state p {
		font-size: 0.875rem;
		max-width: 280px;
	}

	/* Table */
	.table-container {
		overflow-x: auto;
		border: 1px solid var(--border);
		border-radius: 4px;
	}

	.keys-table {
		width: 100%;
		border-collapse: collapse;
	}

	.keys-table th {
		background: var(--bg-elevated);
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 1px;
		color: var(--text-secondary);
		text-align: left;
		padding: 12px 16px;
		border-bottom: 1px solid var(--border);
		text-transform: uppercase;
	}

	.keys-table td {
		padding: 14px 16px;
		border-bottom: 1px solid var(--border);
		font-size: 0.875rem;
		color: var(--text);
	}

	.keys-table tbody tr:last-child td {
		border-bottom: none;
	}

	.keys-table tbody tr:hover {
		background: var(--bg-elevated);
	}

	.name-cell {
		font-weight: 500;
	}

	.prefix-cell code {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		background: var(--bg-surface);
		padding: 4px 8px;
		border-radius: 3px;
		color: var(--text-secondary);
	}

	.scopes-cell {
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
	}

	.scope-tag {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		background: var(--accent-dim);
		color: var(--accent);
		padding: 3px 8px;
		border-radius: 2px;
		letter-spacing: 0.3px;
	}

	.date-cell {
		color: var(--text-secondary);
		font-size: 0.8rem;
		white-space: nowrap;
	}

	.date-cell.expired {
		color: var(--red);
	}

	.expired-label {
		font-size: 0.7rem;
		margin-left: 4px;
	}

	.actions-cell {
		white-space: nowrap;
	}

	.revoke-btn {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		color: var(--red);
		padding: 6px 14px;
		border-radius: 3px;
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		min-width: 70px;
		height: 30px;
		transition: background 0.2s;
	}

	.revoke-btn:hover:not(:disabled) {
		background: rgba(239, 68, 68, 0.15);
	}

	.revoke-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-spinner {
		width: 14px;
		height: 14px;
		border: 2px solid rgba(239, 68, 68, 0.3);
		border-top-color: var(--red);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.confirm-revoke {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.confirm-revoke span {
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	.confirm-yes,
	.confirm-no {
		padding: 5px 12px;
		border-radius: 3px;
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 500;
		cursor: pointer;
	}

	.confirm-yes {
		background: var(--red);
		border: none;
		color: #fff;
	}

	.confirm-yes:hover:not(:disabled) {
		opacity: 0.9;
	}

	.confirm-no {
		background: transparent;
		border: 1px solid var(--border);
		color: var(--text-secondary);
	}

	.confirm-no:hover:not(:disabled) {
		border-color: var(--border-strong);
		color: var(--text);
	}

	.confirm-yes:disabled,
	.confirm-no:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
