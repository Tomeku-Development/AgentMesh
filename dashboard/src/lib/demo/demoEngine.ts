/**
 * Demo engine — animates mock data into dashboard stores
 * to simulate a live MESH supply chain during tours/demos.
 */

import { writable, get, type Writable } from 'svelte/store';
import type { AgentInfo } from '$lib/stores/agents';
import type { OrderInfo } from '$lib/stores/orders';
import type { MeshEvent } from '$lib/stores/websocket';
import {
	MOCK_AGENTS,
	MOCK_ORDERS,
	MOCK_EVENTS,
	MOCK_METRICS,
	generateRandomEvent,
	getNextPhase,
} from './mockData';

// Demo mode state
export const isDemoMode = writable(false);
export const DEMO_MODE_KEY = 'mesh_demo_mode';

// Store references
interface StoreSet {
	agents: Writable<Map<string, AgentInfo>>;
	orders: Writable<Map<string, OrderInfo>>;
	events: Writable<MeshEvent[]>;
	connected: Writable<boolean>;
	messageCount: Writable<number>;
	latencySamples: Writable<number[]>;
	throughputSamples: Writable<number[]>;
}

let stores: StoreSet | null = null;
let stopAnimation = false;
let animationTimers: ReturnType<typeof setTimeout>[] = [];
let intervalIds: ReturnType<typeof setInterval>[] = [];

// Track current state for animations
let currentEventIndex = 0;
let activeOrderIds: string[] = [];

/**
 * Start the demo animation
 */
export function startDemo(storeSet: StoreSet): void {
	if (typeof window === 'undefined') return;

	// Prevent multiple demo starts
	if (get(isDemoMode)) {
		stopDemo();
	}

	stores = storeSet;
	stopAnimation = false;
	currentEventIndex = 0;

	// Reset stores
	stores.agents.set(new Map());
	stores.orders.set(new Map());
	stores.events.set([]);
	stores.connected.set(false);
	stores.messageCount.set(0);
	stores.latencySamples.set([]);
	stores.throughputSamples.set([]);

	isDemoMode.set(true);

	// 1. Simulate connection establishment (500ms delay)
	scheduleTimeout(() => {
		stores?.connected.set(true);
	}, 500);

	// 2. Add agents one-by-one with 300ms delays (discovery animation)
	MOCK_AGENTS.forEach((agent, index) => {
		scheduleTimeout(() => {
			if (stopAnimation) return;
			stores?.agents.update((map) => {
				const newMap = new Map(map);
				newMap.set(agent.id, { ...agent, lastSeen: Date.now() });
				return newMap;
			});
			// Add discovery event for each agent
			addEvent({
				topic: 'mesh/discovery/announce',
				timestamp: Math.floor(Date.now() / 1000),
				payload: {
					header: { sender_role: agent.role },
					payload: {
						agent_id: agent.id,
						role: agent.role,
						capabilities: agent.capabilities,
						status: 'online',
					},
				},
				qos: 1,
				retain: false,
			});
		}, 800 + index * 300);
	});

	// 3. Add orders progressively after agents are discovered
	const ordersStartDelay = 800 + MOCK_AGENTS.length * 300 + 500;
	MOCK_ORDERS.forEach((order, index) => {
		scheduleTimeout(() => {
			if (stopAnimation) return;
			stores?.orders.update((map) => {
				const newMap = new Map(map);
				newMap.set(order.id, { ...order });
				return newMap;
			});
			activeOrderIds.push(order.id);
			// Add order request event
			addEvent({
				topic: 'mesh/orders/request',
				timestamp: Math.floor(Date.now() / 1000),
				payload: {
					header: { sender_role: 'buyer' },
					payload: {
						order_id: order.id,
						goods: order.goods,
						quantity: order.quantity,
						max_price_per_unit: order.maxPrice,
					},
				},
				qos: 1,
				retain: false,
			});
		}, ordersStartDelay + index * 200);
	});

	// 4. Stream initial events from mock list
	const eventsStartDelay = ordersStartDelay + MOCK_ORDERS.length * 200 + 500;
	MOCK_EVENTS.forEach((event, index) => {
		scheduleTimeout(() => {
			if (stopAnimation) return;
			addEvent(event);
			stores?.messageCount.update((n) => n + 1);
		}, eventsStartDelay + index * 400);
	});

	// 5. Set initial metrics after initial events
	scheduleTimeout(() => {
		if (stopAnimation) return;
		stores?.latencySamples.set([...MOCK_METRICS.latencySamples]);
		stores?.throughputSamples.set([...MOCK_METRICS.throughputSamples]);
		stores?.messageCount.set(MOCK_METRICS.messageCount);
	}, eventsStartDelay + MOCK_EVENTS.length * 400 + 500);

	// 6. Start periodic updates
	const periodicStartDelay = eventsStartDelay + MOCK_EVENTS.length * 400 + 1000;
	scheduleTimeout(() => {
		if (stopAnimation) return;
		startPeriodicUpdates();
	}, periodicStartDelay);
}

