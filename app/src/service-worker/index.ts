import { self } from '$app/service-worker';
import { assets, immutable, prerendered } from '$app/manifest';

// Offline support: precache the app shell, static assets and every prerendered
// puzzle page. Pages are network-first so a redeploy with a new puzzle shows up
// as soon as you're online; everything else is cache-first.
const CACHE = `gatan-${Date.now()}`;
const PRECACHE = [...immutable, ...assets, ...prerendered].map((f) => f.path);
const IMMUTABLE = new Set(immutable.map((f) => new URL(f.path, self.registration.scope).pathname));

self.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE)
			.then((cache) => cache.addAll(PRECACHE))
			.then(() => self.skipWaiting())
	);
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
			.then(() => self.clients.claim())
	);
});

self.addEventListener('fetch', (event) => {
	const req = event.request;
	if (req.method !== 'GET') return;
	const url = new URL(req.url);
	if (url.origin !== self.location.origin) return;

	event.respondWith(
		(async () => {
			const cache = await caches.open(CACHE);
			if (IMMUTABLE.has(url.pathname)) {
				const hit = await cache.match(req);
				if (hit) return hit;
			}
			try {
				const res = await fetch(req);
				if (res.ok) cache.put(req, res.clone());
				return res;
			} catch (err) {
				const hit = await cache.match(req, { ignoreSearch: true });
				if (hit) return hit;
				throw err;
			}
		})()
	);
});
