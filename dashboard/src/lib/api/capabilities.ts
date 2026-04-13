/**
 * Capability API module.
 * Handles all capability-related API requests.
 */

import { apiGet, apiPost, apiDelete } from './client';
import type { Capability } from '$lib/types/api';

/**
 * List all capabilities (system-wide).
 */
export async function getCapabilities(): Promise<Capability[]> {
	const data = await apiGet<{ capabilities: Capability[] }>('/capabilities');
	return data.capabilities;
}

/**
 * List capabilities for a specific workspace.
 */
export async function getWorkspaceCapabilities(workspaceId: string): Promise<Capability[]> {
	const data = await apiGet<{ capabilities: Capability[] }>(`/workspaces/${workspaceId}/capabilities`);
	return data.capabilities;
}

/**
 * Create a custom capability in a workspace.
 */
export async function createCapability(
	workspaceId: string,
	body: { name: string; display_name: string; category: string; description: string; applicable_roles: string[] }
): Promise<Capability> {
	return apiPost<Capability>(`/workspaces/${workspaceId}/capabilities`, body);
}

/**
 * Delete a custom capability from a workspace.
 */
export async function deleteCapability(workspaceId: string, capId: string): Promise<void> {
	await apiDelete(`/workspaces/${workspaceId}/capabilities/${capId}`);
}
