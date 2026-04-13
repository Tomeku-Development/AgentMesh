/**
 * Mock data for MESH demo mode.
 * Provides realistic agents, orders, events, and metrics
 * that animate to showcase the platform without a live backend.
 */

import type { AgentInfo } from '$lib/stores/agents';
import type { OrderInfo } from '$lib/stores/orders';
import type { MeshEvent } from '$lib/stores/websocket';

// ============================================================
// AGENTS — 6 agents matching the electronics scenario
// ============================================================

export const MOCK_AGENTS: AgentInfo[] = [
	{
		id: 'agent-buyer-001',
		role: 'buyer',
		status: 'online',
		capabilities: ['electronics', 'negotiate', 'evaluate_bids', 'manage_escrow'],
		balance: 8750.0,
		load: 0.65,
		activeOrders: 2,
		uptime: 1847,
		lastSeen: Date.now(),
		reputation: {
			electronics: 0.92,
			negotiate: 0.88,
		},
	},
	{
		id: 'agent-supplier-alpha',
		role: 'supplier',
		status: 'busy',
		capabilities: ['electronics', 'displays', 'keyboards', 'bid', 'fulfill_orders'],
		balance: 12340.0,
		load: 0.78,
		activeOrders: 3,
		uptime: 1832,
		lastSeen: Date.now(),
		reputation: {
			electronics: 0.91,
			displays: 0.94,
			keyboards: 0.89,
		},
	},
	{
		id: 'agent-supplier-beta',
		role: 'supplier',
		status: 'online',
		capabilities: ['electronics', 'batteries', 'bid', 'counter_offer'],
		balance: 9870.0,
		load: 0.42,
		activeOrders: 1,
		uptime: 1815,
		lastSeen: Date.now(),
		reputation: {
			electronics: 0.83,
			batteries: 0.87,
		},
	},
	{
		id: 'agent-logistics-001',
		role: 'logistics',
		status: 'online',
		capabilities: ['shipping', 'fragile_handling', 'express_delivery', 'gps_tracker'],
		balance: 6420.0,
		load: 0.55,
		activeOrders: 2,
		uptime: 1840,
		lastSeen: Date.now(),
		reputation: {
			shipping: 0.95,
			fragile_handling: 0.91,
		},
	},
	{
		id: 'agent-inspector-001',
		role: 'inspector',
		status: 'online',
		capabilities: ['quality_control', 'camera_inspection', 'temperature_sensor'],
		balance: 5200.0,
		load: 0.30,
		activeOrders: 1,
		uptime: 1825,
		lastSeen: Date.now(),
		reputation: {
			quality_control: 0.96,
			camera_inspection: 0.93,
		},
	},
	{
		id: 'agent-oracle-001',
		role: 'oracle',
		status: 'online',
		capabilities: ['market_data', 'price_feed', 'demand_analysis', 'predictive_analytics'],
		balance: 4890.0,
		load: 0.20,
		activeOrders: 0,
		uptime: 1850,
		lastSeen: Date.now(),
		reputation: {
			market_data: 0.98,
			price_feed: 0.97,
		},
	},
];

// ============================================================
// ORDERS — 8 orders in various lifecycle phases
// ============================================================
// Phases: bidding, negotiating, committed, fulfilling, shipping, inspecting, settled

