/** WebSocket connection manager */

import { writable, type Writable } from 'svelte/store';

export interface MeshEvent {
	topic: string;
	timestamp: number;
	payload: any;
	qos: number;
	retain: boolean;
}

export const connected = writable(false);
export const events: Writable<MeshEvent[]> = writable([]);
export const lastEvent: Writable<MeshEvent | null> = writable(null);
export const messageCount = writable(0);

const MAX_EVENTS = 200;

let ws: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

export function connect(url: string = 'ws://localhost:8080') {
	if (ws) {
		ws.close();
	}

	ws = new WebSocket(url);

	ws.onopen = () => {
		connected.set(true);
		console.log('[WS] Connected to bridge');
	};

	ws.onmessage = (event) => {
		try {
			const data: MeshEvent = JSON.parse(event.data);
			lastEvent.set(data);
			messageCount.update(n => n + 1);
			events.update(list => {
				const updated = [data, ...list];
				return updated.slice(0, MAX_EVENTS);
			});

			// Dispatch to topic-specific handlers
			dispatchEvent(data);
		} catch (e) {
			console.error('[WS] Parse error:', e);
		}
	};

	ws.onclose = () => {
		connected.set(false);
		console.log('[WS] Disconnected — reconnecting in 3s');
		reconnectTimer = setTimeout(() => connect(url), 3000);
	};

	ws.onerror = (err) => {
		console.error('[WS] Error:', err);
	};
}

export function disconnect() {
	if (reconnectTimer) clearTimeout(reconnectTimer);
	if (ws) ws.close();
}

export function sendCommand(action: string, target: string = '') {
	if (ws && ws.readyState === WebSocket.OPEN) {
		ws.send(JSON.stringify({ action, target }));
	}
}

// Topic-specific dispatch
type EventHandler = (event: MeshEvent) => void;
const handlers: Map<string, EventHandler[]> = new Map();

export function onTopic(pattern: string, handler: EventHandler) {
	if (!handlers.has(pattern)) {
		handlers.set(pattern, []);
	}
	handlers.get(pattern)!.push(handler);
}

function dispatchEvent(event: MeshEvent) {
	for (const [pattern, handlerList] of handlers) {
		if (event.topic.includes(pattern)) {
			handlerList.forEach(h => h(event));
		}
	}
}
