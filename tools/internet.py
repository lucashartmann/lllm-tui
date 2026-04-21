import base64
import json
import re
import time
import unicodedata
from datetime import datetime, timedelta
from typing import Any
from xml.etree import ElementTree as ET
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
import ollama
import requests
from bs4 import BeautifulSoup

from database import shelve


MAX_TEXT_SIZE = 12000

BLACKLIST = [
    "leia mais", "artigos relacionados", "publicidade",
    "compartilhar", "newsletter", "anúncio"
]

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

REQUEST_TIMEOUT = 15

STOPWORDS = {
    "a", "o", "as", "os", "de", "do", "da", "dos", "das", "e", "em",
    "para", "por", "com", "sem", "um", "uma", "no", "na", "nos", "nas",
    "ao", "aos", "ultimas", "ultimos", "noticias", "sobre", "proximo", "proxima"
}


def _normalize_query(query: str) -> str:
    text = (query or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _dedupe_results(results: list[dict], amount: int) -> list[dict]:
    seen_links = set()
    final = []

    for item in results:
        link = str(item.get("link", "")).strip()
        title = str(item.get("title", "")).strip()

        if not link or not title:
            continue

        link = link.split("#")[0]  # remove âncora
        link = link.rstrip("/")

        if link in seen_links:
            continue

        seen_links.add(link)

        final.append({
            "title": title,
            "link": link,
            "snippet": str(item.get("snippet", "")).strip(),
        })

        if len(final) >= amount:
            break

    return final

def _tokens_relevantes(query: str) -> list[str]:
    base = _strip_accents((query or "").lower())
    tokens = re.findall(r"[a-z0-9]+", base)
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]



def score_result(item: dict, query_tokens: list[str]) -> float:
    title = _strip_accents(item.get("title", "").lower())
    snippet = _strip_accents(item.get("snippet", "").lower())

    score = 0.0

    for tok in query_tokens:
        if tok in title:
            score += 3.0  

        if tok in snippet:
            score += 1.2

    if query_tokens and all(tok in (title + snippet) for tok in query_tokens):
        score += 3.0

    if len(snippet) < 20:
        score -= 1.0

    return score

def _clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _remove_noise(text: str) -> str:
    lines = text.split("\n")
    filtered = [
        l for l in lines
        if not any(word in l.lower() for word in BLACKLIST)
    ]
    return "\n".join(filtered)


def _smart_truncate(text: str, max_chars: int) -> str:
    parts = text.split("\n\n")
    result = []
    total = 0

    for p in parts:
        if total + len(p) > max_chars:
            break
        result.append(p)
        total += len(p)

    return "\n\n".join(result)


def _preserve_code_blocks(soup: BeautifulSoup):
    for pre in soup.find_all("pre"):
        code = pre.get_text("\n", strip=True)
        pre.replace_with(f"\n```python\n{code}\n```\n")


def _convert_to_markdown(soup: BeautifulSoup):
    for h1 in soup.find_all("h1"):
        h1.replace_with(f"\n# {h1.get_text(strip=True)}\n")

    for h2 in soup.find_all("h2"):
        h2.replace_with(f"\n## {h2.get_text(strip=True)}\n")

    for h3 in soup.find_all("h3"):
        h3.replace_with(f"\n### {h3.get_text(strip=True)}\n")

    for li in soup.find_all("li"):
        li.replace_with(f"\n- {li.get_text(strip=True)}")

    for a in soup.find_all("a"):
        text = a.get_text(strip=True)
        href = a.get("href")
        if text and href:
            a.replace_with(f"{text} ({href})")

    return soup


def browse_page(url: str, instructions: str = "") -> str:
    import requests
    from urllib.parse import urljoin

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"browse_page: Acessando página: {url} (status {response.status_code})")
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup([
            "script", "style", "nav", "header", "footer",
            "aside", "noscript", "form", "svg"
        ]):
            tag.decompose()

        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find("section")
            or soup.body
        )

        if not main:
            return "Erro: conteúdo não encontrado."

        _preserve_code_blocks(main)

        main = _convert_to_markdown(main)

        text = main.get_text("\n", strip=True)

        text = _clean_text(text)
        text = _remove_noise(text)

        text = _smart_truncate(text, MAX_TEXT_SIZE)

        return (
            f"[PAGINA]\nURL: {url}\n\n"
            f"{text}\n\n"
            f"[INSTRUCOES]\n{instructions or 'nenhuma'}"
        )

    except Exception as e:
        return f"Erro ao acessar página: {e}"



