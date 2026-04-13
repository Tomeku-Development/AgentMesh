/**
 * TypeScript types matching the MESH platform backend schemas.
 * Field names follow snake_case to match Python backend exactly.
 */

// ============================================
// Agent Types
// ============================================

export interface Agent {
  id: string;
  workspace_id: string;
  agent_role: string;
  agent_mesh_id: string;
  capabilities: string;
  initial_balance: number;
  is_active: boolean;
  created_at: string;
}

export interface AgentListResponse {
  agents: Agent[];
}

export interface AgentStatus {
  status: string;
  load: number;
  active_orders: number;
  recorded_at: string;
}

// ============================================
// Order Types
// ============================================

export interface Order {
  id: string;
  workspace_id: string;
  goods: string;
  quantity: number;
  max_price_per_unit: number;
  current_status: string;
  winner_supplier_id: string | null;
  agreed_price_per_unit: number | null;
  bid_count: number;
  created_at: string;
}

export interface OrderListResponse {
  orders: Order[];
  total: number;
}

export interface OrderEvent {
  id: number;
  event_type: string;
  agent_id: string;
  payload_json: string | null;
  occurred_at: string;
  recorded_at: string;
}

// ============================================
// Ledger Types
// ============================================

export interface LedgerEntry {
  id: number;
  tx_id: string;
  tx_type: string;
  from_agent: string;
  to_agent: string;
  amount: number;
  order_id: string | null;
  memo: string | null;
  recorded_at: string;
}

export interface LedgerListResponse {
  entries: LedgerEntry[];
  total: number;
}

export interface Balance {
  agent_id: string;
  balance: number;
}

export interface BalancesResponse {
  balances: Balance[];
}

// ============================================
// Auth Types
// ============================================

export interface User {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ============================================
// Workspace Types
// ============================================

export interface Workspace {
  id: string;
  slug: string;
  name: string;
  owner_id: string;
  plan: string;
  max_agents: number;
  created_at: string;
}

export interface WorkspaceListResponse {
  workspaces: Workspace[];
}

// ============================================
// API Key Types
// ============================================

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}

export interface APIKeyCreated {
  id: string;
  name: string;
  key_prefix: string;
  raw_key: string;
  scopes: string;
  created_at: string;
  expires_at: string | null;
}

export interface APIKeyListResponse {
  keys: APIKey[];
}

// ============================================
// Common Types
// ============================================

export interface ApiError {
  detail: string;
}

export interface PaginatedParams {
  limit?: number;
  offset?: number;
}
