/**
 * API module barrel export.
 * Re-exports all API functions and types for convenient imports.
 */

// Base client
export { apiGet, apiPost, apiPut, apiDelete } from './client';

// Domain modules
export { getAgents, getAgentStatus } from './agents';
export { getOrders, getOrder, getOrderEvents } from './orders';
export { getTransactions, getBalances } from './ledger';
export * from './auth';
export * from './workspaces';
export * from './apikeys';

// Re-export types for convenience
export type {
  Agent,
  AgentListResponse,
  AgentStatus,
  Order,
  OrderListResponse,
  OrderEvent,
  LedgerEntry,
  LedgerListResponse,
  Balance,
  BalancesResponse,
  ApiError,
  PaginatedParams,
  User,
  TokenResponse,
  Workspace,
  WorkspaceListResponse,
  APIKey,
  APIKeyCreated,
  APIKeyListResponse,
} from '$lib/types/api';
