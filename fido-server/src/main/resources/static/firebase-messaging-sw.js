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

  const notificationTitle = payload.notification?.title || payload.data?.title || "🚨 GuardrailAI - Autorização de Ordem";
  const notificationBody = payload.notification?.body || payload.data?.body || "Nova recomendação disponível para autorização.";
  const consentUrl = payload.data?.consentUrl || payload.data?.url;

  const notificationOptions = {
    body: notificationBody,
    icon: 'https://www.gstatic.com/mobilesdk/160503_mobilesdk/logo/2x/firebase_28.png',
    tag: 'guardrail-order-' + (payload.data?.ticker || 'single'),
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
  const consentUrl = data.url || data.consentUrl;
  if (consentUrl) {
    event.waitUntil(clients.openWindow(consentUrl));
  } else {
    console.warn("[SW] URL de consentimento não localizada no clique.");
  }
});
