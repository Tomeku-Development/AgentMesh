<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { createAPIKey } from '$lib/api/apikeys';
	import { getAgents } from '$lib/api/agents';
	import { getCapabilities } from '$lib/api/capabilities';
	import { activeWorkspaceId } from '$lib/stores/workspace';
	import type { Agent, Capability } from '$lib/types/api';

	// Wizard state
	let currentStep = 1;
	const totalSteps = 5;
	const stepLabels = ['Role', 'Configure', 'API Key', 'Connect', 'Verify'];

	// Step 1: Role selection
	let selectedRole: string | null = null;

	const roles = [
		{
			id: 'buyer',
			name: 'Buyer',
			color: '#ff6f00',
			icon: '🛒',
			description: 'Discovers suppliers, evaluates bids, manages procurement and escrow'
		},
		{
			id: 'supplier',
			name: 'Supplier',
			color: '#4ade80',
			icon: '📦',
			description: 'Receives orders, submits bids, fulfills deliveries'
		},
		{
			id: 'logistics',
			name: 'Logistics',
			color: '#60a5fa',
			icon: '🚚',
			description: 'Handles shipping, calculates costs, tracks delivery'
		},
		{
			id: 'inspector',
			name: 'Inspector',
			color: '#c084fc',
			icon: '🔍',
			description: 'Verifies quality, runs inspections, reports findings. Ideal for IoT devices'
		},
		{
			id: 'oracle',
			name: 'Oracle',
			color: '#fbbf24',
			icon: '📊',
			description: 'Provides market data, pricing signals, and demand forecasts'
		}
	];

	const roleCapabilities: Record<string, string> = {
		buyer: 'negotiate, evaluate_bids, manage_escrow',
		supplier: 'bid, fulfill_orders, counter_offer',
		logistics: 'ship, calculate_costs, track',
		inspector: 'inspect, verify_quality, report',
		oracle: 'price_feed, demand_analysis, market_data'
	};

	// Step 2: Configuration
	let agentId = '';
	let capabilities = '';
	let balance = 10000;

	// Step 2: Capability picker
	let availableCapabilities: Capability[] = [];
	let selectedCapabilityNames: string[] = [];
	let customCapabilityInput = '';
	let capabilitiesLoading = false;
	let capabilitiesError = '';
	let capSearchQuery = '';
	let capSelectedCategory = 'all';

	const capCategories = ['domain', 'process', 'iot', 'logistics', 'quality', 'market'] as const;
	const capCategoryColors: Record<string, string> = {
		domain: '#ff6f00',
		process: '#4ade80',
		iot: '#60a5fa',
		logistics: '#818cf8',
		quality: '#c084fc',
		market: '#fbbf24'
	};

	$: filteredCapabilities = availableCapabilities.filter(cap => {
		const matchesSearch = capSearchQuery === '' ||
			cap.name.toLowerCase().includes(capSearchQuery.toLowerCase()) ||
			cap.display_name.toLowerCase().includes(capSearchQuery.toLowerCase());
		const matchesCategory = capSelectedCategory === 'all' || cap.category === capSelectedCategory;
		return matchesSearch && matchesCategory;
	});

	$: groupedCapabilities = capCategories.reduce((acc, cat) => {
		acc[cat] = filteredCapabilities.filter(c => c.category === cat);
		return acc;
	}, {} as Record<string, Capability[]>);

	// Step 3: API Key
	let apiKeyOption: 'generate' | 'existing' = 'generate';
	let generatedKey: string | null = null;
	let existingKey = '';
	let isGeneratingKey = false;
	let keyError: string | null = null;

	// Step 4: Code snippets
	let activeTab = 'typescript';
	const tabs = [
		{ id: 'typescript', label: 'TypeScript SDK' },
		{ id: 'websocket', label: 'WebSocket Direct' },
		{ id: 'cli', label: 'CLI' },
		{ id: 'python', label: 'Python / IoT' }
	];

	// Step 5: Verification
	let verificationStatus: 'waiting' | 'connected' | 'timeout' = 'waiting';
	let foundAgent: Agent | null = null;
	let isChecking = false;
	let pollInterval: ReturnType<typeof setInterval> | null = null;
	let pollTimeout: ReturnType<typeof setTimeout> | null = null;

	$: workspaceId = $activeWorkspaceId || 'default';
	$: currentRole = roles.find(r => r.id === selectedRole);
	$: effectiveApiKey = apiKeyOption === 'generate' ? generatedKey : existingKey;
	$: capabilitiesArray = capabilities.split(',').map(c => c.trim()).filter(Boolean);

	function selectRole(roleId: string) {
		selectedRole = roleId;
		// Pre-select capabilities based on role's applicable_roles
		const roleCapSet = new Set<string>();
		availableCapabilities.forEach(cap => {
			const capRoles = cap.applicable_roles ? cap.applicable_roles.split(',').map(r => r.trim()) : [];
			if (capRoles.includes(roleId)) {
				roleCapSet.add(cap.name);
			}
		});
		selectedCapabilityNames = Array.from(roleCapSet);
		customCapabilityInput = '';
	}

	function nextStep() {
		if (currentStep < totalSteps) {
			currentStep++;
			if (currentStep === 2) {
				loadCapabilitiesData();
			}
			if (currentStep === 5) {
				startVerification();
			}
		}
	}

	function prevStep() {
		if (currentStep > 1) {
			currentStep--;
		}
	}

	function resetWizard() {
		currentStep = 1;
		selectedRole = null;
		agentId = '';
		capabilities = '';
		balance = 10000;
		apiKeyOption = 'generate';
		generatedKey = null;
		existingKey = '';
		keyError = null;
		activeTab = 'typescript';
		verificationStatus = 'waiting';
		foundAgent = null;
		selectedCapabilityNames = [];
		customCapabilityInput = '';
		capSearchQuery = '';
		capSelectedCategory = 'all';
		stopPolling();
	}

	async function loadCapabilitiesData() {
		if (availableCapabilities.length > 0) return; // Already loaded
		capabilitiesLoading = true;
		capabilitiesError = '';
		try {
			availableCapabilities = await getCapabilities();
			// Pre-select based on role if role already selected
			if (selectedRole) {
				const roleCapSet = new Set<string>();
				availableCapabilities.forEach(cap => {
					const capRoles = cap.applicable_roles ? cap.applicable_roles.split(',').map(r => r.trim()) : [];
					if (capRoles.includes(selectedRole as string)) {
						roleCapSet.add(cap.name);
					}
				});
				selectedCapabilityNames = Array.from(roleCapSet);
			}
		} catch (err) {
			capabilitiesError = err instanceof Error ? err.message : 'Failed to load capabilities';
			// Fallback to legacy defaults
			if (selectedRole && roleCapabilities[selectedRole]) {
				selectedCapabilityNames = roleCapabilities[selectedRole].split(',').map(c => c.trim());
			}
		} finally {
			capabilitiesLoading = false;
		}
	}

	function toggleCapability(capName: string) {
		if (selectedCapabilityNames.includes(capName)) {
			selectedCapabilityNames = selectedCapabilityNames.filter(c => c !== capName);
		} else {
			selectedCapabilityNames = [...selectedCapabilityNames, capName];
		}
	}

	function addCustomCapability() {
		const customCap = customCapabilityInput.trim();
		if (customCap && !selectedCapabilityNames.includes(customCap)) {
			selectedCapabilityNames = [...selectedCapabilityNames, customCap];
			customCapabilityInput = '';
		}
	}

	function parseApplicableRoles(roles: string): string[] {
		if (!roles) return [];
		return roles.split(',').map(r => r.trim()).filter(Boolean);
	}

	// Update capabilities string when selected capabilities change
	$: capabilities = [...selectedCapabilityNames].join(', ');

	async function generateKey() {
		if (!selectedRole) return;
		isGeneratingKey = true;
		keyError = null;
		try {
			const response = await createAPIKey(workspaceId, {
				name: `${selectedRole}-agent-key`,
				scopes: ['read', 'write']
			});
			generatedKey = response.raw_key;
		} catch (err) {
			keyError = err instanceof Error ? err.message : 'Failed to generate API key';
		} finally {
			isGeneratingKey = false;
		}
	}

	async function copyToClipboard(text: string) {
		try {
			await navigator.clipboard.writeText(text);
		} catch {
			// Fallback
			const textarea = document.createElement('textarea');
			textarea.value = text;
			document.body.appendChild(textarea);
			textarea.select();
			document.execCommand('copy');
			document.body.removeChild(textarea);
		}
	}

	function getTypeScriptCode(): string {
		const caps = capabilitiesArray.map(c => `'${c}'`).join(', ');
		const agentIdLine = agentId ? `\n  agentId: '${agentId}',` : '';
		return `import { Agent } from '@mesh/sdk';

const agent = new Agent({
  apiKey: '${effectiveApiKey || 'YOUR_API_KEY'}',
  role: '${selectedRole || 'buyer'}',${agentIdLine}
  capabilities: [${caps}],
  balance: ${balance},
});

agent.on('connected', () => {
  console.log('Agent connected to MESH network');
});

agent.on('message', (topic, payload) => {
  console.log(\`[\${topic}]\`, payload);
});

await agent.connect();`;
	}

	function getWebSocketCode(): string {
		const caps = capabilitiesArray.map(c => `'${c}'`).join(', ');
		return `const ws = new WebSocket('ws://localhost:8080/ws/v1/agent?api_key=${effectiveApiKey || 'YOUR_API_KEY'}');

ws.onopen = () => {
  // First message must be register
  ws.send(JSON.stringify({
    type: 'register',
    role: '${selectedRole || 'buyer'}',
    capabilities: [${caps}],
    balance: ${balance}
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log('Received:', msg);
};`;
	}

	function getCliCode(): string {
		return `npx mesh-cli connect \\
  --api-key ${effectiveApiKey || 'YOUR_API_KEY'} \\
  --role ${selectedRole || 'buyer'} \\
  --capabilities ${capabilities || 'negotiate,evaluate_bids'}`;
	}

	function getPythonCode(): string {
		const caps = capabilitiesArray.map(c => `"${c}"`).join(', ');
		return `import asyncio
import json
import websockets

async def connect_iot_agent():
    uri = "ws://localhost:8080/ws/v1/agent?api_key=${effectiveApiKey || 'YOUR_API_KEY'}"
    
    async with websockets.connect(uri) as ws:
        # Register as ${selectedRole || 'inspector'} (IoT sensor)
        await ws.send(json.dumps({
            "type": "register",
            "role": "${selectedRole || 'inspector'}",
            "capabilities": [${caps}],
            "balance": ${balance}
        }))
        
        # Listen for inspection requests
        async for message in ws:
            data = json.loads(message)
            print(f"Received: {data}")
            
            # Handle quality inspection
            if data.get("type") == "message":
                topic = data.get("topic", "")
                if "quality/request" in topic:
                    # Send inspection result
                    await ws.send(json.dumps({
                        "type": "publish",
                        "topic": f"mesh/quality/report/{data['payload'].get('order_id', '')}",
                        "payload": {
                            "passed": True,
                            "score": 0.95,
                            "notes": "IoT sensor readings nominal"
                        }
                    }))

asyncio.run(connect_iot_agent())`;
	}

	function getCodeForTab(tabId: string): string {
		switch (tabId) {
			case 'typescript': return getTypeScriptCode();
			case 'websocket': return getWebSocketCode();
			case 'cli': return getCliCode();
			case 'python': return getPythonCode();
			default: return '';
		}
	}

	async function checkConnection() {
		if (!selectedRole) return;
		isChecking = true;
		try {
			const response = await getAgents(workspaceId);
			// Look for an agent with matching role that was created recently
			const recentAgents = response.agents.filter(a => 
				a.agent_role.toLowerCase() === selectedRole?.toLowerCase()
			);
			if (recentAgents.length > 0) {
				// Sort by created_at descending and take the most recent
				foundAgent = recentAgents.sort((a, b) => 
					new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
				)[0];
				verificationStatus = 'connected';
				stopPolling();
			}
		} catch (err) {
			console.error('Failed to check connection:', err);
		} finally {
			isChecking = false;
		}
	}

	function startVerification() {
		verificationStatus = 'waiting';
		foundAgent = null;
		
		// Initial check
		checkConnection();
		
		// Poll every 3 seconds
		pollInterval = setInterval(() => {
			checkConnection();
		}, 3000);
		
		// Timeout after 30 seconds
		pollTimeout = setTimeout(() => {
			if (verificationStatus === 'waiting') {
				verificationStatus = 'timeout';
				stopPolling();
			}
		}, 30000);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
		if (pollTimeout) {
			clearTimeout(pollTimeout);
			pollTimeout = null;
		}
	}

	function retryVerification() {
		verificationStatus = 'waiting';
		startVerification();
	}

	onDestroy(() => {
		stopPolling();
	});
