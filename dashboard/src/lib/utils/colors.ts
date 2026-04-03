// Tashi-inspired color palette for MESH dashboard

export const ROLE_COLORS: Record<string, string> = {
	buyer: '#ff6f00',     // tashi orange (primary)
	supplier: '#4ade80',  // green
	logistics: '#60a5fa', // blue
	inspector: '#c084fc', // purple
	oracle: '#fbbf24',    // gold
};

export const STATUS_COLORS: Record<string, string> = {
	online: '#4ade80',
	busy: '#fbbf24',
	degraded: '#ff6f00',
	suspect: '#ef4444',
	dead: '#52525b',
	rejoining: '#38bdf8',
};

export function roleColor(role: string): string {
	return ROLE_COLORS[role] || '#52525b';
}

export function statusColor(status: string): string {
	return STATUS_COLORS[status] || '#52525b';
}

export function roleIcon(role: string): string {
	const icons: Record<string, string> = {
		buyer: 'B',
		supplier: 'S',
		logistics: 'L',
		inspector: 'I',
		oracle: 'O',
	};
	return icons[role] || '?';
}
