const CACHE_NAME = 'austin-orphan-portfolio-v2';
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
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(keys) {
      return Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      );
    })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});
