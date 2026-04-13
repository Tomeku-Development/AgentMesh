/**
 * Base API client for MESH platform.
 * Handles authentication headers and common request patterns.
 */

import { browser } from '$app/environment';
import { logout } from '$lib/stores/auth';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';

/**
 * Get authentication headers for API requests.
 * Retrieves JWT token from localStorage if available.
 */
function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (browser) {
    const token = localStorage.getItem('mesh_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Handle API response errors.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      // Token expired or invalid - logout and redirect
      logout();
    }
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

/**
 * Perform a GET request to the API.
 */
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse<T>(response);
}

/**
 * Perform a POST request to the API.
 */
export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}

/**
 * Perform a PUT request to the API.
 */
export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse<T>(response);
}

/**
 * Perform a DELETE request to the API.
 */
export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    if (response.status === 401) {
      logout();
    }
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `API error: ${response.status} ${response.statusText}`);
  }
}
