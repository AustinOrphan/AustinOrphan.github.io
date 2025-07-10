const CACHE_NAME = 'austin-orphan-portfolio-v1';
const urlsToCache = [
  '/',
  '/styles/main.css',
  '/AustinOrphanResume.pdf',
  'https://fonts.googleapis.com/css2?family=Anta&family=Comfortaa:wght@700&family=Source+Sans+Pro:wght@900&display=swap',
  'https://unpkg.com/@phosphor-icons/web@2.1.1'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      }
    )
  );
});