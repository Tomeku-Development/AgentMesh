/**
 * Orders API module.
 * Handles all order-related API requests.
 */

import { apiGet } from './client';
import type { Order, OrderListResponse, OrderEvent } from '$lib/types/api';

export interface OrdersParams {
  status?: string;
  limit?: number;
  offset?: number;
}

/**
 * List orders in a workspace with optional filtering.
 */
export async function getOrders(
  workspaceId: string,
  params?: OrdersParams
): Promise<OrderListResponse> {
  const query = new URLSearchParams();

  if (params?.status) {
    query.set('status', params.status);
  }
  if (params?.limit !== undefined) {
    query.set('limit', String(params.limit));
  }
  if (params?.offset !== undefined) {
    query.set('offset', String(params.offset));
  }

  const queryString = query.toString();
  return apiGet<OrderListResponse>(
    `/workspaces/${workspaceId}/orders${queryString ? '?' + queryString : ''}`
  );
}

/**
 * Get a single order by ID.
 */
export async function getOrder(workspaceId: string, orderId: string): Promise<Order> {
  return apiGet<Order>(`/workspaces/${workspaceId}/orders/${orderId}`);
}

/**
 * Get event history for a specific order.
 */
export async function getOrderEvents(
  workspaceId: string,
  orderId: string
): Promise<OrderEvent[]> {
  return apiGet<OrderEvent[]>(`/workspaces/${workspaceId}/orders/${orderId}/events`);
}
