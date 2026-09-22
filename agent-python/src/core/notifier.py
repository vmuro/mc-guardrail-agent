# agent-python/src/core/notifier.py
import os
import firebase_admin
from firebase_admin import credentials, messaging

FCM_CREDS_PATH = "/home/ubuntu/repo/mc-guardrail-agent/agent-python/config/fcm-service-account.json"
# Certifique-se que este é o token mais recente gerado no console do seu navegador
TARGET_DEVICE_TOKEN = "eixTwBdIMVZtlQXEEn9g3D:APA91bFrT63niRg9pxqQOYJ5RyLC7JzVDK9a2WAocIjcRlknUZPWYMCt8prPmbrYo2wIJ-39FDoUnevcRIqrAhMX-pMPO_w-2nsCcR1YtqI0Y_7qTJeJocY"

try:
    if os.path.exists(FCM_CREDS_PATH) and not firebase_admin._apps:
        cred = credentials.Certificate(FCM_CREDS_PATH)
        firebase_admin.initialize_app(cred)
        print(f"✅ [NOTIFIER] Firebase Admin SDK inicializado.")
except Exception as e:
    print(f"❌ [NOTIFIER] ERRO ao inicializar Firebase: {e}")

def send_push_notification(client_name: str, order: dict, consent_url: str) -> bool:
    if not firebase_admin._apps:
        print("[NOTIFIER - SIMULAÇÃO] SDK não inicializado.")
        return True

    try:
        ticker = order.get("ticker", "ORDEM")
        action = order.get("action", "BUY")
        total_cost = order.get("total_cost", 0.0)
        tag = f"guardrail-{ticker}-{action}"

        # WebpushConfig: link só é permitido pelo SDK Firebase se for HTTPS (ex: ngrok ou prod).
        # Para http://localhost, a URL é transmitida no payload 'data' e tratada pelo Service Worker.
        fcm_options = messaging.WebpushFCMOptions(link=consent_url) if consent_url.startswith("https://") else None
        webpush_config = messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                tag=tag
            ),
            fcm_options=fcm_options
        ) if fcm_options else messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                tag=tag
            )
        )

        # Monta a mensagem com WebpushConfig e tag para impedir duplicidade no navegador
        message = messaging.Message(
            notification=messaging.Notification(
                title="🚨 GuardrailAI - Autorização de Ordem",
                body=f"Nova ordem de {action} para {ticker} (R$ {total_cost:.2f})",
            ),
            data={
                "consentUrl": consent_url,
                "ticker": str(ticker),
                "action": str(action),
                "total_cost": str(total_cost)
            },
            webpush=webpush_config,
            token=TARGET_DEVICE_TOKEN,
        )
        response = messaging.send(message)
        print(f"📲 [NOTIFIER] Push FCM enviado! Message ID: {response}")
        return True
    except Exception as e:
        print(f"❌ [NOTIFIER] Falha ao enviar Push: {e}")
        return False
