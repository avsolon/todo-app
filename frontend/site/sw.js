// Service Worker для Todo Calendar PWA
const CACHE_NAME = 'todo-calendar-v1';
const ASSETS_TO_CACHE = [
    '/spisok-del-todo-app/',
    '/spisok-del-todo-app/index.html',
    '/spisok-del-todo-app/style.css',
    '/spisok-del-todo-app/app.js',
    '/spisok-del-todo-app/manifest.json'
];

// Установка — кэшируем статику
self.addEventListener('install', (event) => {
    console.log('📦 Service Worker: Установка');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Кэширование ресурсов');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => self.skipWaiting())
    );
});

// Активация — чистим старые кэши
self.addEventListener('activate', (event) => {
    console.log('✅ Service Worker: Активирован');
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            );
        }).then(() => self.clients.claim())
    );
});

// Стратегия: сначала кэш, потом сеть
self.addEventListener('fetch', (event) => {
    // Пропускаем API-запросы
    if (event.request.url.includes('/api/') ||
        event.request.url.includes('/todo-api/')) {
        return; // API не кэшируем
    }

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                // Возвращаем из кэша если есть
                if (cachedResponse) {
                    return cachedResponse;
                }

                // Иначе делаем запрос в сеть
                return fetch(event.request)
                    .then(response => {
                        // Кэшируем успешные ответы
                        if (response && response.status === 200) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME)
                                .then(cache => cache.put(event.request, responseClone));
                        }
                        return response;
                    })
                    .catch(() => {
                        // Офлайн — показываем заглушку для страниц
                        if (event.request.mode === 'navigate') {
                            return caches.match('/spisok-del-todo-app/');
                        }
                    });
            })
    );
});

// Push-уведомления (заготовка)
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Календарь дел';
    const options = {
        body: data.body || 'У вас есть задача',
        icon: '/spisok-del-todo-app/icon-192.png',
        badge: '/spisok-del-todo-app/icon-192.png'
    };

    event.waitUntil(self.registration.showNotification(title, options));
});