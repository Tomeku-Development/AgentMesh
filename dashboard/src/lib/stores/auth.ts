import { writable, derived, get } from 'svelte/store';
import { browser } from '$app/environment';
import type { User } from '$lib/types/api';

// Token state
function createTokenStore() {
  const stored = browser ? localStorage.getItem('mesh_token') : null;
  const storedRefresh = browser ? localStorage.getItem('mesh_refresh_token') : null;
  
  const accessToken = writable<string | null>(stored);
  const refreshTokenStore = writable<string | null>(storedRefresh);
  
  accessToken.subscribe(val => {
    if (browser) {
      if (val) localStorage.setItem('mesh_token', val);
      else localStorage.removeItem('mesh_token');
    }
  });
  
  refreshTokenStore.subscribe(val => {
    if (browser) {
      if (val) localStorage.setItem('mesh_refresh_token', val);
      else localStorage.removeItem('mesh_refresh_token');
    }
  });
  
  return { accessToken, refreshToken: refreshTokenStore };
}

const { accessToken, refreshToken } = createTokenStore();
export { accessToken, refreshToken };

// User state
export const currentUser = writable<User | null>(null);

// Derived
export const isAuthenticated = derived(accessToken, $token => !!$token);

// Actions
export function setTokens(access: string, refresh: string) {
  accessToken.set(access);
  refreshToken.set(refresh);
}

export function logout() {
  accessToken.set(null);
  refreshToken.set(null);
  currentUser.set(null);
  if (browser) {
    localStorage.removeItem('mesh_token');
    localStorage.removeItem('mesh_refresh_token');
    localStorage.removeItem('mesh_active_workspace');
    window.location.href = '/auth/login';
  }
}