/**
 * Stop the demo animation and clean up
 */
export function stopDemo(): void {
	stopAnimation = true;

	// Clear all scheduled timeouts
	animationTimers.forEach((t) => clearTimeout(t));
	animationTimers = [];

	// Clear all intervals
	intervalIds.forEach((id) => clearInterval(id));
	intervalIds = [];

	isDemoMode.set(false);
	stores = null;
}

/**
 * Check if demo mode is currently active
 */
export function getDemoMode(): boolean {
	return get(isDemoMode);
}

// ============================================================
// INTERNAL HELPERS
// ============================================================

function scheduleTimeout(fn: () => void, delay: number): void {
	if (typeof window === 'undefined') return;
	const timer = setTimeout(fn, delay);
	animationTimers.push(timer);
}

function scheduleInterval(fn: () => void, interval: number): ReturnType<typeof setInterval> {
	if (typeof window === 'undefined') return 0 as unknown as ReturnType<typeof setInterval>;
	const id = setInterval(fn, interval);
	intervalIds.push(id);
	return id;
}

function addEvent(event: MeshEvent): void {
	if (!stores || stopAnimation) return;
	stores.events.update((list) => {
		const updated = [event, ...list];
		return updated.slice(0, 200); // Keep last 200 events
	});
}

// ============================================================
// PERIODIC ANIMATION LOOPS
// ============================================================

function startPeriodicUpdates(): void {
	if (!stores || stopAnimation) return;

	// 1. Event streaming — new generated events every 2-3s
	scheduleInterval(() => {
		if (stopAnimation || !stores) return;
		const event = generateRandomEvent();
		addEvent(event);
		stores.messageCount.update((n) => n + 1);
	}, 2500);

	// 2. Order progression — every 5-8 seconds, advance one order to next phase
	scheduleInterval(() => {
		if (stopAnimation || !stores) return;
		advanceRandomOrder();
	}, 6000);

	// 3. Metrics updates — fluctuate latency/throughput every 2s
	scheduleInterval(() => {
		if (stopAnimation || !stores) return;
		updateMetrics();
	}, 2000);

	// 4. Agent load fluctuation — randomly adjust agent load ±5% every 3s
	scheduleInterval(() => {
		if (stopAnimation || !stores) return;
		fluctuateAgentLoads();
	}, 3000);

	// 5. Agent heartbeats — every 5s
	scheduleInterval(() => {
		if (stopAnimation || !stores) return;
		sendAgentHeartbeats();
	}, 5000);
}