export const MOCK_ORDERS: OrderInfo[] = [
	{
		id: 'ORD-2024-001',
		goods: 'OLED Displays',
		quantity: 500,
		maxPrice: 50.0,
		status: 'settled',
		bids: 3,
		winnerId: 'agent-supplier-alpha',
		agreedPrice: 42.50,
		createdAt: Date.now() - 120000,
		updatedAt: Date.now() - 20000,
		phases: ['request', 'bid', 'accept', 'commit', 'ship', 'inspect', 'settle'],
	},
	{
		id: 'ORD-2024-002',
		goods: 'Li-Ion Batteries',
		quantity: 1000,
		maxPrice: 22.0,
		status: 'inspecting',
		bids: 2,
		winnerId: 'agent-supplier-beta',
		agreedPrice: 18.75,
		createdAt: Date.now() - 95000,
		updatedAt: Date.now() - 15000,
		phases: ['request', 'bid', 'accept', 'commit', 'ship', 'inspect'],
	},
	{
		id: 'ORD-2024-003',
		goods: 'Mech Keyboards',
		quantity: 250,
		maxPrice: 75.0,
		status: 'shipping',
		bids: 4,
		winnerId: 'agent-supplier-alpha',
		agreedPrice: 67.0,
		createdAt: Date.now() - 75000,
		updatedAt: Date.now() - 12000,
		phases: ['request', 'bid', 'accept', 'commit', 'ship'],
	},
	{
		id: 'ORD-2024-004',
		goods: 'PCB Assemblies',
		quantity: 2000,
		maxPrice: 10.0,
		status: 'fulfilling',
		bids: 5,
		winnerId: 'agent-supplier-alpha',
		agreedPrice: 8.20,
		createdAt: Date.now() - 55000,
		updatedAt: Date.now() - 8000,
		phases: ['request', 'bid', 'accept', 'commit', 'fulfill'],
	},
	{
		id: 'ORD-2024-005',
		goods: 'Capacitor Arrays',
		quantity: 5000,
		maxPrice: 2.0,
		status: 'committed',
		bids: 3,
		winnerId: 'agent-supplier-beta',
		agreedPrice: 1.50,
		createdAt: Date.now() - 40000,
		updatedAt: Date.now() - 5000,
		phases: ['request', 'bid', 'accept', 'commit'],
	},
	{
		id: 'ORD-2024-006',
		goods: 'LED Panels',
		quantity: 300,
		maxPrice: 40.0,
		status: 'negotiating',
		bids: 2,
		winnerId: '',
		agreedPrice: 0,
		createdAt: Date.now() - 25000,
		updatedAt: Date.now() - 3000,
		phases: ['request', 'bid'],
	},
	{
		id: 'ORD-2024-007',
		goods: 'Thermal Paste',
		quantity: 800,
		maxPrice: 5.50,
		status: 'bidding',
		bids: 0,
		winnerId: '',
		agreedPrice: 0,
		createdAt: Date.now() - 10000,
		updatedAt: Date.now() - 10000,
		phases: ['request'],
	},
	{
		id: 'ORD-2024-008',
		goods: 'USB-C Connectors',
		quantity: 10000,
		maxPrice: 1.0,
		status: 'settled',
		bids: 2,
		winnerId: 'agent-supplier-beta',
		agreedPrice: 0.85,
		createdAt: Date.now() - 180000,
		updatedAt: Date.now() - 60000,
		phases: ['request', 'bid', 'accept', 'commit', 'ship', 'inspect', 'settle'],
	},
];

// ============================================================
// EVENTS — 40 realistic events showing supply chain activity
// ============================================================

