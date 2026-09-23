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
  const consentUrl = payload.data?.consentUrl || payload.data?.url;
  const notificationTag = payload.data?.tag || ('guardrail-order-' + (payload.data?.challengeId || payload.data?.ticker || 'single'));

  const notificationOptions = {
    body: notificationBody,
    icon: 'https://www.gstatic.com/mobilesdk/160503_mobilesdk/logo/2x/firebase_28.png',
    tag: notificationTag,
    renotify: false,
    data: { url: consentUrl },
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Manipulador para o clique na notificação
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notificação clicada:', event.notification);
  event.notification.close();

  const data = event.notification.data || {};
  let targetUrl = data.url || data.consentUrl;
  if (data.challengeId) {
    targetUrl = new URL(`/consent.html?challengeId=${data.challengeId}`, self.location.origin).href;
  }

  if (targetUrl) {
    event.waitUntil(clients.openWindow(targetUrl));
  } else {
    console.warn("[SW] URL de consentimento não localizada no clique.");
  }
});

