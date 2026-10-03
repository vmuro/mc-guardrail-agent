// fido-server/src/main/resources/static/firebase-messaging-sw.js

// Importa os scripts do Firebase (versão compatível)
importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js");

// Configuração do projeto Firebase
const firebaseConfig = {
  apiKey: "AIzaSyClcgX40Hs5fTGV57PY4JGRY78NJ6tFCco",
  authDomain: "guardrail-notifier-mvp.firebaseapp.com",
  projectId: "guardrail-notifier-mvp",
  storageBucket: "guardrail-notifier-mvp.appspot.com",
  messagingSenderId: "376986876849",
  appId: "1:376986876849:web:57487778033c282ebf1b90",
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Manipulador para quando a mensagem chega com o app em segundo plano
messaging.onBackgroundMessage((payload) => {
  console.log("[SW] Push recebido em segundo plano:", payload);

  // No padrão Data-Only, payload.data contém todas as informações da ordem
  const notificationTitle = payload.data?.title || payload.notification?.title || "🚨 GuardrailAI - Autorização de Ordem";
  const notificationBody = payload.data?.body || payload.notification?.body || "Nova recomendação disponível para autorização.";
  const challengeId = payload.data?.challengeId;
  const consentUrl = payload.data?.consentUrl || payload.data?.url;
  const notificationTag = payload.data?.tag || ('guardrail-order-' + (challengeId || payload.data?.ticker || 'single'));

  const notificationOptions = {
    body: notificationBody,
    icon: 'https://www.gstatic.com/mobilesdk/160503_mobilesdk/logo/2x/firebase_28.png',
    tag: notificationTag,
    renotify: false,
    data: {
      url: consentUrl,
      consentUrl: consentUrl,
      challengeId: challengeId,
      ...(payload.data || {})
    },
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Manipulador para o clique na notificação
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notificação clicada:', event.notification);
  event.notification.close();

  const data = event.notification.data || {};
  let challengeId = data.challengeId;
  const rawUrl = data.url || data.consentUrl;

  // Extrai challengeId via query params ou regex se não estiver diretamente presente
  if (!challengeId && rawUrl) {
    try {
      const parsed = new URL(rawUrl, self.location.origin);
      challengeId = parsed.searchParams.get('challengeId');
    } catch (e) {
      const match = String(rawUrl).match(/[?&]challengeId=([^&#]+)/);
      if (match) challengeId = decodeURIComponent(match[1]);
    }
  }

  let targetUrl;
  if (challengeId) {
    targetUrl = new URL(`/consent.html?challengeId=${encodeURIComponent(challengeId)}`, self.location.origin).href;
  } else if (rawUrl) {
    try {
      const parsed = new URL(rawUrl, self.location.origin);
      targetUrl = new URL(parsed.pathname + parsed.search, self.location.origin).href;
    } catch (e) {
      targetUrl = new URL(rawUrl, self.location.origin).href;
    }
  } else {
    targetUrl = new URL('/consent.html', self.location.origin).href;
  }

  if (targetUrl) {
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
        // Se uma aba de consentimento já estiver aberta, navega e foca nela
        for (const client of windowClients) {
          if (client.url && client.url.includes('/consent.html') && 'focus' in client) {
            client.focus();
            if ('navigate' in client) {
              return client.navigate(targetUrl);
            }
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
    );
  } else {
    console.warn("[SW] URL de consentimento não localizada no clique.");
  }
});

