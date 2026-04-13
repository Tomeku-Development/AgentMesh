<script lang="ts">
	import { browser } from '$app/environment';

	// Toast state
	let showToast = false;
	let toastMessage = '';

	// Section A: LLM Preferences
	let preferredModel = 'claude-3-haiku';
	let temperature = 0.3;
	let maxTokens = 1024;

	// Section B: Notification Settings
	let usageAlertThreshold = 75;
	let emailNotifications = true;
	let dailyDigest = false;

	// Section C: Budget Controls
	let monthlySpendingCap = 500;
	let autoPauseOnQuota = true;
	let warningThreshold = 80;

	// Section D: Agent Defaults
	let defaultRole = 'buyer';
	let defaultCapabilities = 'negotiate, evaluate, settle';
	let autoConnectOnCreate = true;

	// Role colors
	const roleColors: Record<string, string> = {
		buyer: '#ff6f00',
		supplier: '#4ade80',
		logistics: '#60a5fa',
		inspector: '#c084fc',
		oracle: '#fbbf24'
	};

	function handleSave() {
		// Local state only - no backend yet
		showToastMessage('Configuration saved');
	}

	function showToastMessage(message: string) {
		toastMessage = message;
		showToast = true;
		setTimeout(() => {
			showToast = false;
		}, 3000);
	}

	function formatTemperature(value: number): string {
		return value.toFixed(1);
	}
</script>

<svelte:head>
	<title>Configuration — MESH Dashboard</title>
</svelte:head>

<div class="config-page">
	<!-- Page Header -->
	<header class="page-header">
		<h1>Configuration</h1>
		<p class="subtitle">Customize LLM preferences, notification settings, and agent defaults</p>
	</header>

	<!-- Info Banner -->
	<div class="info-banner">
		<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<circle cx="12" cy="12" r="10"/>
			<line x1="12" y1="16" x2="12" y2="12"/>
			<line x1="12" y1="8" x2="12.01" y2="8"/>
		</svg>
		<span>Configuration is stored locally. Server-side persistence coming soon.</span>
	</div>

	<div class="config-content">
		<!-- Section A: LLM Preferences -->
		<section class="config-section">
			<div class="section-header">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polygon points="12 2 2 7 12 12 22 7 12 2"/>
					<polyline points="2 17 12 22 22 17"/>
					<polyline points="2 12 12 17 22 12"/>
				</svg>
				<h3>LLM Preferences</h3>
			</div>
			<p class="section-note">Configuration is applied at the workspace level. Upgrade to Pro for custom model selection.</p>

			<div class="form-group">
				<label for="preferred-model">Preferred Model</label>
				<select id="preferred-model" bind:value={preferredModel}>
					<option value="claude-3-haiku">Claude 3 Haiku</option>
					<option value="claude-3-sonnet">Claude 3 Sonnet</option>
					<option value="gpt-4o">GPT-4o</option>
				</select>
			</div>

			<div class="form-group">
				<label for="temperature">
					Temperature
					<span class="value-display">{formatTemperature(temperature)}</span>
				</label>
				<input
					id="temperature"
					type="range"
					min="0"
					max="1"
					step="0.1"
					bind:value={temperature}
				/>
				<div class="range-labels">
					<span>Precise</span>
					<span>Creative</span>
				</div>
			</div>

			<div class="form-group">
				<label for="max-tokens">Max Tokens</label>
				<input
					id="max-tokens"
					type="number"
					min="256"
					max="8192"
					step="256"
					bind:value={maxTokens}
				/>
			</div>
		</section>

		<!-- Section B: Notification Settings -->
		<section class="config-section">
			<div class="section-header">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
					<path d="M13.73 21a2 2 0 0 1-3.46 0"/>
				</svg>
				<h3>Notification Settings</h3>
			</div>

			<div class="form-group">
				<label for="usage-threshold">
					Usage Alert Threshold
					<span class="value-display">{usageAlertThreshold}%</span>
				</label>
				<input
					id="usage-threshold"
					type="range"
					min="50"
					max="90"
					step="5"
					bind:value={usageAlertThreshold}
				/>
				<div class="range-labels">
					<span>50%</span>
					<span>90%</span>
				</div>
			</div>

			<div class="form-group toggle-group">
				<div class="toggle-label">
					<span>Email Notifications</span>
					<p class="toggle-description">Receive alerts via email for important events</p>
				</div>
				<label class="toggle-switch">
					<input type="checkbox" bind:checked={emailNotifications} />
					<span class="toggle-slider"></span>
				</label>
			</div>

			<div class="form-group toggle-group">
				<div class="toggle-label">
					<span>Daily Digest</span>
					<p class="toggle-description">Receive a daily summary of workspace activity</p>
				</div>
				<label class="toggle-switch">
					<input type="checkbox" bind:checked={dailyDigest} />
					<span class="toggle-slider"></span>
				</label>
			</div>
		</section>

		<!-- Section C: Budget Controls -->
		<section class="config-section">
			<div class="section-header">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="12" y1="1" x2="12" y2="23"/>
					<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
				</svg>
				<h3>Budget Controls</h3>
			</div>

			<div class="form-group">
				<label for="spending-cap">Monthly Spending Cap (USD)</label>
				<div class="input-prefix">
					<span class="prefix">$</span>
					<input
						id="spending-cap"
						type="number"
						min="0"
						step="50"
						bind:value={monthlySpendingCap}
					/>
				</div>
			</div>

			<div class="form-group toggle-group">
				<div class="toggle-label">
					<span>Auto-pause on Quota Exceeded</span>
					<p class="toggle-description">Automatically pause agents when spending cap is reached</p>
				</div>
				<label class="toggle-switch">
					<input type="checkbox" bind:checked={autoPauseOnQuota} />
					<span class="toggle-slider"></span>
				</label>
			</div>

			<div class="form-group">
				<label for="warning-threshold">
					Warning Threshold
					<span class="value-display">{warningThreshold}%</span>
				</label>
				<input
					id="warning-threshold"
					type="range"
					min="50"
					max="95"
					step="5"
					bind:value={warningThreshold}
				/>
				<div class="range-labels">
					<span>50%</span>
					<span>95%</span>
				</div>
			</div>
		</section>

		<!-- Section D: Agent Defaults -->
		<section class="config-section">
			<div class="section-header">
				<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
					<circle cx="9" cy="7" r="4"/>
					<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
					<path d="M16 3.13a4 4 0 0 1 0 7.75"/>
				</svg>
				<h3>Agent Defaults</h3>
			</div>

			<div class="form-group">
				<label for="default-role">Default Role</label>
				<select id="default-role" bind:value={defaultRole}>
					<option value="buyer" style="color: {roleColors.buyer}">Buyer</option>
					<option value="supplier" style="color: {roleColors.supplier}">Supplier</option>
					<option value="logistics" style="color: {roleColors.logistics}">Logistics</option>
					<option value="inspector" style="color: {roleColors.inspector}">Inspector</option>
					<option value="oracle" style="color: {roleColors.oracle}">Oracle</option>
				</select>
				<div class="role-preview" style="--role-color: {roleColors[defaultRole]}">
					<span class="role-badge">{defaultRole}</span>
				</div>
			</div>

			<div class="form-group">
				<label for="default-capabilities">Default Capabilities</label>
				<textarea
					id="default-capabilities"
					bind:value={defaultCapabilities}
					rows="3"
					placeholder="Enter capabilities separated by commas"
				></textarea>
				<p class="field-hint">Comma-separated list of default capabilities for new agents</p>
			</div>

			<div class="form-group toggle-group">
				<div class="toggle-label">
					<span>Auto-connect on Creation</span>
					<p class="toggle-description">Automatically connect agents to the mesh upon creation</p>
				</div>
				<label class="toggle-switch">
					<input type="checkbox" bind:checked={autoConnectOnCreate} />
					<span class="toggle-slider"></span>
				</label>
			</div>
		</section>

		<!-- Save Button -->
		<div class="save-section">
			<button class="save-btn" on:click={handleSave}>
				<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
					<polyline points="17 21 17 13 7 13 7 21"/>
					<polyline points="7 3 7 8 15 8"/>
				</svg>
				Save Configuration
			</button>
		</div>
	</div>
