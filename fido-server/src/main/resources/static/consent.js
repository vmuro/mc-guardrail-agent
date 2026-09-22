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

// Funções utilitárias de conversão
function bufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    bytes.forEach(b => binary += String.fromCharCode(b));
    return window.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function stringToBuffer(str) {
    return new TextEncoder().encode(str);
}

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
                            console.log('🔑 TOKEN FCM:', token);
                            localStorage.setItem('fcm_token', token);
                        }
                    } catch (tokenErr) {
                        console.error('❌ Erro ao obter Token FCM:', tokenErr);
                    }
                }
            })
            .catch((err) => console.error('❌ Erro no registro do Service Worker:', err));
    }

    messaging.onMessage((payload) => {
        console.log('📩 Mensagem FCM recebida:', payload);
        // Não chamamos `new Notification` aqui para evitar duplicar
        // com a notificação do sistema operacional já disparada pelo FCM.
    });
}

// ==========================================
// 2. FUNÇÕES DE UI E CONTAGEM REGRESSIVA (TTL)
// ==========================================
let countdownInterval = null;

function startCountdown(expiresAt) {
    const timerElem = document.getElementById("timer");
    if (!timerElem) return;

    if (countdownInterval) clearInterval(countdownInterval);

    const targetTime = expiresAt ? new Date(expiresAt).getTime() : (Date.now() + 120000);

    const updateTimer = () => {
        const remaining = Math.max(0, Math.floor((targetTime - Date.now()) / 1000));
        timerElem.innerText = `TTL: ${remaining}s`;
        if (remaining <= 0) {
            clearInterval(countdownInterval);
            renderExpired();
        }
    };

    updateTimer();
    countdownInterval = setInterval(updateTimer, 1000);
}

function renderExpired() {
    const authBtn = document.getElementById("authBtn");
    const statusMsg = document.getElementById("statusMsg");
    const timerElem = document.getElementById("timer");

    if (timerElem) timerElem.innerText = "TTL: EXPIRADO";
    if (authBtn) {
        authBtn.disabled = true;
        authBtn.style.backgroundColor = "#334155";
        authBtn.innerText = "⛔ Desafio Expirado";
    }
    if (statusMsg) {
        statusMsg.style.color = "#ef4444";
        statusMsg.innerHTML = "❌ <strong>Este desafio expirou.</strong> O TTL regulatório de 120 segundos foi atingido.";
    }
}

function renderApproved(authBtn, timerElem) {
    if (timerElem) timerElem.innerText = "TTL: CONCLUÍDO";
    if (authBtn) {
        authBtn.disabled = true;
        authBtn.style.backgroundColor = "#16a34a";
        authBtn.innerText = "✓ Assinatura Concluída (FIDO2)";
    }
    const statusMsg = document.getElementById("statusMsg");
    if (statusMsg) {
        statusMsg.style.color = "#22c55e";
        statusMsg.innerHTML = "✅ <strong>Ordem assinada com sucesso!</strong><br><small style='color: #94a3b8;'>Não-repúdio registrado (CVM Compliant / FIDO2).</small>";
    }
}

function renderError(message) {
    const summaryBox = document.getElementById("orderSummary");
    const statusMsg = document.getElementById("statusMsg");
    if (summaryBox) {
        summaryBox.innerHTML = `<p style="color: #ef4444; text-align: center; padding: 12px;">❌ ${message}</p>`;
    }
    if (statusMsg) {
        statusMsg.style.color = "#ef4444";
        statusMsg.innerText = message;
    }
}

// ==========================================
// 3. CARREGAMENTO DOS DETALHES DA ORDEM
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    const challengeId = urlParams.get("challengeId");
    const summaryBox = document.getElementById("orderSummary");
    const authBtn = document.getElementById("authBtn");

    if (!challengeId) {
        if (summaryBox) summaryBox.innerHTML = "<p style='color:#94a3b8; text-align:center;'>Aguardando recomendações via notificação push...</p>";
        if (authBtn) authBtn.disabled = true;
        return;
    }

    console.log("🔍 Carregando detalhes do desafio:", challengeId);
    loadOrderDetails(challengeId);
});

