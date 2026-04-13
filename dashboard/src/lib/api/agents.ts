/**
 * Agent API module.
 * Handles all agent-related API requests.
 */

import { apiGet } from './client';
import type { Agent, AgentListResponse, AgentStatus } from '$lib/types/api';

/**
 * List all agents in a workspace.
 */
export async function getAgents(workspaceId: string): Promise<AgentListResponse> {
  return apiGet<AgentListResponse>(`/workspaces/${workspaceId}/agents`);
}

/**
 * Get status history for a specific agent.
 * Returns up to 50 most recent status logs.
 */
export async function getAgentStatus(
  workspaceId: string,
  agentId: string
): Promise<AgentStatus[]> {
  return apiGet<AgentStatus[]>(`/workspaces/${workspaceId}/agents/${agentId}/status`);
}