</div>

<!-- Toast Notification -->
{#if showToast}
	<div class="toast" class:show={showToast}>
		<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
			<polyline points="20 6 9 17 4 12"/>
		</svg>
		<span>{toastMessage}</span>
	</div>
{/if}

<style>
	.config-page {
		padding: 28px;
		max-width: 800px;
		margin: 0 auto;
	}

	/* Page Header */
	.page-header {
		margin-bottom: 20px;
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
		margin: 0;
		letter-spacing: 0.5px;
	}

	.subtitle {
		font-size: 0.875rem;
		color: var(--text-dim);
		margin: 0;
	}

	/* Info Banner */
	.info-banner {
		display: flex;
		align-items: center;
		gap: 12px;
		background: rgba(96, 165, 250, 0.1);
		border: 1px solid rgba(96, 165, 250, 0.2);
		border-radius: 4px;
		padding: 12px 16px;
		margin-bottom: 24px;
		color: #60a5fa;
		font-size: 0.875rem;
	}

	.info-banner svg {
		flex-shrink: 0;
	}

	/* Config Sections */
	.config-content {
		display: flex;
		flex-direction: column;
		gap: 24px;
	}

	.config-section {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 6px;
		padding: 24px;
	}

	.section-header {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 16px;
	}

	.section-header svg {
		color: var(--accent);
	}

	.section-note {
		font-size: 0.8rem;
		color: var(--text-dim);
		margin: -8px 0 20px 0;
		font-style: italic;
	}

	/* Form Groups */
	.form-group {
		margin-bottom: 20px;
	}

	.form-group:last-child {
		margin-bottom: 0;
	}

	.form-group label {
		display: block;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 500;
		color: var(--text-secondary);
		letter-spacing: 0.5px;
		text-transform: uppercase;
		margin-bottom: 8px;
	}

	.form-group input[type="text"],
	.form-group input[type="number"],
	.form-group select,
	.form-group textarea {
		width: 100%;
		max-width: 300px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 10px 14px;
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

	.form-group textarea {
		max-width: 100%;
		resize: vertical;
		min-height: 80px;
	}

	.form-group select {
		cursor: pointer;
	}

	.value-display {
		float: right;
		font-family: var(--font-mono);
		color: var(--accent);
		font-size: 0.85rem;
	}

	/* Range Input */
	.form-group input[type="range"] {
		width: 100%;
		max-width: 300px;
		height: 6px;
		background: var(--bg);
		border-radius: 3px;
		outline: none;
		padding: 0;
		margin: 8px 0;
		-webkit-appearance: none;
	}

	.form-group input[type="range"]::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 18px;
		height: 18px;
		background: var(--accent);
		border-radius: 50%;
		cursor: pointer;
		transition: transform 0.15s;
	}

	.form-group input[type="range"]::-webkit-slider-thumb:hover {
		transform: scale(1.1);
	}

	.form-group input[type="range"]::-moz-range-thumb {
		width: 18px;
		height: 18px;
		background: var(--accent);
		border-radius: 50%;
		cursor: pointer;
		border: none;
	}

	.range-labels {
		display: flex;
		justify-content: space-between;
		max-width: 300px;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-dim);
	}

	/* Input with prefix */
	.input-prefix {
		display: flex;
		align-items: center;
		max-width: 300px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 0 14px;
	}

	.input-prefix:focus-within {
		border-color: var(--accent);
	}

	.input-prefix .prefix {
		font-family: var(--font-mono);
		color: var(--text-dim);
		margin-right: 8px;
	}

	.input-prefix input {
		background: transparent;
		border: none;
		padding: 10px 0;
		flex: 1;
	}

	.input-prefix input:focus {
		outline: none;
		border: none;
	}

	/* Toggle Switch */
	.toggle-group {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
	}

	.toggle-label span {
		font-family: var(--font-heading);
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text);
	}

	.toggle-description {
		font-size: 0.8rem;
		color: var(--text-dim);
		margin: 4px 0 0 0;
	}

	.toggle-switch {
		position: relative;
		display: inline-block;
		width: 44px;
		height: 24px;
		flex-shrink: 0;
		cursor: pointer;
	}

	.toggle-switch input {
		opacity: 0;
		width: 0;
		height: 0;
	}

	.toggle-slider {
		position: absolute;
		cursor: pointer;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 24px;
		transition: 0.3s;
	}

	.toggle-slider:before {
		position: absolute;
		content: "";
		height: 18px;
		width: 18px;
		left: 2px;
		bottom: 2px;
		background-color: var(--text-dim);
		border-radius: 50%;
		transition: 0.3s;
	}

	.toggle-switch input:checked + .toggle-slider {
		background-color: rgba(255, 111, 0, 0.2);
		border-color: var(--accent);
	}

	.toggle-switch input:checked + .toggle-slider:before {
		transform: translateX(20px);
		background-color: var(--accent);
	}

	/* Role Preview */
	.role-preview {
		margin-top: 8px;
	}

	.role-badge {
		display: inline-block;
		font-family: var(--font-mono);
		font-size: 0.75rem;
		font-weight: 500;
		padding: 4px 12px;
		border-radius: 2px;
		background: rgba(255, 111, 0, 0.15);
		color: var(--role-color, var(--accent));
		border: 1px solid var(--role-color, var(--accent));
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	/* Field Hint */
	.field-hint {
		font-size: 0.75rem;
		color: var(--text-dim);
		margin: 6px 0 0 0;
	}

	/* Save Section */
	.save-section {
		margin-top: 8px;
	}

	.save-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 3px;
		padding: 12px 24px;
		font-family: var(--font-heading);
		font-size: 0.875rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		cursor: pointer;
		transition: background 0.2s;
	}

	.save-btn:hover {
		background: var(--accent-hover);
	}

	/* Toast Notification */
	.toast {
		position: fixed;
		bottom: 24px;
		right: 24px;
		display: flex;
		align-items: center;
		gap: 10px;
		background: var(--green);
		color: #fff;
		padding: 14px 20px;
		border-radius: 4px;
		font-family: var(--font-heading);
		font-size: 0.875rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
		z-index: 1000;
		animation: slideIn 0.3s ease;
	}

	@keyframes slideIn {
		from {
			transform: translateX(100%);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}

	/* Responsive */
	@media (max-width: 768px) {
		.config-page {
			padding: 16px;
		}

		.form-group input,
		.form-group select,
		.input-prefix {
			max-width: 100%;
		}

		.range-labels {
			max-width: 100%;
		}
	}
</style>
