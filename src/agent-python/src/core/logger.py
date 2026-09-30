import json
import logging
from datetime import datetime
from typing import Any, Dict

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("agent_investor")


def log_event(event_type: str, data: Dict[str, Any], severity: str = "INFO") -> None:
    """
    Emite um log estruturado em formato JSON.
    Compatível tanto com execução local quanto com ingestão automática do Cloud Logging no GCP.
    """
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "severity": severity,
        "event_type": event_type,
        "data": data
    }

    # Emite como JSON em linha única no stdout para captura automática no GCP
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    print("📝 Testando emissão de log estruturado:")
    log_event(
        event_type="TEST_EVENT",
        data={"message": "Logger funcionando com sucesso", "status": "OK"},
        severity="INFO"
    )
