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

def send_push_notification(client_name: str, order: dict, consent_url: str, challenge_id: str = None) -> bool:
    if not firebase_admin._apps:
        print("[NOTIFIER - SIMULAÇÃO] SDK não inicializado.")
        return True

    try:
        ticker = order.get("ticker", "ORDEM")
        action = order.get("action", "BUY")
        total_cost = float(order.get("total_cost", 0.0))
        tag = f"guardrail-order-{challenge_id or ticker}"

        # Padrão Data-Only (FCM Web): NÃO envia o bloco 'notification' nem 'webpush.notification'.
        # Isso impede que o navegador/Chromium dispare uma notificação automática paralela no Windows,
        # garantindo que o Service Worker seja o único responsável por exibir o Toast (1 ordem = 1 notificação).
        message = messaging.Message(
            data={
                "title": "🚨 GuardrailAI - Autorização de Ordem",
                "body": f"Nova ordem de {action} para {ticker} (R$ {total_cost:.2f})",
                "consentUrl": str(consent_url),
                "challengeId": str(challenge_id or ""),
                "ticker": str(ticker),
                "action": str(action),
                "total_cost": f"{total_cost:.2f}",
                "tag": str(tag),
            },
            token=TARGET_DEVICE_TOKEN,
        )
        response = messaging.send(message)
        print(f"📲 [NOTIFIER] Push FCM Data-Only enviado! Message ID: {response}")
        return True
    except Exception as e:
        print(f"❌ [NOTIFIER] Falha ao enviar Push: {e}")
        return False

