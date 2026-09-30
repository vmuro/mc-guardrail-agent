# 📊 Dados Sintéticos e de Demonstração (Mock) — GuardrailAI
## Desafio de Agentes de IA · Mercado de Capitais (GFT × Google · SMC26)

> ⚠️ **CONFORMIDADE E PRIVACIDADE:**
> Todos os dados contidos neste diretório são **100% fictícios, públicos ou sintéticos**. Em conformidade com o regulamento do desafio, **não há dados reais, confidenciais ou sensíveis de clientes ou instituições financeiras**.

---

### 📁 Arquivos Disponíveis

#### 1. `clients.json`
Perfis sintéticos de investidores para simulação dos 3 perfis de risco suportados pelo motor de governança:

| Client ID | Perfil de Risco | Orçamento Simulado | Teto de Concentração | Finalidade |
|---|---|---|---|---|
| `CLI-001` | `CONSERVATIVE` | R$ 5.000,00 | 20% do orçamento | Testes de alocação conservadora |
| `CLI-002` | `MODERATE` | R$ 10.000,00 | 35% do orçamento | Testes de rebalanceamento balanceado |
| `CLI-003` | `AGGRESSIVE` | R$ 20.000,00 | 50% do orçamento | Testes de momentum e alta exposição |

---

### 🌐 Origem das Cotações de Mercado
- **Ativos da B3:** Cotações públicas históricas e em tempo real (via Yahoo Finance API / B3 pública) para os tickers líquidos: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`, `BBDC4.SA`, `WEGE3.SA`, etc.
- **Notícias de Mercado:** Feeds RSS abertos e públicos do Google News Brasil sobre finanças e mercado de ações.
