/** Agent states store */

import { writable, derived, type Writable } from 'svelte/store';
import { onTopic, type MeshEvent } from './websocket';

export interface AgentInfo {
	id: string;
	role: string;
	capabilities: string[];
	status: 'online' | 'busy' | 'degraded' | 'suspect' | 'dead' | 'rejoining';
	lastSeen: number;
	load: number;
	activeOrders: number;
	uptime: number;
	balance: number;
	reputation: Record<string, number>;
}

export const agents: Writable<Map<string, AgentInfo>> = writable(new Map());

export const agentList = derived(agents, ($agents) => Array.from($agents.values()));
export const activeAgentCount = derived(agentList, ($list) =>
	$list.filter(a => a.status === 'online' || a.status === 'busy').length
);
export const totalAgents = derived(agentList, ($list) => $list.length);

// Initialize listeners
onTopic('discovery/announce', (event: MeshEvent) => {
	const p = event.payload?.payload || event.payload;
	if (!p?.agent_id) return;

	agents.update(map => {
		const existing = map.get(p.agent_id);
		map.set(p.agent_id, {
			id: p.agent_id,
			role: p.role || existing?.role || 'unknown',
			capabilities: p.capabilities || existing?.capabilities || [],
			status: p.status || 'online',
			lastSeen: Date.now(),
			load: existing?.load || 0,
			activeOrders: existing?.activeOrders || 0,
			uptime: existing?.uptime || 0,
			balance: existing?.balance || 0,
			reputation: existing?.reputation || {},
		});
		return new Map(map);
	});
});

onTopic('discovery/heartbeat', (event: MeshEvent) => {
	const p = event.payload?.payload || event.payload;
	if (!p?.agent_id) return;

	agents.update(map => {
		const existing = map.get(p.agent_id);
		if (existing) {
			existing.lastSeen = Date.now();
			existing.load = p.load || 0;
			existing.activeOrders = p.active_orders || 0;
			existing.uptime = p.uptime_seconds || 0;
			existing.status = p.status === 'healthy' ? 'online' : p.status;
			map.set(p.agent_id, { ...existing });
		}
		return new Map(map);
	});
});

onTopic('discovery/goodbye', (event: MeshEvent) => {
	const p = event.payload?.payload || event.payload;
	if (!p?.agent_id) return;

	agents.update(map => {
		const existing = map.get(p.agent_id);
		if (existing) {
			existing.status = 'dead';
			map.set(p.agent_id, { ...existing });
		}
		return new Map(map);
	});
});

onTopic('health/alerts', (event: MeshEvent) => {
	const p = event.payload?.payload || event.payload;
	if (!p?.suspect_agent_id) return;

	agents.update(map => {
		const existing = map.get(p.suspect_agent_id);
		if (existing) {
			existing.status = p.severity === 'critical' ? 'dead' : 'suspect';
			map.set(p.suspect_agent_id, { ...existing });
		}
		return new Map(map);
	});
});
