import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type { Workspace } from '$lib/types/api';

function createWorkspaceStore() {
  const storedId = browser ? localStorage.getItem('mesh_active_workspace') : null;
  
  const activeWorkspaceId = writable<string | null>(storedId);
  const activeWorkspace = writable<Workspace | null>(null);
  
  activeWorkspaceId.subscribe(val => {
    if (browser) {
      if (val) localStorage.setItem('mesh_active_workspace', val);
      else localStorage.removeItem('mesh_active_workspace');
    }
  });
  
  return { activeWorkspaceId, activeWorkspace };
}

const { activeWorkspaceId, activeWorkspace } = createWorkspaceStore();
export { activeWorkspaceId, activeWorkspace };

export function setActiveWorkspace(workspace: Workspace) {
  activeWorkspaceId.set(workspace.id);
  activeWorkspace.set(workspace);
}

export function clearActiveWorkspace() {
  activeWorkspaceId.set(null);
  activeWorkspace.set(null);
}