def _safe_request(url: str, **kwargs) -> requests.Response:
    """Request com retry simples."""
    for _ in range(2):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException:
            time.sleep(1)
    raise


def _coerce_amount(num_results: Any, default: int = 5, max_value: int = 10) -> int:
    try:
        return max(1, min(int(num_results), max_value))
    except Exception:
        return default


def _extract_ddg_target(link: str) -> str:
    parsed = urlparse(link)
    if "duckduckgo.com" not in parsed.netloc:
        return link

    query = parse_qs(parsed.query)
    target = query.get("uddg", [""])[0]
    return unquote(target) if target else link


def _extract_bing_target(link: str) -> str:
    parsed = urlparse(link)
    if "bing.com" not in parsed.netloc or not parsed.path.startswith("/ck/"):
        return link

    params = parse_qs(parsed.query)
    encoded = params.get("u", [""])[0]
    if not encoded:
        return link

    
    if encoded.startswith("a1"):
        encoded = encoded[2:]

    try:
        padding = "=" * ((4 - len(encoded) % 4) % 4)
        decoded = base64.urlsafe_b64decode(encoded + padding).decode("utf-8", errors="ignore")
        if decoded.startswith("http"):
            return decoded
    except Exception:
        pass

    return link


def _duckduckgo_results(query: str, amount: int) -> list[dict]:
    def _collect_from_html(html: str, limit: int) -> list[dict]:
        soup_local = BeautifulSoup(html, "html.parser")
        collected: list[dict] = []

        cards = soup_local.select("div.result") or soup_local.select("article")
        for card in cards:
            title_tag = card.select_one("a.result__a") or card.select_one("a[data-testid='result-title-a']")
            snippet_tag = card.select_one(".result__snippet") or card.select_one(".snippet")

            if not title_tag:
                continue

            raw_link = title_tag.get("href", "")
            full_link = urljoin("https://duckduckgo.com", raw_link)
            link = _extract_ddg_target(full_link)

            if not link.startswith("http"):
                continue

            collected.append({
                "title": title_tag.get_text(strip=True),
                "link": link,
                "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
            })

            if len(collected) >= limit:
                break

        return collected

    html_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    response = _safe_request(html_url, headers=DEFAULT_HEADERS)
    results = _collect_from_html(response.text, amount)

    if len(results) >= amount:
        return results

    
    lite_url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
    lite_response = _safe_request(lite_url, headers=DEFAULT_HEADERS)
    lite_soup = BeautifulSoup(lite_response.text, "html.parser")

    for anchor in lite_soup.select("a.result-link"):
        raw_link = anchor.get("href", "")
        full_link = urljoin("https://duckduckgo.com", raw_link)
        link = _extract_ddg_target(full_link)

        if not link.startswith("http"):
            continue

        results.append({
            "title": anchor.get_text(strip=True),
            "link": link,
            "snippet": "",
        })

        if len(results) >= amount:
            break

    return results

def _bing_web_results(query: str, amount: int) -> list[dict]:
    response = _safe_request(
        "https://www.bing.com/search",
        headers=DEFAULT_HEADERS,
        params={"q": query, "setlang": "pt-BR"},
    )
    soup = BeautifulSoup(response.text, "html.parser")

    results: list[dict] = []
    for card in soup.select("li.b_algo"):
        link_tag = card.select_one("h2 a[href]")
        title_tag = card.select_one("h2")
        snippet_tag = card.select_one(".b_caption p") or card.select_one("p")

        if not link_tag or not title_tag:
            continue

        raw_link = link_tag.get("href", "").strip()
        link = _extract_bing_target(raw_link)
        if not link.startswith("http"):
            continue

        results.append({
            "title": title_tag.get_text(" ", strip=True),
            "link": link,
            "snippet": snippet_tag.get_text(" ", strip=True) if snippet_tag else "",
        })

        if len(results) >= amount:
            break

    return results

