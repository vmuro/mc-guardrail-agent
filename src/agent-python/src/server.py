import os
import sys
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

# Garante que a raiz do repositório esteja no PYTHONPATH
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.core.evaluator import evaluate_client_portfolio

app = FastAPI(
    title="GuardrailAI - Agent Python API",
    description="API de Avaliação de Portfólio e Ordens B3 com Governança Determinística",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderItemModel(BaseModel):
    ticker: str
    action: str = "BUY"
    quantity: Optional[int] = 0
    unit_price: Optional[float] = Field(None, alias="unitPrice")
    total_cost: Optional[float] = Field(None, alias="totalCost")
    stop_loss_price: Optional[float] = Field(None, alias="stopLossPrice")
    rationale: Optional[str] = "Ordem proposta para auditoria."

    model_config = ConfigDict(populate_by_name=True)


class EvaluationRequestModel(BaseModel):
    client_id: str = Field(..., alias="clientId")
    budget: float
    risk_profile: str = Field("MODERATE", alias="riskProfile")
    watchlist: Optional[List[str]] = Field(default_factory=list)
    orders: Optional[List[OrderItemModel]] = None
    client_name: Optional[str] = Field(None, alias="clientName")
    segment: Optional[str] = "Varejo"
    device_token: Optional[str] = Field(None, alias="deviceToken")

    model_config = ConfigDict(populate_by_name=True)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "UP", "service": "guardrail-agent-python"}


@app.post("/api/evaluate", tags=["Evaluation"])
def evaluate_orders(request: EvaluationRequestModel) -> Dict[str, Any]:
    """
    Avalia a carteira/ordens do investidor.
    Suporta:
      - Modo Autônomo com IA: Quando 'orders' estiver vazio, avalia a 'watchlist' usando Gemini + Screener B3.
      - Modo Auditoria Direta: Quando 'orders' for informado, audita deterministicamente as ordens especificadas.
    """
    try:
        custom_orders_payload = None
        if request.orders:
            custom_orders_payload = [
                {
                    "ticker": o.ticker.strip().upper(),
                    "action": o.action.strip().upper(),
                    "quantity": o.quantity,
                    "unit_price": o.unit_price,
                    "total_cost": o.total_cost,
                    "stop_loss_price": o.stop_loss_price,
                    "rationale": o.rationale
                }
                for o in request.orders
            ]

        result = evaluate_client_portfolio(
            client_id=request.client_id,
            budget=request.budget,
            risk_profile=request.risk_profile,
            watchlist=request.watchlist,
            custom_orders=custom_orders_payload,
            client_name=request.client_name,
            segment=request.segment,
            send_notifications=True,
            device_token=request.device_token
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar avaliação de portfólio: {str(e)}"
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("src.server:app", host="0.0.0.0", port=port, reload=False)
