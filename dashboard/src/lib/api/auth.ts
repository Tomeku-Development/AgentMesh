import { apiGet, apiPost } from './client';
import type { User, TokenResponse } from '$lib/types/api';

export interface RegisterParams {
  email: string;
  password: string;
  display_name: string;
}

export interface LoginParams {
  email: string;
  password: string;
}

export async function register(params: RegisterParams): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/register', params);
}

export async function login(params: LoginParams): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/login', params);
}

export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  return apiPost<TokenResponse>('/auth/refresh', { refresh_token });
}

export async function getMe(): Promise<User> {
  return apiGet<User>('/auth/me');
}
