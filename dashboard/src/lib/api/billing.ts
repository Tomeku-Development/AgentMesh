/**
 * Billing API client for MESH platform.
 * Handles usage summaries, subscriptions, quotas, and billing history.
 */

import { apiGet, apiPost } from './client';
import type {
	UsageSummary,
	SubscriptionPlan,
	QuotaStatus,
	BillingEntry,
	PlatformAnalytics
} from '../types/api';

export async function getUsageSummary(workspaceId: string, days: number = 30): Promise<UsageSummary> {
	return apiGet<UsageSummary>(`/admin/workspaces/${workspaceId}/usage?days=${days}`);
}

export async function getQuotaStatus(workspaceId: string): Promise<QuotaStatus> {
	return apiGet<QuotaStatus>(`/admin/workspaces/${workspaceId}/quota`);
}

export async function getPlans(): Promise<SubscriptionPlan[]> {
	const data = await apiGet<{ plans: SubscriptionPlan[] }>('/admin/plans');
	return data.plans;
}

export async function changePlan(workspaceId: string, planName: string): Promise<void> {
	await apiPost(`/admin/workspaces/${workspaceId}/plan?plan_name=${planName}`, {});
}

export async function getBillingHistory(workspaceId: string): Promise<BillingEntry[]> {
	const data = await apiGet<{ entries: BillingEntry[] }>(
		`/admin/workspaces/${workspaceId}/billing`
	);
	return data.entries;
}

export async function getPlatformAnalytics(): Promise<PlatformAnalytics> {
	return apiGet<PlatformAnalytics>('/admin/analytics');
}

export async function exportUsageCsv(workspaceId: string, days: number = 30): Promise<void> {
	// Direct download
	const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';
	window.open(`${baseUrl}/admin/workspaces/${workspaceId}/usage/export?days=${days}`, '_blank');
}
