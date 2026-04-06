import json
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    )
}

TOOL_MAP = {}


def _coerce_amount(num_results: Any, default: int = 5, max_value: int = 10) -> int:
    try:
        return max(1, min(int(num_results), max_value))
    except (TypeError, ValueError):
        return default


def _extract_ddg_target(link: str) -> str:
    """Converte links de redirecionamento do DuckDuckGo para URL final."""
    parsed = urlparse(link)
    if "duckduckgo.com" not in parsed.netloc:
        return link

    query = parse_qs(parsed.query)
    target = query.get("uddg", [""])[0]
    return unquote(target) if target else link


def _duckduckgo_results(query: str, amount: int) -> list[dict[str, str]]:
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=12)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    parsed_results = []

    for result in soup.find_all("div", class_="result"):
        title = result.find("a", class_="result__a")
        snippet = result.find("a", class_="result__snippet")
        if not title:
            continue

        title_text = title.get_text(strip=True)
        raw_link = title.get("href", "")
        ddg_link = urljoin("https://duckduckgo.com", raw_link)
        link = _extract_ddg_target(ddg_link)
        snippet_text = snippet.get_text(strip=True) if snippet else ""
        parsed_results.append(
            {
                "title": title_text,
                "link": link,
                "snippet": snippet_text,
            }
        )
        if len(parsed_results) >= amount:
            break

    return parsed_results


def web_search(query: str, num_results: int = 5) -> str:
    """Busca na internet usando DuckDuckGo e retorna resultados limpos."""
    query = (query or "").strip()
    if not query:
        return "Erro na busca: a consulta nao pode estar vazia."

    amount = _coerce_amount(num_results, default=5, max_value=10)

    try:
        parsed_results = _duckduckgo_results(query=query, amount=amount)
        if not parsed_results:
            return f"Nenhum resultado util encontrado para: {query}"

        results = [
            f"- {item['title']}\n  {item['link']}\n  {item['snippet']}\n"
            for item in parsed_results
        ]

        return f"Resultados da busca para '{query}':\n\n" + "\n".join(results)

    except requests.RequestException as exc:
        return f"Erro na busca (rede/http): {exc}"
    except Exception as exc:
        return f"Erro inesperado na busca: {exc}"


def browse_page(url: str, instructions: str = "Extraia o conteudo principal e resuma em portugues.") -> str:
    """Acessa uma URL especifica e retorna conteudo limpo."""
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        return "Erro ao acessar URL: informe uma URL com http:// ou https://"

    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines[:1500])

        return (
            f"Conteudo da pagina ({url}):\n\n{clean_text}\n\n"
            f"Instrucoes aplicadas: {instructions}"
        )

    except requests.RequestException as exc:
        return f"Erro ao acessar {url} (rede/http): {exc}"
    except Exception as exc:
        return f"Erro inesperado ao acessar {url}: {exc}"


def search_images(query: str, num_results: int = 5) -> str:
    """Busca imagens no Wikimedia Commons sem precisar de API key."""
    query = (query or "").strip()
    if not query:
        return "Erro na busca de imagens: a consulta nao pode estar vazia."

    amount = _coerce_amount(num_results, default=5, max_value=20)

    try:
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            headers=DEFAULT_HEADERS,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 6,
                "gsrlimit": amount,
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json",
            },
            timeout=15,
        )
        response.raise_for_status()

        payload = response.json()
        pages = payload.get("query", {}).get("pages", {})
        if not pages:
            return f"Nenhuma imagem encontrada para: {query}"

        results = []
        for page in pages.values():
            title = page.get("title", "(sem titulo)")
            imageinfo = page.get("imageinfo") or []
            if not imageinfo:
                continue

            info = imageinfo[0]
            image_url = info.get("url", "")
            page_url = info.get("descriptionurl", "")
            if not image_url:
                continue

            results.append(
                f"- {title}\n"
                f"  imagem: {image_url}\n"
                f"  pagina: {page_url}\n"
            )

            if len(results) >= amount:
                break

        if not results:
            return f"Nenhuma imagem util encontrada para: {query}"

        return f"Resultados de imagens para '{query}':\n\n" + "\n".join(results)

    except requests.RequestException as exc:
        return f"Erro na busca de imagens (rede/http): {exc}"
    except Exception as exc:
        return f"Erro inesperado na busca de imagens: {exc}"


def search_videos(query: str, num_results: int = 5) -> str:
    """Busca videos no YouTube via DuckDuckGo (links de estudo)."""
    query = (query or "").strip()
    if not query:
        return "Erro na busca de videos: a consulta nao pode estar vazia."

    amount = _coerce_amount(num_results, default=5, max_value=10)

    try:
        parsed_results = _duckduckgo_results(
            query=f"site:youtube.com/watch {query}",
            amount=amount,
        )

        if not parsed_results:
            return f"Nenhum video util encontrado para: {query}"

        results = [
            f"- {item['title']}\n  {item['link']}\n  {item['snippet']}\n"
            for item in parsed_results
        ]
        return f"Resultados de videos para '{query}':\n\n" + "\n".join(results)

    except requests.RequestException as exc:
        return f"Erro na busca de videos (rede/http): {exc}"
    except Exception as exc:
        return f"Erro inesperado na busca de videos: {exc}"


def _normalize_tool_args(arguments: Any) -> dict:
    """Normaliza argumentos vindos de tool_calls para dict."""
    if isinstance(arguments, dict):
        return arguments

    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    return {}


TOOL_MAP.update(
    {
        "web_search": web_search,
        "browse_page": browse_page,
        "search_images": search_images,
        "search_videos": search_videos,
    }
)
