import { apiGet, apiPost, apiDelete } from './client';
import type { APIKeyCreated, APIKeyListResponse } from '$lib/types/api';

export interface CreateAPIKeyParams {
  name?: string;
  scopes?: string[];
  expires_in_days?: number | null;
}

export async function createAPIKey(workspaceId: string, params?: CreateAPIKeyParams): Promise<APIKeyCreated> {
  return apiPost<APIKeyCreated>(`/workspaces/${workspaceId}/api-keys`, params || {});
}

export async function getAPIKeys(workspaceId: string): Promise<APIKeyListResponse> {
  return apiGet<APIKeyListResponse>(`/workspaces/${workspaceId}/api-keys`);
}

export async function revokeAPIKey(workspaceId: string, keyId: string): Promise<void> {
  return apiDelete(`/workspaces/${workspaceId}/api-keys/${keyId}`);
}