export const MOCK_EVENTS: MeshEvent[] = [
	{
		topic: 'mesh/system/startup',
		timestamp: Math.floor((Date.now() - 180000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { message: 'MESH network initialized — BFT consensus active' },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/discovery/announce',
		timestamp: Math.floor((Date.now() - 175000) / 1000),
		payload: {
			header: { sender_role: 'oracle' },
			payload: { agent_id: 'agent-oracle-001', capabilities: ['market_data', 'price_feed'] },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/discovery/announce',
		timestamp: Math.floor((Date.now() - 170000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { agent_id: 'agent-buyer-001', capabilities: ['electronics', 'negotiate'] },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/discovery/announce',
		timestamp: Math.floor((Date.now() - 165000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { agent_id: 'agent-supplier-alpha', capabilities: ['electronics', 'displays', 'keyboards'] },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/discovery/announce',
		timestamp: Math.floor((Date.now() - 160000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { agent_id: 'agent-supplier-beta', capabilities: ['electronics', 'batteries'] },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/discovery/announce',
		timestamp: Math.floor((Date.now() - 155000) / 1000),
		payload: {
			header: { sender_role: 'logistics' },
			payload: { agent_id: 'agent-logistics-001', capabilities: ['shipping', 'fragile_handling'] },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/discovery/announce',
		timestamp: Math.floor((Date.now() - 150000) / 1000),
		payload: {
			header: { sender_role: 'inspector' },
			payload: { agent_id: 'agent-inspector-001', capabilities: ['quality_control', 'camera_inspection'] },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/oracle/price_update',
		timestamp: Math.floor((Date.now() - 145000) / 1000),
		payload: {
			header: { sender_role: 'oracle' },
			payload: { displays: 42.5, batteries: 18.75, keyboards: 67.0 },
		},
		qos: 0,
		retain: false,
	},
	{
		topic: 'mesh/orders/request',
		timestamp: Math.floor((Date.now() - 140000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-008', goods: 'USB-C Connectors', quantity: 10000, max_price_per_unit: 1.0 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/bid',
		timestamp: Math.floor((Date.now() - 135000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { order_id: 'ORD-2024-008', supplier_id: 'agent-supplier-beta', price: 0.85, quantity: 10000 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/committed',
		timestamp: Math.floor((Date.now() - 130000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-008', escrow_amount: 8500 },
		},
		qos: 2,
		retain: false,
	},
	{
		topic: 'mesh/orders/request',
		timestamp: Math.floor((Date.now() - 125000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-001', goods: 'OLED Displays', quantity: 500, max_price_per_unit: 50.0 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/bid',
		timestamp: Math.floor((Date.now() - 120000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { order_id: 'ORD-2024-001', supplier_id: 'agent-supplier-alpha', price: 42.5, quality_score: 0.95 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/negotiation/counter',
		timestamp: Math.floor((Date.now() - 115000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-001', counter_price: 40.0, strategy: 'moderate' },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/negotiation/accept',
		timestamp: Math.floor((Date.now() - 110000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { order_id: 'ORD-2024-001', agreed_price_per_unit: 42.5, rounds: 2 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/ledger/escrow_lock',
		timestamp: Math.floor((Date.now() - 105000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { order_id: 'ORD-2024-001', amount: 21250, verified_by: 'hashgraph' },
		},
		qos: 2,
		retain: false,
	},
	{
		topic: 'mesh/logistics/pickup',
		timestamp: Math.floor((Date.now() - 100000) / 1000),
		payload: {
			header: { sender_role: 'logistics' },
			payload: { order_id: 'ORD-2024-001', protocol: 'fragile_handling' },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/request',
		timestamp: Math.floor((Date.now() - 95000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-002', goods: 'Li-Ion Batteries', quantity: 1000, max_price_per_unit: 22.0 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/logistics/delivered',
		timestamp: Math.floor((Date.now() - 90000) / 1000),
		payload: {
			header: { sender_role: 'logistics' },
			payload: { order_id: 'ORD-2024-001', transit_time: 2, gps_verified: true },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/inspection/result',
		timestamp: Math.floor((Date.now() - 85000) / 1000),
		payload: {
			header: { sender_role: 'inspector' },
			payload: { order_id: 'ORD-2024-001', quality_score: 0.94, notes: 'minor cosmetic variance' },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/ledger/settlement',
		timestamp: Math.floor((Date.now() - 80000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { order_id: 'ORD-2024-001', amount_released: 21250, recipient: 'agent-supplier-alpha' },
		},
		qos: 2,
		retain: false,
	},
	{
		topic: 'mesh/reputation/update',
		timestamp: Math.floor((Date.now() - 78000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { agent_id: 'agent-supplier-alpha', category: 'electronics', old_score: 0.87, new_score: 0.92 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/request',
		timestamp: Math.floor((Date.now() - 75000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-003', goods: 'Mech Keyboards', quantity: 250, max_price_per_unit: 75.0 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/bid',
		timestamp: Math.floor((Date.now() - 70000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { order_id: 'ORD-2024-002', supplier_id: 'agent-supplier-beta', price: 18.75, hazmat_compliant: true },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/health/heartbeat',
		timestamp: Math.floor((Date.now() - 65000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { cycle: 47, healthy_agents: 6, failures: 0 },
		},
		qos: 0,
		retain: false,
	},
	{
		topic: 'mesh/oracle/demand',
		timestamp: Math.floor((Date.now() - 60000) / 1000),
		payload: {
			header: { sender_role: 'oracle' },
			payload: { electronics: 'HIGH', batteries: 'MEDIUM', trend: 'up' },
		},
		qos: 0,
		retain: false,
	},
	{
		topic: 'mesh/orders/committed',
		timestamp: Math.floor((Date.now() - 55000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-004', goods: 'PCB Assemblies', quantity: 2000, price: 8.2 },
		},
		qos: 2,
		retain: false,
	},
	{
		topic: 'mesh/logistics/tracking',
		timestamp: Math.floor((Date.now() - 50000) / 1000),
		payload: {
			header: { sender_role: 'logistics' },
			payload: { order_id: 'ORD-2024-003', gps: '34.052N,118.244W', eta: 1.5 },
		},
		qos: 0,
		retain: false,
	},
	{
		topic: 'mesh/inspection/scheduled',
		timestamp: Math.floor((Date.now() - 45000) / 1000),
		payload: {
			header: { sender_role: 'inspector' },
			payload: { order_id: 'ORD-2024-002', monitoring: 'temperature_sensor' },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/committed',
		timestamp: Math.floor((Date.now() - 40000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-005', goods: 'Capacitor Arrays', quantity: 5000, price: 1.5 },
		},
		qos: 2,
		retain: false,
	},
	{
		topic: 'mesh/ledger/credit_transfer',
		timestamp: Math.floor((Date.now() - 35000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { epoch: 52, transactions: 4, volume: 52950 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/negotiation/counter',
		timestamp: Math.floor((Date.now() - 30000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { order_id: 'ORD-2024-006', counter_price: 35.0, goods: 'LED Panels' },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/reputation/update',
		timestamp: Math.floor((Date.now() - 25000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { agent_id: 'agent-supplier-beta', category: 'batteries', old_score: 0.78, new_score: 0.83 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/health/heartbeat',
		timestamp: Math.floor((Date.now() - 20000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { cycle: 52, failures_last_30: 0 },
		},
		qos: 0,
		retain: false,
	},
	{
		topic: 'mesh/inspection/result',
		timestamp: Math.floor((Date.now() - 15000) / 1000),
		payload: {
			header: { sender_role: 'inspector' },
			payload: { order_id: 'ORD-2024-002', quality_score: 0.91, rfid_verified: true },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/request',
		timestamp: Math.floor((Date.now() - 10000) / 1000),
		payload: {
			header: { sender_role: 'buyer' },
			payload: { order_id: 'ORD-2024-007', goods: 'Thermal Paste', quantity: 800, max_price_per_unit: 5.5 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/bid',
		timestamp: Math.floor((Date.now() - 8000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { order_id: 'ORD-2024-007', supplier_id: 'agent-supplier-alpha', price: 4.5, delivery: 2 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/orders/bid',
		timestamp: Math.floor((Date.now() - 5000) / 1000),
		payload: {
			header: { sender_role: 'supplier' },
			payload: { order_id: 'ORD-2024-007', supplier_id: 'agent-supplier-beta', price: 4.8, delivery: 1 },
		},
		qos: 1,
		retain: false,
	},
	{
		topic: 'mesh/oracle/price_update',
		timestamp: Math.floor((Date.now() - 3000) / 1000),
		payload: {
			header: { sender_role: 'oracle' },
			payload: { trend: 'rising', confidence: 0.87, new_categories: 3 },
		},
		qos: 0,
		retain: false,
	},
	{
		topic: 'mesh/system/epoch',
		timestamp: Math.floor((Date.now() - 1000) / 1000),
		payload: {
			header: { sender_role: 'system' },
			payload: { epoch: 53, active_agents: 6, pending_orders: 3, settled_orders: 5 },
		},
		qos: 0,
		retain: false,
	},
];

// ============================================================
// METRICS — realistic performance numbers
// ============================================================

export const MOCK_METRICS = {
	latencySamples: [10, 12, 11, 13, 12, 14, 11, 10, 12, 13, 12, 11, 12, 14, 12, 11, 13, 12, 11, 12],
	throughputSamples: [25, 26, 28, 27, 29, 28, 30, 28, 27, 29, 28, 27, 28, 29, 28, 27, 28, 29, 28, 27],
	messageCount: 847,
};

// ============================================================
// GENERATOR FUNCTIONS — for creating new dynamic events
// ============================================================

const EVENT_TEMPLATES = [
	{ topic: 'mesh/health/heartbeat', sender: 'system', payload: { cycle: 0, healthy_agents: 6 } },
	{ topic: 'mesh/discovery/heartbeat', sender: 'supplier', payload: { agent_id: 'agent-supplier-alpha', load: 0.75 } },
	{ topic: 'mesh/discovery/heartbeat', sender: 'buyer', payload: { agent_id: 'agent-buyer-001', load: 0.6 } },
	{ topic: 'mesh/oracle/price_update', sender: 'oracle', payload: { trend: 'stable' } },
	{ topic: 'mesh/ledger/credit_transfer', sender: 'system', payload: { volume: 15000 } },
];

let eventCycle = 54;

export function generateRandomEvent(): MeshEvent {
	const template = EVENT_TEMPLATES[Math.floor(Math.random() * EVENT_TEMPLATES.length)];
	eventCycle++;
	
	const payload = { ...template.payload };
	if (template.topic === 'mesh/health/heartbeat') {
		payload.cycle = eventCycle;
	}
	
	return {
		topic: template.topic,
		timestamp: Math.floor(Date.now() / 1000),
		payload: {
			header: { sender_role: template.sender },
			payload,
		},
		qos: 0,
		retain: false,
	};
}

// ============================================================
// ORDER PHASE PROGRESSION — for animating orders through pipeline
// ============================================================

const PHASE_ORDER = ['bidding', 'negotiating', 'committed', 'fulfilling', 'shipping', 'inspecting', 'settled'];

export function getNextPhase(currentStatus: string): string | null {
	const idx = PHASE_ORDER.indexOf(currentStatus);
	if (idx >= 0 && idx < PHASE_ORDER.length - 1) {
		return PHASE_ORDER[idx + 1];
	}
	return null;
}

export function getPhaseIndex(status: string): number {
	return PHASE_ORDER.indexOf(status);
}