def web_search(query: str, num_results: int = 5) -> str:
    query = _normalize_query(query)
    if not query:
        return "Erro: consulta vazia."

    amount = _coerce_amount(num_results)
    print(f"Realizando busca na web por: {query} (max {amount} resultados)")

    try:
        aggregate = []

        if len(aggregate) < amount:
            try:
                aggregate.extend(_bing_web_results(query, amount * 2))
            except Exception as e:
                print(f"Erro na busca Bing: {e}")
                pass

        if len(aggregate) < amount:
            try:
                aggregate.extend(_duckduckgo_results(query, amount))
            except Exception as e:
                print(f"Erro na busca DuckDuckGo: {e}")
                pass

        query_tokens = _tokens_relevantes(query)

        ranked = _dedupe_results(aggregate, amount * 3)

        if query_tokens:
            ranked.sort(
                key=lambda item: score_result(item, query_tokens),
                reverse=True,
            )

        results = ranked[:amount]

        if not results:
            return f"Nenhum resultado encontrado para: {query}"

        formatted = []
        for r in results:
            formatted.append(
                f"- {r['title']}\n"
                f"  {r['link']}\n"
                f"  {r['snippet']}\n"
            )
            print(f"Resultado: {r['title']} ({r['link']})")

        return f"[BUSCA] {query}\n\n" + "\n".join(formatted)

    except Exception as e:
        return f"Erro na busca: {e}"


def search_images(query: str, num_results: int = 5) -> str:
    query = (query or "").strip()
    if not query:
        return "Erro: consulta vazia."

    amount = _coerce_amount(num_results, max_value=20)

    try:
        response = _safe_request(
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
        )

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        results = []
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]

            url = info.get("url")
            if not url:
                continue

            results.append(
                f"- {page.get('title')}\n"
                f"  {url}\n"
            )

            if len(results) >= amount:
                break

        return f"[IMAGENS] {query}\n\n" + "\n".join(results)

    except Exception as e:
        return f"Erro imagens: {e}"


def search_videos(query: str, num_results: int = 5) -> str:
    query = (query or "").strip()
    if not query:
        return "Erro: consulta vazia."

    amount = _coerce_amount(num_results)

    try:
        results = _duckduckgo_results(f"site:youtube.com {query}", amount)

        formatted = []
        for r in results:
            formatted.append(
                f"- {r['title']}\n"
                f"  {r['link']}\n"
            )

        return f"[VIDEOS] {query}\n\n" + "\n".join(formatted)

    except Exception as e:
        return f"Erro vídeos: {e}"



def _extract_links(text: str) -> list[str]:
    return re.findall(r"https?://\S+", text or "")



def learn_topic(topic: str,
                max_pages: int = 3,
                max_images: int = 3) -> str:

    if not topic:
        return "Erro: topic vazio."

    report = [f"[TEMA] {topic}"]

    web = web_search(topic, num_results=5)
    report.append(web)

    links = _extract_links(web)[:max_pages]

    for link in links:
        content = browse_page(link)
        report.append(content[:2000])

    imgs = search_images(topic, num_results=max_images)
    report.append(imgs)

    img_links = _extract_links(imgs)[:max_images]

    if img_links:
        try:
            payloads = []
            for url in img_links:
                r = requests.get(url, timeout=10)
                payloads.append(base64.b64encode(r.content).decode())

            if shelve.carregar_modelo():
                model_name = shelve.carregar_modelo()
            else:
                return "Nenhum modelo configurado para sumarização."

            resp = ollama.chat(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": f"Explique visualmente: {topic}",
                    "images": payloads
                }]
            )

            report.append(resp["message"]["content"])
        except Exception as e:
            report.append(f"Erro visão: {e}")

    vids = search_videos(topic, num_results=3)
    report.append(vids)

    return "\n\n".join(report)
