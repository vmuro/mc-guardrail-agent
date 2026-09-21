// fido-server/src/main/resources/static/firebase-messaging-sw.js

// Importa os scripts do Firebase (versão compatível)
importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js");

// Cole aqui a configuração do seu projeto Firebase (a mesma do consent.html)
const firebaseConfig = {
  apiKey: "AIzaSyClcgX40Hs5fTGV57PY4JGRY78NJ6tFCco",
  authDomain: "guardrail-notifier-mvp.firebaseapp.com",
  projectId: "guardrail-notifier-mvp",
  storageBucket: "guardrail-notifier-mvp.appspot.com", // Verifique se é .appspot.com
  messagingSenderId: "376986876849",
  appId: "1:376986876849:web:57487778033c282ebf1b90",
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Manipulador para quando a mensagem chega com o app em segundo plano
messaging.onBackgroundMessage((payload) => {
  console.log("[SW] Push em segundo plano recebido:", payload);

  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: 'https://www.gstatic.com/mobilesdk/160503_mobilesdk/logo/2x/firebase_28.png',
    // Guarda a URL de consentimento que veio do Python no campo 'data' da notificação
    data: { url: payload.data.consentUrl },
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Manipulador para o clique na notificação
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notificação clicada:', event.notification);

  // Fecha a notificação que foi clicada
  event.notification.close();

  // Pega a URL que guardamos no 'data' e abre em uma nova janela
  const consentUrl = event.notification.data.url;
  if (consentUrl) {
    event.waitUntil(clients.openWindow(consentUrl));
  } else {
    console.error("[SW] Não foi encontrada URL para abrir no clique da notificação.");
  }
});
