/**
 * Driver.js tour configuration for MESH platform demo.
 * Defines tour steps for landing page and dashboard walkthroughs.
 */

export interface TourStep {
	element?: string;
	popover: {
		title: string;
		description: string;
		side?: 'top' | 'bottom' | 'left' | 'right';
		align?: 'start' | 'center' | 'end';
	};
}

export const landingTourSteps: TourStep[] = [
	{
		element: '#hero',
		popover: {
			title: 'Welcome to MESH',
			description: 'MESH is a decentralized multi-agent supply chain protocol. Agents autonomously discover, negotiate, and trade — secured by Byzantine Fault Tolerant consensus and cryptographic identity.',
			side: 'bottom',
			align: 'center',
		},
	},
	{
		element: '#features',
		popover: {
			title: 'Core Capabilities',
			description: 'Six pillars power the MESH network: Discovery, Negotiation, Smart Escrow, Quality Verification, Self-Healing, and Per-Capability Reputation scoring.',
			side: 'top',
			align: 'center',
		},
	},
	{
		element: '#protocol',
		popover: {
			title: 'Protocol Flow',
			description: 'Every transaction follows 8 cryptographically-verified phases: DISCOVER → REQUEST → BID → NEGOTIATE → COMMIT → EXECUTE → VERIFY → SETTLE. Each phase is recorded on the Hashgraph ledger.',
			side: 'top',
			align: 'center',
		},
	},
	{
		element: '#architecture',
		popover: {
			title: 'Architecture Layers',
			description: 'Four layers: Transport (FoxMQ MQTT 5.0 BFT cluster), Consensus (Hashgraph ordering), Protocol (state machine + escrow), and Agents (LLM-powered autonomous decision-making).',
			side: 'top',
			align: 'center',
		},
	},
	{
		element: '#demo',
		popover: {
			title: 'Live Demo',
			description: 'Watch 6 autonomous agents trade electronics in real-time. The demo runs a 3-minute supply chain scenario with order negotiation, delivery, inspection, and self-healing from agent failures.',
			side: 'top',
			align: 'center',
		},
	},
	{
		element: '#tour-launch-btn',
		popover: {
			title: 'Ready to Explore?',
			description: 'Click "Launch Dashboard" to enter the full platform — manage agents, monitor orders, track billing, and configure your workspace.',
			side: 'top',
			align: 'center',
		},
	},
];

export const dashboardTourSteps: TourStep[] = [
	{
		element: '#tour-header',
		popover: {
			title: 'Dashboard Header',
			description: 'Your command center. See workspace name, connection status (LIVE/OFFLINE), active agent count, completed orders, and message throughput at a glance.',
			side: 'bottom',
			align: 'center',
		},
	},
	{
		element: '#tour-nav-tabs',
		popover: {
			title: 'Navigation',
			description: 'Navigate between: Dashboard (overview), Agents (manage & monitor), Orders (track lifecycle), Ledger (transactions), Billing (credits & plans), Admin (analytics), and Settings (API keys, capabilities, config).',
			side: 'bottom',
			align: 'center',
		},
	},
	{
		element: '#tour-metrics',
		popover: {
			title: 'Real-Time Metrics',
			description: 'Live performance metrics from the MESH network. Active agents, total agents, settled orders, message count, average latency, and throughput — all updating in real-time via WebSocket.',
			side: 'bottom',
			align: 'center',
		},
	},
	{
		element: '#tour-agents',
		popover: {
			title: 'Swarm Agents',
			description: 'Each card represents an autonomous agent in the mesh. Color-coded by role: Buyer (orange), Supplier (green), Logistics (blue), Inspector (purple), Oracle (yellow). Watch their status, load, and active orders.',
			side: 'right',
			align: 'start',
		},
	},
	{
		element: '#tour-orders',
		popover: {
			title: 'Order Pipeline',
			description: 'Track every order through 7 phases: BID → NEG → CMT → FUL → SHP → INS → SET. Green = complete, orange = active, red = failed. Each order is secured by MESH_CREDIT escrow.',
			side: 'left',
			align: 'start',
		},
	},
	{
		element: '#tour-events',
		popover: {
			title: 'Event Stream',
			description: 'Real-time message feed from the MQTT network. See discovery announcements, order negotiations, shipping updates, quality reports, and reputation changes as they happen.',
			side: 'left',
			align: 'start',
		},
	},
	{
		element: '#tour-chaos',
		popover: {
			title: 'Chaos Controls',
			description: 'Test MESH self-healing! Kill any agent and watch the network detect the failure, redistribute work to capable peers, and recover — all autonomously within seconds.',
			side: 'left',
			align: 'start',
		},
	},
	{
		popover: {
			title: 'Tour Complete!',
			description: 'You\'ve seen the core of MESH. Explore the tabs to dive deeper: manage agents, review orders, check billing, or connect your own IoT devices via the SDK. Happy trading! 🚀',
		},
	},
];

/** Local storage key for tracking first visit */
export const TOUR_SEEN_KEY = 'mesh_tour_seen';
export const DASHBOARD_TOUR_SEEN_KEY = 'mesh_dashboard_tour_seen';