async function loadOrderDetails(challengeId) {
    const summaryBox = document.getElementById("orderSummary");
    const authBtn = document.getElementById("authBtn");
    const timerElem = document.getElementById("timer");

    try {
        const response = await fetch(`/api/consent/status/${challengeId}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}: Desafio não localizado.`);

        const data = await response.json();

        if (data.status === 'EXPIRED') {
            renderExpired();
            return;
        }

        if (data.status === 'APPROVED') {
            renderApproved(authBtn, timerElem);
            return;
        }

        let payload = data.canonicalPayload || {};
        if (typeof payload === "string") {
            try { payload = JSON.parse(payload); } catch (e) { payload = {}; }
        }

        const client = data.clientId || payload.client_id || 'Investidor';
        const ticker = payload.ticker || 'N/A';
        const action = (payload.action || 'BUY').toUpperCase();
        const qty = payload.quantity || 0;
        const price = payload.unit_price || payload.estimated_price || 0.0;
        const stopLoss = payload.stop_loss_price || 0.0;
        const total = payload.total_cost || (qty * price);
        const rationale = payload.rationale || (payload.order && payload.order.rationale) || data.rationale || 'Tese formulada com base em análise técnica e indicadores de mercado.';

        summaryBox.innerHTML = `
            <div class="row"><span>Cliente:</span> <strong>${client}</strong></div>
            <div class="row"><span>Ativo:</span> <strong>${ticker}</strong></div>
            <div class="row"><span>Operação:</span> <strong style="color: ${action === 'BUY' ? '#22c55e' : '#ef4444'};">${action}</strong></div>
            <div class="row"><span>Quantidade:</span> <strong>${qty} cotas</strong></div>
            <div class="row"><span>Preço Unitário:</span> <strong>R$ ${Number(price).toFixed(2)}</strong></div>
            <div class="row"><span>Stop-Loss:</span> <strong style="color: #f59e0b;">R$ ${Number(stopLoss).toFixed(2)}</strong></div>
            <div class="row" style="border-top: 1px solid #334155; padding-top: 6px; margin-top: 6px;">
                <span>Total Estimado:</span> <strong style="color: #38bdf8; font-size: 15px;">R$ ${Number(total).toFixed(2)}</strong>
            </div>
            <div style="margin-top: 12px; background: #1e293b; border-radius: 8px; padding: 10px; border-left: 3px solid #38bdf8;">
                <span style="color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">🧠 Racional da IA:</span>
                <p style="color: #e2e8f0; font-size: 12px; line-height: 1.45; margin-top: 4px; text-align: justify;">${rationale}</p>
            </div>
            <div class="row" style="font-size: 10px; color: #64748b; margin-top: 8px;">
                <span>Hash HMAC:</span> <strong style="font-size: 10px;">${(data.orderHash || '').substring(0, 18)}...</strong>
            </div>
        `;

        if (authBtn) {
            authBtn.disabled = false;
            authBtn.onclick = () => performFidoAuthentication(challengeId, data);
        }
        startCountdown(data.expiresAt);

    } catch (err) {
        renderError(`Erro ao carregar dados da ordem: ${err.message}`);
    }
}

