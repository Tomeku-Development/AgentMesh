/** Real-time metrics store */

import { writable, derived } from 'svelte/store';
import { messageCount } from './websocket';

export const latencySamples = writable<number[]>([]);
export const throughputSamples = writable<number[]>([]);

// Derived metrics
export const avgLatency = derived(latencySamples, ($samples) => {
	if ($samples.length === 0) return 0;
	return $samples.reduce((a, b) => a + b, 0) / $samples.length;
});

export const p99Latency = derived(latencySamples, ($samples) => {
	if ($samples.length === 0) return 0;
	const sorted = [...$samples].sort((a, b) => a - b);
	return sorted[Math.floor(sorted.length * 0.99)] || 0;
});

// Track messages per second
let lastCount = 0;
let lastTime = Date.now();

if (typeof window !== 'undefined') {
	setInterval(() => {
		const now = Date.now();
		const elapsed = (now - lastTime) / 1000;
		lastTime = now;

		messageCount.subscribe(count => {
			const mps = (count - lastCount) / elapsed;
			lastCount = count;
			throughputSamples.update(samples => {
				const updated = [...samples, mps];
				return updated.slice(-60); // Keep last 60 seconds
			});
		})();
	}, 1000);
}

export function recordLatency(ms: number) {
	latencySamples.update(samples => {
		const updated = [...samples, ms];
		return updated.slice(-100); // Keep last 100 samples
	});
}
