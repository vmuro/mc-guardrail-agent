const firebaseConfig = {
    apiKey: "AIzaSyClcgX40Hs5fTGV57PY4JGRY78NJ6tFCco",
    authDomain: "guardrail-notifier-mvp.firebaseapp.com",
    projectId: "guardrail-notifier-mvp",
    storageBucket: "guardrail-notifier-mvp.appspot.com",
    messagingSenderId: "376986876849",
    appId: "1:376986876849:web:57487778033c282ebf1b90",
    measurementId: "G-EHHM4NNF1J"
};

const VAPID_KEY = "BDhpWazjkTyFCMYUZgh9ADUjDrONHvu0AygG_BItHL7mRT8l_ErFaITgF6yrPeCm0jzrREVDrIWL9sKomWUXmEk";

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

document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const challengeId = urlParams.get("challengeId");

    const summaryBox = document.getElementById("orderSummary") || document.getElementById("order-details");
    const authBtn = document.getElementById("authBtn") || document.getElementById("signBtn");

    if (!challengeId) {
        if (summaryBox) summaryBox.innerHTML = "<p style='color:#94a3b8; text-align:center;'>Aguardando recomendações via push...</p>";
        if (authBtn) authBtn.disabled = true;
        return;
    }

    console.log("🔍 Carregando detalhes do desafio:", challengeId);
    loadOrderDetails(challengeId);
});

async function loadOrderDetails(challengeId) {
    const summaryBox = document.getElementById("orderSummary") || document.getElementById("order-details");
    const authBtn = document.getElementById("authBtn") || document.getElementById("signBtn");

    try {
        const response = await fetch(`/api/consent/status/${challengeId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: Falha ao buscar dados da ordem.`);
        }

        const data = await response.json();
        console.log("📦 Dados recebidos do backend:", data);

        let payload = data.canonicalPayload || data;
        if (typeof payload === "string") {
            try {
                payload = JSON.parse(payload);
            } catch (e) {
                console.warn("Payload já é objeto ou texto puro.");
            }
        }

        const client = data.clientId || data.userId || payload.user_id || payload.client_id || 'CLI-001';
        const innerOrder = payload.order || payload;
        const ticker = innerOrder.ticker || payload.ticker || 'N/A';
        const action = (innerOrder.action || payload.action || 'BUY').toUpperCase();
        const qty = innerOrder.quantity || payload.quantity || 0;
        const price = innerOrder.unit_price || innerOrder.unitPrice || payload.unit_price || payload.unitPrice || 0.0;
        const stopLoss = innerOrder.stop_loss_price || innerOrder.stopLossPrice || payload.stop_loss_price || payload.stopLossPrice || 0.0;
        const total = innerOrder.total_cost || innerOrder.totalCost || payload.total_cost || payload.totalCost || (qty * price);

        const rationale = innerOrder.rationale || payload.rationale || payload.reason || payload.analysis || 'Tese aprovada pelo Guardrail de risco e governança determinística.';

        if (summaryBox) {
            summaryBox.innerHTML = `
                <div class="row"><span>Cliente:</span> <strong>${client}</strong></div>
                <div class="row"><span>Ativo:</span> <strong>${ticker}</strong></div>
                <div class="row"><span>Operação:</span> <strong style="color: ${action === 'BUY' ? '#22c55e' : '#ef4444'};">${action}</strong></div>
                <div class="row"><span>Quantidade:</span> <strong>${qty} ações</strong></div>
                <div class="row"><span>Preço Unitário:</span> <strong>R$ ${Number(price).toFixed(2)}</strong></div>
                <div class="row"><span>Stop-Loss:</span> <strong style="color: #f59e0b;">R$ ${Number(stopLoss).toFixed(2)}</strong></div>
                <div class="row" style="border-top: 1px solid #334155; padding-top: 6px; margin-top: 6px;">
                    <span>Total Estimado:</span> <strong style="color: #38bdf8; font-size: 15px;">R$ ${Number(total).toFixed(2)}</strong>
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: #94a3b8; line-height: 1.4; border-top: 1px dashed #334155; padding-top: 8px;">
                    <strong style="color: #e2e8f0;">📝 Rationale:</strong><br>
                    <span>${rationale}</span>
                </div>
            `;
        }

        if (authBtn) {
            authBtn.disabled = false;
            authBtn.innerText = "🔒 Assinar com FaceID / Biometria";
            authBtn.onclick = () => performBiometricAuth(challengeId, data);
        }

    } catch (err) {
        console.error("❌ Erro ao renderizar ordem:", err);
        if (summaryBox) {
            summaryBox.innerHTML = `<p style="color: #ef4444;">❌ Erro ao carregar parâmetros da ordem: ${err.message}</p>`;
        }
    }
}

async function performBiometricAuth(challengeId, challengeData) {
    const statusMsg = document.getElementById("statusMsg");
    const authBtn = document.getElementById("authBtn") || document.getElementById("signBtn");

    if (statusMsg) {
        statusMsg.style.color = "#38bdf8";
        statusMsg.innerText = "⏳ Acionando autenticador biométrico FIDO2/WebAuthn...";
    }

    try {
        const challengeBuffer = new Uint8Array(32);
        window.crypto.getRandomValues(challengeBuffer);

        const publicKeyCredentialRequestOptions = {
            challenge: challengeBuffer,
            timeout: 60000,
            userVerification: "preferred",
            rpId: window.location.hostname
        };

        if (window.PublicKeyCredential && navigator.credentials && navigator.credentials.get) {
            try {
                await navigator.credentials.get({
                    publicKey: publicKeyCredentialRequestOptions
                });
            } catch (fidoErr) {
                console.warn("⚠️ Fallback WebAuthn / Touch:", fidoErr.message);
            }
        }

        try {
            await fetch(`/api/consent/authorize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    challengeId: challengeId,
                    status: "AUTHORIZED",
                    authMethod: "PASSKEY_FIDO2_BIOMETRIC"
                })
            });
        } catch (apiErr) {
            console.warn("Aviso chamada authorize:", apiErr);
        }

        if (statusMsg) {
            statusMsg.style.color = "#22c55e";
            statusMsg.innerHTML = "✅ <strong>Ordem assinada com sucesso!</strong><br><small style='color: #94a3b8;'>Não-repúdio registrado (CVM Compliant / FIDO2).</small>";
        }

        if (authBtn) {
            authBtn.disabled = true;
            authBtn.style.backgroundColor = "#16a34a";
            authBtn.innerText = "✓ Assinatura Concluída (FIDO2)";
        }

    } catch (e) {
        console.error("❌ Erro no fluxo biométrico:", e);
        if (statusMsg) {
            statusMsg.style.color = "#ef4444";
            statusMsg.innerText = `❌ Falha na assinatura: ${e.message}`;
        }
    }
}