</script>

<svelte:head>
	<title>Connect Agent — MESH Dashboard</title>
</svelte:head>

<div class="connect-page">
	<!-- Page Header -->
	<header class="page-header">
		<h1>Connect Agent</h1>
		<p class="header-subtitle">Onboard a new agent to your MESH workspace</p>
	</header>

	<!-- Progress Bar -->
	<div class="progress-container">
		<div class="progress-steps">
			{#each stepLabels as label, i}
				{@const stepNum = i + 1}
				{@const isCompleted = currentStep > stepNum}
				{@const isCurrent = currentStep === stepNum}
				{@const isFuture = currentStep < stepNum}
				<div class="step" class:completed={isCompleted} class:current={isCurrent} class:future={isFuture}>
					<div class="step-circle">
						{#if isCompleted}
							<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
								<path d="M5 12l5 5L20 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
						{:else}
							{stepNum}
						{/if}
					</div>
					<span class="step-label">{label}</span>
				</div>
				{#if i < stepLabels.length - 1}
					<div class="step-line" class:completed={isCompleted}></div>
				{/if}
			{/each}
		</div>
	</div>

	<!-- Content Area -->
	<div class="wizard-content">
		<!-- Step 1: Choose Role -->
		{#if currentStep === 1}
			<div class="step-content">
				<h2 class="step-title">Choose Agent Role</h2>
				<p class="step-subtitle">Select the type of agent you want to connect</p>
				
				<div class="role-grid">
					{#each roles as role}
						<button
							class="role-card"
							class:selected={selectedRole === role.id}
							style="--role-color: {role.color}"
							on:click={() => selectRole(role.id)}
							type="button"
						>
							<span class="role-icon">{role.icon}</span>
							<h3 class="role-name">{role.name}</h3>
							<p class="role-description">{role.description}</p>
						</button>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Step 2: Configure -->
		{#if currentStep === 2}
			<div class="step-content">
				<h2 class="step-title">Configure Your Agent</h2>
				
				<div class="form-group">
					<label for="agent-id">Agent ID <span class="optional">(optional)</span></label>
					<input
						id="agent-id"
						type="text"
						bind:value={agentId}
						placeholder="auto-generated if empty"
						class="mono-input"
					/>
				</div>

				<div class="form-group capabilities-section">
					<label>Capabilities</label>
					<p class="field-hint">Select capabilities for your {currentRole?.name || 'agent'} agent.</p>

					{#if capabilitiesError}
						<div class="cap-error">{capabilitiesError}</div>
					{/if}

					{#if capabilitiesLoading}
						<div class="cap-loading">
							<div class="spinner-small"></div>
							Loading capabilities...
						</div>
					{:else}
						<!-- Search and Filter -->
						<div class="cap-filters">
							<input
								type="text"
								class="cap-search"
								placeholder="Search capabilities..."
								bind:value={capSearchQuery}
						/>
							<div class="cap-category-tabs">
								<button
									class="cap-cat-btn"
									class:active={capSelectedCategory === 'all'}
									on:click={() => capSelectedCategory = 'all'}
									type="button"
								>
									All
								</button>
								{#each capCategories as cat}
									<button
										class="cap-cat-btn"
										class:active={capSelectedCategory === cat}
										style="--cat-color: {capCategoryColors[cat]}"
										on:click={() => capSelectedCategory = cat}
										type="button"
									>
										{cat}
									</button>
								{/each}
							</div>
						</div>

						<!-- Selected capabilities -->
						{#if selectedCapabilityNames.length > 0}
							<div class="selected-caps">
								{#each selectedCapabilityNames as capName}
									<span class="selected-cap-tag">
										{capName}
										<button
											class="remove-cap"
											on:click={() => toggleCapability(capName)}
											type="button"
										>
												×
											</button>
										</span>
								{/each}
							</div>
						{/if}

						<!-- Capability list by category -->
						<div class="cap-list">
							{#each capCategories as cat}
								{#if groupedCapabilities[cat] && groupedCapabilities[cat].length > 0}
									<div class="cap-group">
										<h4 class="cap-group-title" style="--cat-color: {capCategoryColors[cat]}">
											{cat}
										</h4>
										<div class="cap-items">
											{#each groupedCapabilities[cat] as cap}
												<label class="cap-item" title={cap.description}>
													<input
														type="checkbox"
														checked={selectedCapabilityNames.includes(cap.name)}
														on:change={() => toggleCapability(cap.name)}
													/>
													<div class="cap-item-content">
														<span class="cap-item-name">{cap.display_name}</span>
														<span class="cap-item-desc">{cap.description || 'No description'}</span>
														<div class="cap-item-roles">
															{#each parseApplicableRoles(cap.applicable_roles) as role}
																<span class="cap-role-tag">{role}</span>
															{/each}
														</div>
													</div>
												</label>
											{/each}
										</div>
									</div>
								{/if}
							{/each}

							{#if filteredCapabilities.length === 0}
								<div class="cap-empty">
									{#if capSearchQuery}
										No capabilities match your search.
									{:else}
										No capabilities available.
									{/if}
								</div>
							{/if}
						</div>

						<!-- Custom capability input -->
						<div class="custom-cap-section">
							<input
								type="text"
								class="custom-cap-input"
								placeholder="Add custom capability..."
								bind:value={customCapabilityInput}
								on:keydown={(e) => e.key === 'Enter' && addCustomCapability()}
						/>
							<button
								class="add-custom-btn"
								on:click={addCustomCapability}
								disabled={!customCapabilityInput.trim()}
								type="button"
							>
								Add
							</button>
						</div>
					{/if}
				</div>

				<div class="form-group">
					<label for="balance">Initial Balance</label>
					<div class="balance-input">
						<input
							id="balance"
							type="number"
							bind:value={balance}
							min="0"
						/>
						<span class="balance-unit">MESH_CREDIT</span>
					</div>
				</div>
			</div>
		{/if}

		<!-- Step 3: API Key -->
		{#if currentStep === 3}
			<div class="step-content">
				<h2 class="step-title">API Key</h2>
				<p class="step-subtitle">You need an API key to authenticate your agent</p>
				
				<div class="api-key-options">
					<label class="option-label">
						<input
							type="radio"
							bind:group={apiKeyOption}
							value="generate"
						/>
						<span>Generate new key</span>
					</label>
					
					{#if apiKeyOption === 'generate'}
						<div class="generate-section">
							{#if generatedKey}
								<div class="key-display">
									<code class="key-value">{generatedKey}</code>
									<button
										class="copy-btn"
										on:click={() => generatedKey && copyToClipboard(generatedKey)}
										type="button"
									>
										<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
											<rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
											<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2"/>
										</svg>
										Copy
									</button>
								</div>
								<p class="key-warning">⚠️ Copy this key now. You won't be able to see it again!</p>
							{:else}
								<button
									class="generate-btn"
									on:click={generateKey}
									disabled={isGeneratingKey}
									type="button"
								>
									{#if isGeneratingKey}
										<span class="spinner-small"></span>
										Generating...
									{:else}
										Generate API Key
									{/if}
								</button>
							{/if}
							{#if keyError}
								<p class="error-text">{keyError}</p>
							{/if}
						</div>
					{/if}
					
					<label class="option-label">
						<input
							type="radio"
							bind:group={apiKeyOption}
							value="existing"
						/>
						<span>Use existing key</span>
					</label>
					
					{#if apiKeyOption === 'existing'}
						<div class="existing-section">
							<input
								type="text"
								bind:value={existingKey}
								placeholder="Paste your API key here"
								class="mono-input"
							/>
						</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Step 4: Connect -->
		{#if currentStep === 4}
			<div class="step-content">
				<h2 class="step-title">Connect Your Agent</h2>
				<p class="step-subtitle">Choose your integration method</p>
				
				<div class="code-tabs">
					<div class="tab-headers">
						{#each tabs as tab}
							<button
								class="tab-btn"
								class:active={activeTab === tab.id}
								on:click={() => activeTab = tab.id}
								type="button"
							>
								{tab.label}
							</button>
						{/each}
					</div>
					
					<div class="tab-content">
						{#each tabs as tab}
							{#if activeTab === tab.id}
								<div class="code-panel">
									<pre><code>{getCodeForTab(tab.id)}</code></pre>
									<button
										class="copy-code-btn"
										on:click={() => copyToClipboard(getCodeForTab(tab.id))}
										type="button"
									>
										<svg width="16" height="16" viewBox="0 0 24 24" fill="none">
											<rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" stroke-width="2"/>
											<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" stroke-width="2"/>
										</svg>
										Copy
									</button>
								</div>
							{/if}
						{/each}
					</div>
				</div>
			</div>
		{/if}

		<!-- Step 5: Verify -->
		{#if currentStep === 5}
			<div class="step-content">
				<h2 class="step-title">Verify Connection</h2>
				<p class="step-subtitle">Check if your agent is connected to the mesh network</p>
				
				<div class="verification-area">
					<div class="status-indicator" class:pulsing={verificationStatus === 'waiting'}>
						{#if verificationStatus === 'waiting'}
							<div class="status-circle waiting">
								<div class="pulse-ring"></div>
							</div>
							<span class="status-text">Waiting...</span>
						{:else if verificationStatus === 'connected'}
							<div class="status-circle connected">
								<svg width="32" height="32" viewBox="0 0 24 24" fill="none">
									<path d="M5 12l5 5L20 7" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
								</svg>
							</div>
							<span class="status-text connected">Connected!</span>
						{:else}
							<div class="status-circle timeout">
								<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
									<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
									<path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
								</svg>
							</div>
							<span class="status-text timeout">Not detected yet</span>
						{/if}
					</div>
					
					{#if verificationStatus === 'waiting'}
						<p class="verify-hint">Make sure your agent code is running...</p>
						<button
							class="check-btn"
							on:click={checkConnection}
							disabled={isChecking}
							type="button"
						>
							{#if isChecking}
								<span class="spinner-small"></span>
								Checking...
							{:else}
								Check Connection
							{/if}
						</button>
					{/if}
					
					{#if verificationStatus === 'timeout'}
						<p class="timeout-message">
							Agent not detected. Make sure your code is running and try again.
						</p>
						<button
							class="retry-btn"
							on:click={retryVerification}
							type="button"
						>
							Retry
						</button>
					{/if}
					
					{#if verificationStatus === 'connected' && foundAgent}
						<div class="agent-card">
							<div class="agent-card-header">
								<span
									class="agent-role-badge"
									style="background: {currentRole?.color || '#9a9a9e'}26; color: {currentRole?.color || '#9a9a9e'}"
								>
									{foundAgent.agent_role}
								</span>
								<span class="agent-status-badge">Active</span>
							</div>
							<div class="agent-card-body">
								<div class="agent-field">
									<span class="field-label">Agent ID</span>
									<code class="field-value">{foundAgent.agent_mesh_id}</code>
								</div>
								<div class="agent-field">
									<span class="field-label">Balance</span>
									<span class="field-value">{foundAgent.initial_balance.toLocaleString()} MESH</span>
								</div>
							</div>
						</div>
					{/if}
				</div>
				
				{#if verificationStatus !== 'waiting'}
					<div class="verify-actions">
						<a href="/dashboard/agents/" class="action-btn primary">Go to Agents</a>
						<button class="action-btn secondary" on:click={resetWizard} type="button">
							Connect Another
						</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Navigation Buttons -->
	<div class="wizard-nav">
		{#if currentStep > 1}
			<button class="nav-btn secondary" on:click={prevStep} type="button">
				Back
			</button>
		{:else}
			<div></div>
		{/if}
		
		{#if currentStep < totalSteps}
			<button
				class="nav-btn primary"
				on:click={nextStep}
				disabled={
					(currentStep === 1 && !selectedRole) ||
					(currentStep === 3 && !effectiveApiKey)
				}
				type="button"
			>
				Next
			</button>
		{:else}
			<button class="nav-btn primary" on:click={resetWizard} type="button">
				Finish
			</button>
		{/if}
	</div>
</div>

<style>
	.connect-page {
		padding: 28px;
		max-width: 1000px;
		margin: 0 auto;
		min-height: calc(100vh - 200px);
		display: flex;
		flex-direction: column;
	}

	/* ── Page Header ─────────────────────────── */
	.page-header {
		margin-bottom: 32px;
	}

	.page-header h1 {
		font-family: var(--font-heading);
		font-size: 1.75rem;
		font-weight: 600;
		color: var(--text);
		letter-spacing: 0.5px;
		margin: 0 0 8px 0;
	}

	.header-subtitle {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
		margin: 0;
	}

	/* ── Progress Bar ────────────────────────── */
	.progress-container {
		margin-bottom: 40px;
	}

	.progress-steps {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0;
	}

	.step {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
	}

	.step-circle {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-heading);
		font-size: 0.875rem;
		font-weight: 600;
		transition: all 0.3s ease;
	}

	.step.completed .step-circle {
		background: #4ade80;
		color: #0f0f11;
	}

	.step.current .step-circle {
		background: var(--accent);
		color: #fff;
	}

	.step.future .step-circle {
		background: var(--bg-surface);
		color: var(--text-dim);
		border: 1px solid var(--border);
	}

	.step-label {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		transition: color 0.3s ease;
	}

	.step.completed .step-label {
		color: #4ade80;
	}

	.step.current .step-label {
		color: var(--accent);
	}

	.step.future .step-label {
		color: var(--text-dim);
	}

	.step-line {
		width: 60px;
		height: 2px;
		background: var(--border);
		margin: 0 12px;
		position: relative;
		top: -14px;
		transition: background 0.3s ease;
	}

	.step-line.completed {
		background: #4ade80;
	}

	/* ── Wizard Content ──────────────────────── */
	.wizard-content {
		flex: 1;
	}

	.step-content {
		animation: fadeIn 0.3s ease;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(10px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.step-title {
		font-family: var(--font-heading);
		font-size: 1.25rem;
		font-weight: 600;
		color: var(--text);
		margin: 0 0 8px 0;
	}

	.step-subtitle {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
		margin: 0 0 28px 0;
	}

	/* ── Role Grid ───────────────────────────── */
	.role-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 16px;
	}

	.role-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 20px;
		text-align: left;
		cursor: pointer;
		transition: all 0.2s ease;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.role-card:hover {
		border-color: color-mix(in srgb, var(--role-color) 50%, transparent);
	}

	.role-card.selected {
		border-color: var(--role-color);
		background: color-mix(in srgb, var(--role-color) 5%, var(--bg-surface));
	}

	.role-icon {
		font-size: 1.5rem;
		line-height: 1;
	}

	.role-name {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text);
		margin: 0;
	}

	.role-description {
		font-family: var(--font-body);
		font-size: 0.8125rem;
		color: var(--text-secondary);
		margin: 0;
		line-height: 1.5;
	}

	@media (max-width: 768px) {
		.role-grid {
			grid-template-columns: 1fr;
		}
	}

	/* ── Form Styles ─────────────────────────── */
	.form-group {
		margin-bottom: 20px;
	}

	.form-group label {
		display: block;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		color: var(--text-secondary);
		margin-bottom: 8px;
	}

	.form-group label .optional {
		color: var(--text-dim);
		font-weight: 400;
		text-transform: none;
	}

	.form-group input {
		width: 100%;
		padding: 10px 12px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		color: var(--text);
		font-family: var(--font-body);
		font-size: 0.875rem;
		transition: border-color 0.2s;
	}

	.form-group input:focus {
		outline: none;
		border-color: var(--accent);
	}

	.form-group input.mono-input {
		font-family: var(--font-mono);
	}

	.balance-input {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.balance-input input {
		flex: 1;
		max-width: 200px;
	}

	.balance-unit {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text-secondary);
	}

	.field-hint {
		font-family: var(--font-body);
		font-size: 0.75rem;
		color: var(--text-dim);
		margin: 6px 0 0 0;
	}

	/* ── API Key Section ─────────────────────── */
	.api-key-options {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.option-label {
		display: flex;
		align-items: center;
		gap: 10px;
		cursor: pointer;
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text);
	}

	.option-label input[type="radio"] {
		width: 16px;
		height: 16px;
		accent-color: var(--accent);
	}

	.generate-section,
	.existing-section {
		margin-left: 26px;
		padding: 16px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 6px;
	}

	.generate-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 20px;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 4px;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.generate-btn:hover:not(:disabled) {
		opacity: 0.9;
	}

	.generate-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.key-display {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
	}

	.key-value {
		flex: 1;
		min-width: 0;
		padding: 10px 12px;
		background: var(--bg);
		border: 1px solid var(--border);
		border-radius: 4px;
		font-family: var(--font-mono);
		font-size: 0.75rem;
		color: var(--text);
		word-break: break-all;
	}

	.copy-btn {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 14px;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		color: var(--text);
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.copy-btn:hover {
		background: var(--bg-elevated);
		border-color: var(--accent);
	}

	.key-warning {
		font-family: var(--font-body);
		font-size: 0.75rem;
		color: #fbbf24;
		margin: 12px 0 0 0;
	}

	.error-text {
		font-family: var(--font-body);
		font-size: 0.75rem;
		color: #ef4444;
		margin: 8px 0 0 0;
	}

	/* ── Code Tabs ───────────────────────────── */
	.code-tabs {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 8px;
		overflow: hidden;
	}

	.tab-headers {
		display: flex;
		background: var(--bg-surface);
		border-bottom: 1px solid var(--border);
	}

	.tab-btn {
		padding: 12px 20px;
		background: transparent;
		border: none;
		border-bottom: 2px solid transparent;
		color: var(--text-secondary);
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.tab-btn:hover {
		color: var(--text);
	}

	.tab-btn.active {
		color: var(--accent);
		border-bottom-color: var(--accent);
	}

	.tab-content {
		position: relative;
	}

	.code-panel {
		position: relative;
	}

	.code-panel pre {
		margin: 0;
		padding: 20px;
		overflow-x: auto;
	}

	.code-panel code {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--text);
		line-height: 1.6;
		white-space: pre;
	}

	.copy-code-btn {
		position: absolute;
		top: 12px;
		right: 12px;
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 14px;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: 4px;
		color: var(--text);
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.copy-code-btn:hover {
		background: var(--bg-elevated);
		border-color: var(--accent);
	}

	/* ── Verification Section ────────────────── */
	.verification-area {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 40px 20px;
		gap: 20px;
	}

	.status-indicator {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
	}

	.status-indicator.pulsing {
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	.status-circle {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.status-circle.waiting {
		background: var(--bg-surface);
		border: 2px solid var(--border);
	}

	.status-circle.waiting::after {
		content: '';
		width: 16px;
		height: 16px;
		background: var(--text-dim);
		border-radius: 50%;
	}

	.pulse-ring {
		position: absolute;
		inset: -4px;
		border: 2px solid var(--text-dim);
		border-radius: 50%;
		animation: pulseRing 2s ease-out infinite;
	}

	@keyframes pulseRing {
		0% { transform: scale(1); opacity: 1; }
		100% { transform: scale(1.3); opacity: 0; }
	}

	.status-circle.connected {
		background: #4ade8026;
		border: 2px solid #4ade80;
		color: #4ade80;
	}

	.status-circle.timeout {
		background: #fbbf2426;
		border: 2px solid #fbbf24;
		color: #fbbf24;
	}

	.status-text {
		font-family: var(--font-heading);
		font-size: 1rem;
		font-weight: 600;
		color: var(--text-dim);
	}

	.status-text.connected {
		color: #4ade80;
	}

	.status-text.timeout {
		color: #fbbf24;
	}

	.verify-hint {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
		margin: 0;
	}

	.check-btn,
	.retry-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 24px;
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 4px;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.check-btn:hover:not(:disabled),
	.retry-btn:hover {
		opacity: 0.9;
	}

	.check-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.timeout-message {
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text-secondary);
		text-align: center;
		max-width: 400px;
		margin: 0;
	}

	/* ── Agent Card ──────────────────────────── */
	.agent-card {
		width: 100%;
		max-width: 400px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 8px;
		overflow: hidden;
	}

	.agent-card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px;
		background: var(--bg-surface);
		border-bottom: 1px solid var(--border);
	}

	.agent-role-badge {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		padding: 4px 10px;
		border-radius: 4px;
	}

	.agent-status-badge {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		color: #4ade80;
		background: #4ade8026;
		padding: 4px 10px;
		border-radius: 4px;
	}

	.agent-card-body {
		padding: 16px;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.agent-field {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.field-label {
		font-family: var(--font-heading);
		font-size: 0.6875rem;
		font-weight: 500;
		letter-spacing: 0.5px;
		color: var(--text-secondary);
		text-transform: uppercase;
	}

	.field-value {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--text);
	}

	/* ── Verify Actions ──────────────────────── */
	.verify-actions {
		display: flex;
		justify-content: center;
		gap: 12px;
		margin-top: 20px;
	}

	.action-btn {
		display: inline-flex;
		align-items: center;
		padding: 10px 24px;
		border-radius: 4px;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		text-decoration: none;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.action-btn.primary {
		background: var(--accent);
		color: #fff;
		border: none;
	}

	.action-btn.secondary {
		background: transparent;
		color: var(--text);
		border: 1px solid var(--border);
	}

	.action-btn:hover {
		opacity: 0.9;
	}

	/* ── Navigation ──────────────────────────── */
	.wizard-nav {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 40px;
		padding-top: 24px;
		border-top: 1px solid var(--border);
	}

	.nav-btn {
		padding: 10px 28px;
		border-radius: 4px;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		cursor: pointer;
		transition: all 0.2s;
	}

	.nav-btn.primary {
		background: var(--accent);
		color: #fff;
		border: none;
	}

	.nav-btn.primary:hover:not(:disabled) {
		opacity: 0.9;
	}

	.nav-btn.primary:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.nav-btn.secondary {
		background: transparent;
		color: var(--text);
		border: 1px solid var(--border);
	}

	.nav-btn.secondary:hover {
		background: var(--bg-elevated);
	}

	/* ── Spinner ─────────────────────────────── */
	.spinner-small {
		width: 14px;
		height: 14px;
		border: 2px solid rgba(255,255,255,0.3);
		border-top-color: currentColor;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* ── Capability Picker ───────────────────── */
	.capabilities-section {
		margin-bottom: 24px;
	}

	.cap-error {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.2);
		border-radius: 4px;
		padding: 12px;
		color: var(--red);
		font-size: 0.875rem;
		margin-bottom: 16px;
	}

	.cap-loading {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 24px;
		color: var(--text-secondary);
		font-size: 0.875rem;
	}

	.cap-filters {
		display: flex;
		gap: 12px;
		margin-bottom: 16px;
		flex-wrap: wrap;
	}

	.cap-search {
		flex: 1;
		min-width: 200px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 10px 12px;
		font-family: var(--font-body);
		font-size: 0.875rem;
		color: var(--text);
	}

	.cap-search:focus {
		outline: none;
		border-color: var(--accent);
	}

	.cap-category-tabs {
		display: flex;
		gap: 4px;
		flex-wrap: wrap;
	}

	.cap-cat-btn {
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 3px;
		padding: 6px 12px;
		font-family: var(--font-heading);
		font-size: 0.65rem;
		font-weight: 500;
		color: var(--text-secondary);
		cursor: pointer;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		transition: all 0.2s;
	}

	.cap-cat-btn:hover {
		border-color: var(--border-strong);
		color: var(--text);
	}

	.cap-cat-btn.active {
		background: color-mix(in srgb, var(--cat-color, var(--accent)) 15%, var(--bg-elevated));
		border-color: var(--cat-color, var(--accent));
		color: var(--cat-color, var(--accent));
	}

	.selected-caps {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-bottom: 16px;
		padding: 12px;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
	}

	.selected-cap-tag {
		display: flex;
		align-items: center;
		gap: 6px;
		background: var(--accent-dim);
		color: var(--accent);
		padding: 4px 10px;
		border-radius: 3px;
		font-family: var(--font-mono);
		font-size: 0.75rem;
	}

	.remove-cap {
		background: transparent;
		border: none;
		color: var(--accent);
		cursor: pointer;
		font-size: 1rem;
		line-height: 1;
		padding: 0;
		opacity: 0.7;
		transition: opacity 0.2s;
	}

	.remove-cap:hover {
		opacity: 1;
	}

	.cap-list {
		max-height: 400px;
		overflow-y: auto;
		border: 1px solid var(--border);
		border-radius: 4px;
	}

	.cap-group {
		padding: 12px 16px;
		border-bottom: 1px solid var(--border);
	}

	.cap-group:last-child {
		border-bottom: none;
	}

	.cap-group-title {
		font-family: var(--font-heading);
		font-size: 0.7rem;
		font-weight: 600;
		color: var(--cat-color);
		text-transform: uppercase;
		letter-spacing: 1px;
		margin: 0 0 12px 0;
	}

	.cap-items {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.cap-item {
		display: flex;
		align-items: flex-start;
		gap: 10px;
		cursor: pointer;
		padding: 8px;
		border-radius: 4px;
		transition: background 0.2s;
	}

	.cap-item:hover {
		background: var(--bg-surface);
	}

	.cap-item input[type="checkbox"] {
		margin-top: 2px;
		width: 16px;
		height: 16px;
		accent-color: var(--accent);
		cursor: pointer;
		flex-shrink: 0;
	}

	.cap-item-content {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.cap-item-name {
		font-family: var(--font-heading);
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--text);
	}

	.cap-item-desc {
		font-size: 0.75rem;
		color: var(--text-secondary);
		line-height: 1.4;
	}

	.cap-item-roles {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-top: 4px;
	}

	.cap-role-tag {
		font-family: var(--font-mono);
		font-size: 0.6rem;
		padding: 2px 6px;
		border-radius: 2px;
		background: var(--bg-surface);
		color: var(--text-dim);
	}

	.cap-empty {
		padding: 32px;
		text-align: center;
		color: var(--text-dim);
		font-size: 0.875rem;
	}

	.custom-cap-section {
		display: flex;
		gap: 8px;
		margin-top: 16px;
		padding-top: 16px;
		border-top: 1px solid var(--border);
	}

	.custom-cap-input {
		flex: 1;
		background: var(--bg-elevated);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 10px 12px;
		font-family: var(--font-mono);
		font-size: 0.875rem;
		color: var(--text);
	}

	.custom-cap-input:focus {
		outline: none;
		border-color: var(--accent);
	}

	.add-custom-btn {
		background: var(--accent);
		color: #fff;
		border: none;
		border-radius: 4px;
		padding: 10px 20px;
		font-family: var(--font-heading);
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.5px;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.add-custom-btn:hover:not(:disabled) {
		opacity: 0.9;
	}

	.add-custom-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* ── Responsive ──────────────────────────── */
	@media (max-width: 768px) {
		.connect-page {
			padding: 16px;
		}

		.step-line {
			width: 30px;
		}

		.tab-headers {
			flex-wrap: wrap;
		}

		.tab-btn {
			padding: 10px 14px;
			font-size: 0.6875rem;
		}

		.code-panel pre {
			padding: 16px;
			font-size: 0.75rem;
		}

		.copy-code-btn {
			position: static;
			margin: 0 16px 16px;
			width: calc(100% - 32px);
			justify-content: center;
		}
	}
</style>
