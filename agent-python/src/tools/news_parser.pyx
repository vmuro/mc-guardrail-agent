import feedparser
import urllib.parse

# Mapeamento para termos de busca mais abrangentes
TICKER_MAP = {
    "PETR4": "Petrobras",
    "VALE3": "Vale",
    "ITUB4": "Itaú Unibanco",
    "BBAS3": "Banco do Brasil",
}

def fetch_rss(query: str, limit: int):
    """Auxiliar para buscar e formatar as entradas do RSS."""
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    feed = feedparser.parse(rss_url)
    articles = []
    
    for entry in getattr(feed, "entries", [])[:limit]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": getattr(entry, "published", "Data não disponível")
        })
    return articles

def get_market_news(ticker: str, limit: int = 3):
    """
    Busca notícias recentes com fallback para nome fantasia da empresa.
    """
    clean_ticker = ticker.replace(".SA", "").upper()
    
    # 1ª Tentativa: Código do ativo + ações
    articles = fetch_rss(f"{clean_ticker} ações B3", limit)
    
    # 2ª Tentativa (Fallback): Nome da empresa se lista vier vazia
    if not articles and clean_ticker in TICKER_MAP:
        company_name = TICKER_MAP[clean_ticker]
        articles = fetch_rss(f"{company_name} mercado financeiro", limit)
        
    return articles

if __name__ == "__main__":
    ativos = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBAS3.SA"]
    for ativo in ativos:
        noticias = get_market_news(ativo, limit=2)
        print(f"\n--- {ativo} ({len(noticias)} notícias encontradas) ---")
        if noticias:
            for item in noticias:
                print(f"• {item['title']}")
        else:
            print("• Nenhuma notícia relevante no momento (Sentimento Neutro).")