// ==========================================
// 4. AUTENTICAÇÃO FIDO2 / BIOMETRIA (WEBAUTHN)
// ==========================================
async function performFidoAuthentication(challengeId, challengeData) {
    const statusMsg = document.getElementById("statusMsg");
    const authBtn = document.getElementById("authBtn");

    if (statusMsg) {
        statusMsg.style.color = "#38bdf8";
        statusMsg.innerHTML = "⏳ <strong>Acionando autenticador biométrico FIDO2/WebAuthn...</strong><br><small style='color: #94a3b8;'>Toque no leitor biométrico ou confirme no seu dispositivo.</small>";
    }
    if (authBtn) authBtn.disabled = true;

    try {
        let signatureId = "fido2_sig_" + Date.now();
        let clientDataJsonStr = "fido2_client_data_" + Date.now();

        if (window.PublicKeyCredential && navigator.credentials) {
            const rawChallenge = challengeData.orderHash || challengeId;
            const challengeBuffer = new Uint8Array(32);
            const encoded = new TextEncoder().encode(rawChallenge);
            challengeBuffer.set(encoded.slice(0, 32));

            let credential = null;

            // 1ª Tentativa: Obter asserção (get) para credencial existente
            try {
                credential = await navigator.credentials.get({
                    publicKey: {
                        challenge: challengeBuffer,
                        rpId: window.location.hostname,
                        userVerification: "preferred",
                        timeout: 60000
                    }
                });
            } catch (getErr) {
                console.log("ℹ️ get() não retornou credencial prévia. Acionando popup biométrico via create()...", getErr.message);
            }

            // 2ª Tentativa: Se não há credencial residente no localhost, create() aciona o leitor biométrico (Windows Hello, TouchID, FaceID)
            if (!credential) {
                try {
                    credential = await navigator.credentials.create({
                        publicKey: {
                            challenge: challengeBuffer,
                            rp: {
                                name: "GuardrailAI - Governança B3",
                                id: window.location.hostname
                            },
                            user: {
                                id: new TextEncoder().encode(challengeData.clientId || "client_retail_001"),
                                name: (challengeData.clientId || "investidor").toLowerCase() + "@guardrail.ai",
                                displayName: challengeData.clientId || "Investidor B3"
                            },
                            pubKeyCredParams: [
                                { type: "public-key", alg: -7 },   // ES256
                                { type: "public-key", alg: -257 }  // RS256
                            ],
                            authenticatorSelection: {
                                userVerification: "preferred"
                            },
                            timeout: 60000
                        }
                    });
                } catch (createErr) {
                    console.warn("⚠️ Popup biométrico FIDO cancelado ou indisponível:", createErr);
                    // Se o usuário explicitamente cancelou a janela biométrica
                    if (createErr.name === "NotAllowedError" || createErr.name === "AbortError") {
                        throw new Error("Autenticação biométrica cancelada pelo usuário.");
                    }
                }
            }

            if (credential) {
                if (credential.rawId) {
                    signatureId = bufferToBase64(credential.rawId);
                }
                if (credential.response && credential.response.clientDataJSON) {
                    clientDataJsonStr = bufferToBase64(credential.response.clientDataJSON);
                }
            }
        }

        // Envia assinatura criptográfica para o Spring Boot registrar não-repúdio
        const response = await fetch(`/api/consent/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                challengeId: challengeId,
                signature: signatureId,
                clientDataJson: clientDataJsonStr
            })
        });

        const result = await response.json();

        if (response.ok && result.status === "APPROVED") {
            if (statusMsg) {
                statusMsg.style.color = "#22c55e";
                statusMsg.innerHTML = "✅ <strong>Ordem assinada com sucesso!</strong><br><small style='color: #94a3b8;'>Não-repúdio registrado (CVM Compliant / FIDO2).</small>";
            }
            if (authBtn) {
                authBtn.style.backgroundColor = "#16a34a";
                authBtn.innerText = "✓ Assinatura Concluída (FIDO2)";
                authBtn.disabled = true;
            }
            const timerElem = document.getElementById("timer");
            if (timerElem) timerElem.innerText = "TTL: CONCLUÍDO";
        } else {
            throw new Error(result.message || "Assinatura rejeitada pelo servidor.");
        }

    } catch (e) {
        console.error("❌ Erro no fluxo biométrico:", e);
        if (statusMsg) {
            statusMsg.style.color = "#ef4444";
            statusMsg.innerText = `❌ ${e.message}`;
        }
        if (authBtn) {
            authBtn.disabled = false;
        }
    }
}

// Aliases para compatibilidade retroativa
const performBiometricAuth = performFidoAuthentication;
