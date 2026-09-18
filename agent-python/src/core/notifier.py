"""
Módulo de Notificação - GuardrailAI
Responsável pelo envio de links de consentimento biométrico via WhatsApp / Mensageria.
"""
import os
import json
import logging
import requests

logger = logging.getLogger("GuardrailAI.Notifier")

# Configurações de Gateway WhatsApp (ex: Twilio / Z-API / Evolution API)
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")


def format_consent_message(client_name: str, order: dict, consent_url: str, ttl_seconds: int = 120) -> str:
    """Monta a mensagem formatada para envio no WhatsApp."""
    return (
        f"🚨 *GuardrailAI - Autorização de Ordem*\n\n"
        f"Olá, *{client_name}*!\n"
        f"Uma nova recomendação de investimento foi aprovada pelos nossos guardrails de segurança:\n\n"
        f"• *Ativo:* `{order.get('ticker')}`\n"
        f"• *Ação:* *{order.get('action', 'BUY')}*\n"
        f"• *Quantidade:* {order.get('quantity')} cotas\n"
        f"• *Preço Estimado:* R$ {order.get('unit_price', order.get('estimated_price', 0.0)):.2f}\n"
        f"• *Valor Total:* R$ {order.get('total_cost', order.get('total_amount', 0.0)):.2f}\n"
        f"• *Stop Loss:* R$ {order.get('stop_loss_price', 0.0):.2f}\n"
        f"• *Tempo Limite:* {ttl_seconds} segundos\n\n"
        f"🔒 *Para autorizar via Biometria / Passkey, toque no link:*\n"
        f"{consent_url}\n\n"
        f"_Caso você não reconheça esta operação, ignore esta mensagem._"
    )


def send_whatsapp_notification(phone: str, client_name: str, order: dict, consent_url: str) -> bool:
    """
    Envia a notificação via WhatsApp. Se não houver token configurado,
    imprime no log e simula o envio com sucesso.
    """
    message = format_consent_message(client_name, order, consent_url)

    if not WHATSAPP_API_URL or not WHATSAPP_API_TOKEN:
        logger.info(
            f"\n{'='*60}\n"
            f"[NOTIFIER - SIMULAÇÃO WHATSAPP] Para: {phone}\n"
            f"{message}\n"
            f"{'='*60}"
        )
        return True

    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "number": phone,
            "message": message
        }
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            logger.info(f"[NOTIFIER] WhatsApp enviado com sucesso para {phone}")
            return True
        else:
            logger.error(f"[NOTIFIER] Falha ao enviar WhatsApp: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"[NOTIFIER] Erro de conexão com gateway WhatsApp: {e}")
        return False
