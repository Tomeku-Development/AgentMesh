<script lang="ts">
	import type { AgentInfo } from '$lib/stores/agents';
	import { sendCommand } from '$lib/stores/websocket';
	import { roleColor, roleIcon } from '$lib/utils/colors';

	export let agents: AgentInfo[];

	function killAgent(id: string) {
		sendCommand('kill_agent', id);
	}

	function restartAgent(id: string) {
		sendCommand('restart_agent', id);
	}
</script>

<div class="controls" id="tour-chaos">
	<p class="hint">Trigger chaos events during the demo to test self-healing:</p>
	<div class="button-grid">
		{#each agents as agent (agent.id)}
			<div class="agent-control">
				<div class="agent-label">
					<span class="agent-role-dot" style="background: {roleColor(agent.role)}"></span>
					<span class="agent-name">{agent.role}</span>
					<span class="agent-short-id">{agent.id.slice(0, 6)}</span>
				</div>
				<div class="btn-group">
					{#if agent.status === 'dead'}
						<button class="btn btn-restart" on:click={() => restartAgent(agent.id)}>
							RESTART
						</button>
					{:else}
						<button
							class="btn btn-kill"
							on:click={() => killAgent(agent.id)}
							disabled={agent.status === 'dead'}
						>
							KILL
						</button>
					{/if}
				</div>
			</div>
		{/each}
	</div>
	{#if agents.length === 0}
		<p class="empty-state">No agents available</p>
	{/if}
</div>

<style>
	.controls {
		padding: 0;
	}
	.hint {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.7rem;
		color: var(--text-dim, #6b6b70);
		margin-bottom: 14px;
		line-height: 1.5;
	}

	.button-grid {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.agent-control {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 8px 12px;
		background: var(--bg-surface, #232427);
		border: 1px solid var(--border, rgba(255,255,255,0.08));
		border-radius: 3px;
		transition: border-color 0.2s;
	}
	.agent-control:hover {
		border-color: var(--border-strong, rgba(255,255,255,0.14));
	}

	.agent-label {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.agent-role-dot {
		width: 8px;
		height: 8px;
		border-radius: 2px;
		flex-shrink: 0;
	}
	.agent-name {
		font-family: 'Chakra Petch', sans-serif;
		font-size: 0.8rem;
		font-weight: 600;
		text-transform: capitalize;
		color: var(--text, #f4f4f5);
	}
	.agent-short-id {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.6rem;
		color: var(--text-dim, #6b6b70);
	}

	.btn-group {
		display: flex;
		gap: 6px;
	}

	.btn {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.6rem;
		font-weight: 600;
		letter-spacing: 1.5px;
		padding: 5px 14px;
		border-radius: 2px;
		border: none;
		cursor: pointer;
		transition: all 0.2s;
	}
	.btn-kill {
		background: rgba(239, 68, 68, 0.12);
		color: #ef4444;
		border: 1px solid rgba(239, 68, 68, 0.2);
	}
	.btn-kill:hover:not(:disabled) {
		background: rgba(239, 68, 68, 0.25);
		border-color: rgba(239, 68, 68, 0.4);
	}
	.btn-kill:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	.btn-restart {
		background: rgba(255, 111, 0, 0.12);
		color: #ff6f00;
		border: 1px solid rgba(255, 111, 0, 0.2);
	}
	.btn-restart:hover {
		background: rgba(255, 111, 0, 0.25);
		border-color: rgba(255, 111, 0, 0.4);
	}

	.empty-state {
		font-family: 'IBM Plex Mono', monospace;
		font-size: 0.75rem;
		color: var(--text-dim, #6b6b70);
		text-align: center;
		padding: 20px;
	}
</style>
