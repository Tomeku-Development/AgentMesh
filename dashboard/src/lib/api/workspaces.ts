import { apiGet, apiPost } from './client';
import type { Workspace, WorkspaceListResponse } from '$lib/types/api';

export interface CreateWorkspaceParams {
  name: string;
  slug?: string;
}

export async function createWorkspace(params: CreateWorkspaceParams): Promise<Workspace> {
  return apiPost<Workspace>('/workspaces', params);
}

export async function getWorkspaces(): Promise<WorkspaceListResponse> {
  return apiGet<WorkspaceListResponse>('/workspaces');
}

export async function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiGet<Workspace>(`/workspaces/${workspaceId}`);
}
