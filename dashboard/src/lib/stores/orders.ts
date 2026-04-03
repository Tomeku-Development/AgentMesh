/** Order lifecycle tracking store */

import { writable, derived, type Writable } from 'svelte/store';
import { onTopic, type MeshEvent } from './websocket';

export interface OrderInfo {
	id: string;
	goods: string;
	quantity: number;
	maxPrice: number;
	status: string;
	bids: number;
	winnerId: string;
	agreedPrice: number;
	createdAt: number;
	updatedAt: number;
	phases: string[];  // completed phase names
}

export const orders: Writable<Map<string, OrderInfo>> = writable(new Map());
export const orderList = derived(orders, ($orders) =>
	Array.from($orders.values()).sort((a, b) => b.createdAt - a.createdAt)
);
export const completedOrders = derived(orderList, ($list) =>
	$list.filter(o => o.status === 'settled').length
);

onTopic('orders/', (event: MeshEvent) => {
	const p = event.payload?.payload || event.payload;
	const topic = event.topic;

	if (!p?.order_id && !topic.includes('/orders/')) return;
	const orderId = p?.order_id || topic.split('/')[2];

	orders.update(map => {
		const existing = map.get(orderId) || {
			id: orderId,
			goods: '',
			quantity: 0,
			maxPrice: 0,
			status: 'open',
			bids: 0,
			winnerId: '',
			agreedPrice: 0,
			createdAt: Date.now(),
			updatedAt: Date.now(),
			phases: [],
		};

		if (topic.includes('/request')) {
			existing.goods = p.goods || '';
			existing.quantity = p.quantity || 0;
			existing.maxPrice = p.max_price_per_unit || 0;
			existing.status = 'bidding';
			existing.createdAt = Date.now();
			existing.phases.push('request');
		} else if (topic.includes('/bid') && !topic.includes('shipping')) {
			existing.bids++;
		} else if (topic.includes('/accept')) {
			existing.winnerId = p.supplier_id || '';
			existing.agreedPrice = p.agreed_price_per_unit || 0;
			existing.status = 'committed';
			existing.phases.push('accept');
		} else if (topic.includes('/status')) {
			existing.status = p.status || existing.status;
		} else if (topic.includes('/commit')) {
			existing.phases.push('commit');
		}

		existing.updatedAt = Date.now();
		map.set(orderId, { ...existing });
		return new Map(map);
	});
});
