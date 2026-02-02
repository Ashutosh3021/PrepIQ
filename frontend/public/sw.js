// PrepIQ Service Worker for PWA functionality with resilient caching

const CACHE_NAME = 'prepiq-v1';
const urlsToCache = [
  '/',
  '/manifest.json',
  '/icons/android-chrome-192x192.png',
  '/icons/android-chrome-512x512.png',
  '/icons/apple-touch-icon.png',
  '/favicon.ico',
  '/favicon-16x16.png',
  '/favicon-32x32.png',
  '/apple-icon.png',
  '/icon.svg',
  '/icon-light-32x32.png',
  '/icon-dark-32x32.png',
  '/placeholder-logo.png',
  '/placeholder-logo.svg',
  '/placeholder-user.jpg',
  '/placeholder.jpg',
  '/placeholder.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(async (cache) => {
        console.log('Opened cache for installation');
        
        // Cache resources individually with error handling
        for (const url of urlsToCache) {
          try {
            await cache.add(url);
            console.log(`Successfully cached: ${url}`);
          } catch (error) {
            console.warn(`Failed to cache ${url}:`, error.message);
            // Continue with other resources - don't fail the entire installation
          }
        }
        
        console.log('Service Worker installation completed');
      })
      .catch((error) => {
        console.error('Failed to open cache during installation:', error);
      })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version if available, otherwise fetch from network
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
      .catch((error) => {
        console.error('Cache match failed:', error);
        // Fallback to network request
        return fetch(event.request);
      })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});