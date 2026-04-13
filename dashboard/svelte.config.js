import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: '404.html',
			precompress: false,
			strict: true
		}),
		prerender: {
			handleHttpError: ({ path, message }) => {
				// These routes are client-side rendered (SPA) and will 500 during prerender
				// because they depend on browser APIs. The static adapter with fallback handles them.
				const ignorePrefixes = ['/docs', '/auth', '/dashboard', '/workspaces'];
				if (ignorePrefixes.some(p => path.startsWith(p))) return;
				throw new Error(`${message}: ${path}`);
			}
		}
	}
};

export default config;
