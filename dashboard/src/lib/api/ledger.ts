/**
 * Ledger API module.
 * Handles all ledger and transaction-related API requests.
 */

import { apiGet } from './client';
import type { LedgerListResponse, BalancesResponse } from '$lib/types/api';

export interface LedgerParams {
  limit?: number;
  offset?: number;
}

/**
 * List transactions in a workspace ledger.
 */
export async function getTransactions(
  workspaceId: string,
  params?: LedgerParams
): Promise<LedgerListResponse> {
  const query = new URLSearchParams();

  if (params?.limit !== undefined) {
    query.set('limit', String(params.limit));
  }
  if (params?.offset !== undefined) {
    query.set('offset', String(params.offset));
  }

  const queryString = query.toString();
  return apiGet<LedgerListResponse>(
    `/workspaces/${workspaceId}/ledger/transactions${queryString ? '?' + queryString : ''}`
  );
}

/**
 * Get current balances for all agents in a workspace.
 * Note: This endpoint may need to be implemented in the backend.
 */
export async function getBalances(workspaceId: string): Promise<BalancesResponse> {
  return apiGet<BalancesResponse>(`/workspaces/${workspaceId}/ledger/balances`);
}
