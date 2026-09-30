import urllib.parse
import feedparser
from typing import List

# Mapeamento para busca semântica em notícias
TICKER_NAME_MAP = {
    "PETR4.SA": "Petrobras",
    "VALE3.SA": "Vale",
    "ITUB4.SA": "Itaú Unibanco",
    "BBDC4.SA": "Bradesco",
    "BBAS3.SA": "Banco do Brasil"
}


def get_stock_news(ticker: str, max_items: int = 2) -> List[str]:
    """
    Busca as últimas notícias financeiras de um ticker da B3 via RSS do Google News.
    """
    company_name = TICKER_NAME_MAP.get(ticker, ticker.replace(".SA", ""))
    query = f"{company_name} acoes OR mercado"
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    try:
        feed = feedparser.parse(rss_url)
        news_titles = []

        for entry in feed.entries[:max_items]:
            title = entry.title
            # Limpa o sufixo da fonte da notícia (ex: " - InfoMoney")
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            news_titles.append(title.strip())

        return news_titles if news_titles else ["Nenhuma notícia recente encontrada."]
    except Exception as e:
        return [f"Erro ao buscar notícias: {str(e)}"]


if __name__ == "__main__":
    ticker_teste = "PETR4.SA"
    print(f"📰 Testando parser de notícias para {ticker_teste}:")
    manchetes = get_stock_news(ticker_teste)
    for i, m in enumerate(manchetes, 1):
        print(f"  {i}. {m}")