function advanceRandomOrder(): void {
	if (!stores || activeOrderIds.length === 0) return;

	// Pick a random order that hasn't settled yet
	const orders = get(stores.orders);
	const unsettledOrderIds = activeOrderIds.filter((id) => {
		const order = orders.get(id);
		return order && order.status !== 'settled' && order.status !== 'failed';
	});

	if (unsettledOrderIds.length === 0) return;

	const randomId = unsettledOrderIds[Math.floor(Math.random() * unsettledOrderIds.length)];
	const order = orders.get(randomId);
	if (!order) return;

	const nextPhase = getNextPhase(order.status);
	if (!nextPhase) return;

	// Update the order
	stores.orders.update((map) => {
		const newMap = new Map(map);
		const updatedOrder = { ...order, status: nextPhase, updatedAt: Date.now() };
		if (!updatedOrder.phases.includes(nextPhase)) {
			updatedOrder.phases = [...updatedOrder.phases, nextPhase];
		}
		newMap.set(randomId, updatedOrder);
		return newMap;
	});

	// Add appropriate event based on phase
	let eventTopic = 'mesh/orders/status';
	let senderRole = 'system';
	let payload: Record<string, unknown> = { order_id: randomId, status: nextPhase };

	switch (nextPhase) {
		case 'committed':
			eventTopic = 'mesh/orders/committed';
			senderRole = 'buyer';
			payload = {
				order_id: randomId,
				escrow_amount: order.agreedPrice * order.quantity,
			};
			break;
		case 'fulfilling':
			eventTopic = 'mesh/orders/fulfill';
			senderRole = order.winnerId?.startsWith('agent-supplier') ? 'supplier' : 'system';
			break;
		case 'shipping':
			eventTopic = 'mesh/logistics/pickup';
			senderRole = 'logistics';
			break;
		case 'inspecting':
			eventTopic = 'mesh/inspection/scheduled';
			senderRole = 'inspector';
			break;
		case 'settled':
			eventTopic = 'mesh/ledger/settlement';
			senderRole = 'system';
			payload = {
				order_id: randomId,
				amount_released: order.agreedPrice * order.quantity,
				recipient: order.winnerId,
			};
			break;
	}

	addEvent({
		topic: eventTopic,
		timestamp: Math.floor(Date.now() / 1000),
		payload: {
			header: { sender_role: senderRole },
			payload,
		},
		qos: 1,
		retain: false,
	});

	// Update message count
	stores.messageCount.update((n) => n + 1);
}

function updateMetrics(): void {
	if (!stores) return;

	// Fluctuate latency around 12ms with small variance
	const baseLatency = 12;
	const latencyVariance = (Math.random() - 0.5) * 4; // ±2ms
	const newLatency = Math.max(8, baseLatency + latencyVariance);

	stores.latencySamples.update((samples) => {
		const updated = [...samples, newLatency];
		return updated.slice(-100); // Keep last 100 samples
	});

	// Fluctuate throughput around 28 msg/s
	const baseThroughput = 28;
	const throughputVariance = (Math.random() - 0.5) * 6; // ±3 msg/s
	const newThroughput = Math.max(20, baseThroughput + throughputVariance);

	stores.throughputSamples.update((samples) => {
		const updated = [...samples, newThroughput];
		return updated.slice(-60); // Keep last 60 seconds
	});
}

function fluctuateAgentLoads(): void {
	if (!stores) return;

	stores.agents.update((map) => {
		const newMap = new Map(map);
		newMap.forEach((agent, id) => {
			// Random fluctuation ±0.05 (5%)
			const fluctuation = (Math.random() - 0.5) * 0.1;
			let newLoad = agent.load + fluctuation;
			// Clamp between 0.1 and 0.95
			newLoad = Math.max(0.1, Math.min(0.95, newLoad));
			newMap.set(id, { ...agent, load: newLoad });
		});
		return newMap;
	});
}

function sendAgentHeartbeats(): void {
	if (!stores) return;

	const agents = get(stores.agents);
	agents.forEach((agent) => {
		// 20% chance to send a heartbeat event for each agent
		if (Math.random() < 0.2) {
			addEvent({
				topic: 'mesh/discovery/heartbeat',
				timestamp: Math.floor(Date.now() / 1000),
				payload: {
					header: { sender_role: agent.role },
					payload: {
						agent_id: agent.id,
						load: agent.load,
						active_orders: agent.activeOrders,
						uptime_seconds: agent.uptime + Math.floor(Math.random() * 10),
						status: agent.status === 'online' ? 'healthy' : agent.status,
					},
				},
				qos: 0,
				retain: false,
			});
			stores?.messageCount.update((n) => n + 1);
		}
	});
}
