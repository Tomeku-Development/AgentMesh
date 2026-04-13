/**
 * Driver.js tour launcher for MESH platform.
 * Provides functions to start landing page and dashboard tours.
 */
import { driver } from 'driver.js';
import type { DriveStep } from 'driver.js';
import 'driver.js/dist/driver.css';
import { landingTourSteps, dashboardTourSteps, TOUR_SEEN_KEY, DASHBOARD_TOUR_SEEN_KEY } from './config';

/** MESH dark theme configuration for Driver.js */
const meshThemeConfig = {
	animate: true,
	overlayColor: 'rgba(0, 0, 0, 0.85)',
	stagePadding: 8,
	stageRadius: 8,
	allowClose: true,
	popoverClass: 'mesh-tour-popover',
	showProgress: true,
	progressText: 'current of total',
	nextBtnText: 'Next →',
	prevBtnText: '← Back',
	doneBtnText: 'Done ✓',
	showButtons: ['next', 'previous', 'close'],
};

function mapSteps(steps: typeof landingTourSteps): DriveStep[] {
	return steps.map((step) => ({
		element: step.element,
		popover: {
			title: step.popover.title,
			description: step.popover.description,
			side: step.popover.side,
			align: step.popover.align,
		},
	}));
}

export function startLandingTour(): void {
	const d = driver({
		...meshThemeConfig,
		steps: mapSteps(landingTourSteps),
		onDestroyStarted: () => {
			localStorage.setItem(TOUR_SEEN_KEY, 'true');
			d.destroy();
		},
	});
	d.drive();
}

export function startDashboardTour(): void {
	const d = driver({
		...meshThemeConfig,
		steps: mapSteps(dashboardTourSteps),
		onDestroyStarted: () => {
			localStorage.setItem(DASHBOARD_TOUR_SEEN_KEY, 'true');
			d.destroy();
		},
	});
	d.drive();
}

export function shouldShowLandingTour(): boolean {
	return !localStorage.getItem(TOUR_SEEN_KEY);
}

export function shouldShowDashboardTour(): boolean {
	return !localStorage.getItem(DASHBOARD_TOUR_SEEN_KEY);
}

export function resetTourState(): void {
	localStorage.removeItem(TOUR_SEEN_KEY);
	localStorage.removeItem(DASHBOARD_TOUR_SEEN_KEY);
}
