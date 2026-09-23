# agent-python/src/core/notifier.py
import os
import firebase_admin
from firebase_admin import credentials, messaging

FCM_CREDS_PATH = os.getenv("FCM_CREDS_PATH", "/app/config/fcm-service-account.json")
if not os.path.exists(FCM_CREDS_PATH):
    FCM_CREDS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config",
        "fcm-service-account.json"
    )

TARGET_DEVICE_TOKEN = os.getenv(
    "TARGET_DEVICE_TOKEN",
    "eixTwBdIMVZtlQXEEn9g3D:APA91bFrT63niRg9pxqQOYJ5RyLC7JzVDK9a2WAocIjcRlknUZPWYMCt8prPmbrYo2wIJ-39FDoUnevcRIqrAhMX-pMPO_w-2nsCcR1YtqI0Y_7qTJeJocY"
)

def _init_firebase():
    if not firebase_admin._apps and os.path.exists(FCM_CREDS_PATH):
        try:
            cred = credentials.Certificate(FCM_CREDS_PATH)
            firebase_admin.initialize_app(cred)
            print(f"✅ [NOTIFIER] Firebase Admin SDK inicializado a partir de {FCM_CREDS_PATH}.")
        except Exception as e:
            print(f"❌ [NOTIFIER] ERRO ao inicializar Firebase: {e}")

_init_firebase()

def send_push_notification(client_name: str, order: dict, consent_url: str, challenge_id: str = None, device_token: str = None) -> bool:
    _init_firebase()
    if not firebase_admin._apps:
        print("[NOTIFIER - SIMULAÇÃO] SDK não inicializado.")
        return True

    target_token = device_token or TARGET_DEVICE_TOKEN
    if not target_token:
        print("[NOTIFIER] Nenhum token FCM disponível para envio.")
        return False

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
            token=target_token,
        )
        response = messaging.send(message)
        print(f"📲 [NOTIFIER] Push FCM Data-Only enviado para {target_token[:15]}...! Message ID: {response}")
        return True
    except Exception as e:
        print(f"❌ [NOTIFIER] Falha ao enviar Push: {e}")
        return False


