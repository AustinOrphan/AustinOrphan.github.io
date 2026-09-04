const CACHE_NAME = 'austin-orphan-portfolio-v4';
const OFFLINE_URL = '/';
const urlsToCache = [
  '/',
  '/blog',
  '/rss.xml',
  'https://fonts.googleapis.com/css2?family=Anta&family=Comfortaa:wght@700&family=Source+Sans+Pro:wght@900&display=swap',
  'https://unpkg.com/@phosphor-icons/web@2.1.1'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(urlsToCache);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    Promise.all([
      caches.keys().then(function(keys) {
        return Promise.all(
          keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
        );
      }),
      self.clients.claim(),
    ])
  );
});

// A cached HTML document points at content-hashed assets that the next deploy
// deletes, so serving stale HTML renders the site with no CSS at all. Documents
// must come from the network whenever the network is reachable; the cache is an
// offline fallback only. Hashed /_astro/ assets are immutable by construction,
// so those stay cache-first.
function isNavigation(request) {
  return request.mode === 'navigate' || request.destination === 'document';
}

// A response that followed a redirect keeps its "redirected" flag, and the
// browser refuses such a response for a navigation. GitHub Pages redirects
// /blog to /blog/, so the cached copy needs that flag stripped before use.
function replayable(response) {
  if (!response || !response.redirected) return Promise.resolve(response);
  return response.blob().then(function(body) {
    return new Response(body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers
    });
  });
}

function networkFirst(request) {
  return fetch(request).then(function(response) {
    if (response && response.ok && response.type === 'basic') {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(function(cache) {
        cache.put(request, copy);
      }).catch(function() { /* cache write is best effort */ });
    }
    return response;
  }).catch(function() {
    return caches.match(request).then(function(cached) {
      return cached || caches.match(OFFLINE_URL);
    }).then(replayable).then(function(fallback) {
      return fallback || new Response(
        '<!doctype html><meta charset="utf-8"><title>Offline</title>' +
        '<p>This page is not available offline.</p>',
        { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
      );
    });
  });
}

function isImmutableAsset(request) {
  return request.url.indexOf(self.location.origin + '/_astro/') === 0;
}

function cacheFirst(request) {
  return caches.match(request).then(function(cached) {
    if (cached) return cached;
    return fetch(request).then(function(response) {
      // Hashed asset filenames never change meaning, so keeping a copy is safe
      // and it is what makes the offline fallback render styled instead of bare.
      if (response && response.ok && isImmutableAsset(request)) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(request, copy);
        }).catch(function() { /* cache write is best effort */ });
      }
      return response;
    });
  });
}

self.addEventListener('fetch', function(event) {
  if (event.request.method !== 'GET') return;

  if (isNavigation(event.request)) {
    event.respondWith(networkFirst(event.request));
  } else {
    event.respondWith(cacheFirst(event.request));
  }
});
