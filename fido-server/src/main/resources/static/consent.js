// fido-server/src/main/resources/static/consent.js

const firebaseConfig = {
    apiKey: "AIzaSyClcgX40Hs5fTGV57PY4JGRY78NJ6tFCco",
    authDomain: "guardrail-notifier-mvp.firebaseapp.com",
    projectId: "guardrail-notifier-mvp",
    storageBucket: "guardrail-notifier-mvp.firebasestorage.app",
    messagingSenderId: "376986876849",
    appId: "1:376986876849:web:57487778033c282ebf1b90",
    measurementId: "G-EHHM4NNF1J"
};

const VAPID_KEY = "BDhpWazjkTyFCMYUZgh9ADUjDrONHvu0AygG_BItHL7mRT8l_ErFaITgF6yrPeCm0jzrREVDrIWL9sKomWUXmEk";

// ==========================================
// 1. INICIALIZAÇÃO DO FIREBASE & SERVICE WORKER
// ==========================================
if (typeof firebase !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/firebase-messaging-sw.js')
            .then(async (registration) => {
                console.log('✅ Service Worker registrado:', registration);
                const readyRegistration = await navigator.serviceWorker.ready;

                const permission = await Notification.requestPermission();
                if (permission === 'granted') {
                    try {
                        const token = await messaging.getToken({
                            serviceWorkerRegistration: readyRegistration,
                            vapidKey: VAPID_KEY
                        });
                        if (token) {
                            console.log('🔑 TOKEN FCM:\n', token);
                            localStorage.setItem('fcm_token', token);
                        }
                    } catch (tokenErr) {
                        console.error('❌ Erro Token FCM:', tokenErr);
                    }
                }
            })
            .catch((err) => console.error('❌ Erro Service Worker:', err));
    }

    messaging.onMessage((payload) => {
        console.log('📩 Notificação em primeiro plano:', payload);
        const title = payload.notification ? payload.notification.title : "GuardrailAI";
        const body = payload.notification ? payload.notification.body : "Nova recomendação disponível.";
        new Notification(title, { body: body });
    });
}

// ==========================================
// 2. CARREGAMENTO DOS DETALHES DA ORDEM
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const challengeId = urlParams.get("challengeId");

    if (!challengeId) {
        // Se não há challengeId, a página fica em modo "ouvinte" de notificações
        document.getElementById("order-details").innerHTML = "<p>Aguardando novas recomendações via notificação push...</p>";
        document.getElementById("signBtn").disabled = true;
        return;
    }

    console.log("🔍 Carregando detalhes do desafio:", challengeId);
    loadOrderDetails(challengeId);
});

async function loadOrderDetails(challengeId) {
    try {
        const response = await fetch(`/api/consent/status/${challengeId}`);
        if (!response.ok) {
            throw new Error(`Falha na API: ${response.status}`);
        }
        const data = await response.json();
        console.log("📦 Dados da ordem recebidos:", data);

        // O 'canonicalPayload' vem como uma string JSON, precisamos parseá-la
        const payload = JSON.parse(data.canonicalPayload);

        const detailsDiv = document.getElementById("order-details");

        // Formata os dados para exibição
        const htmlContent = `
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; border: 1px solid #00E676; text-align: left; font-family: monospace; word-wrap: break-word;">
                <p><strong>👤 Cliente:</strong> ${data.clientId || 'N/A'}</p>
                <p><strong>📈 Ativo:</strong> ${payload.ticker || 'N/A'}</p>
                <p><strong>🎯 Ação:</strong> <span style="color: #00E676; font-weight: bold;">${payload.action || 'N/A'}</span></p>
                <p><strong>🔢 Quantidade:</strong> ${payload.quantity || '0'}</p>
                <p><strong>💵 Preço Unit.:</strong> R$ ${(payload.unit_price || payload.unitPrice || 0).toFixed(2)}</p>
                <p><strong>🛡️ Stop-Loss:</strong> R$ ${(payload.stop_loss_price || payload.stopLossPrice || 0).toFixed(2)}</p>
                <p><strong>💰 Total Estimado:</strong> R$ ${(payload.total_cost || payload.totalCost || 0).toFixed(2)}</p>
                <p style="margin-top: 10px; font-size: 0.85em; color: #bbb;"><strong>📝 Rationale:</strong> ${payload.rationale || 'N/A'}</p>
            </div>
        `;

        detailsDiv.innerHTML = htmlContent;

        // Habilita o botão para assinatura
        const signButton = document.getElementById("signBtn");
        signButton.disabled = false;
        // Adiciona o evento de clique para iniciar a autenticação WebAuthn
        signButton.onclick = () => performBiometricAuth(challengeId, data.userHandle);

    } catch (err) {
        console.error("❌ Erro ao renderizar detalhes da ordem:", err);
        document.getElementById("order-details").innerHTML = `<p style="color: #FF5252;">❌ Erro ao carregar ordem: ${err.message}</p>`;
    }
}

// Função placeholder para a assinatura FIDO2/WebAuthn
async function performBiometricAuth(challengeId, userHandle) {
    alert(`Iniciando assinatura biométrica para o desafio ${challengeId} e usuário ${userHandle}...`);
    // Aqui viria a lógica real do WebAuthn:
    // 1. Chamar um endpoint no backend Java para obter as opções de assinatura (getAssertion)
    // 2. Usar navigator.credentials.get(...) para solicitar a biometria
    // 3. Enviar o resultado da assinatura para o backend Java para verificação
    console.log("Desafio:", challengeId);
    console.log("User Handle:", userHandle);
}


async function performBiometricAuth(challengeId, payload) {
    alert(`🔐 Simulando assinatura biométrica FIDO2 para o desafio: ${challengeId}`);
    // Aqui integra com o WebAuthn real ou conclui o desafio no backend
}
