import argparse
import base64
import re

import requests

import ollama

from diagrama import DEFAULT_MODEL as DEFAULT_DIAGRAM_MODEL
from diagrama import generate_and_save_diagram
from internet import (
    TOOL_MAP,
    _normalize_tool_args,
    browse_page,
    search_images,
    search_videos,
    web_search,
)


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _diagram_style_from_type(diagram_type: str, request: str) -> str:
    """Converte tipo solicitado para estilo esperado no diagrama.py."""
    kind = _normalize_text(diagram_type)
    text = _normalize_text(request)
    joined = f"{kind} {text}"

    astah_keywords = [
        "astah",
        "uml",
        "classe",
        "class",
        "sequencia",
        "use case",
        "caso de uso",
        "atividade",
    ]
    brmodelo_keywords = [
        "br modelo",
        "brmodelo",
        "conceitual",
        "logico",
        "fisi",
        "relacionamento",
        "entidade",
        "er",
        "banco de dados",
        "schema",
    ]

    if any(token in joined for token in astah_keywords):
        return "astah"
    if any(token in joined for token in brmodelo_keywords):
        return "brmodelo"
    return "auto"


def generate_diagram(
    request: str,
    diagram_type: str = "auto",
    output_file: str = "diagrama.svg",
    model: str = DEFAULT_DIAGRAM_MODEL,
) -> str:
    """
    Gera um diagrama SVG em arquivo para pedidos como conceitual, logico, relacionamento, UML, etc.

    Parameters
    ----------
    request:
        Descricao textual do diagrama.
    diagram_type:
        Tipo opcional (ex.: conceitual, logico, relacionamento, uml, astah, auto).
    output_file:
        Nome/caminho do arquivo SVG de saida.
    model:
        Modelo Ollama usado na geracao do SVG.
    """
    style = _diagram_style_from_type(diagram_type, request)
    saved = generate_and_save_diagram(
        request=request,
        output_file=output_file,
        model=model,
        style=style,
    )
    return (
        f"Diagrama gerado com sucesso em: {saved}. "
        f"Estilo aplicado: {style}."
    )


TOOL_MAP.update({"generate_diagram": generate_diagram})


def _extract_links(text: str) -> list[str]:
    """Extrai URLs de um texto retornado pelas ferramentas."""
    return re.findall(r"https?://\S+", text or "")


def learn_topic(
    topic: str,
    vision_model: str = "qwen2.5vl:7b",
    max_pages: int = 3,
    max_images: int = 3,
) -> str:
    """
    Pesquisa um tema e tenta extrair entendimento visual com modelo multimodal.

    Observacao: isso melhora o contexto apenas na conversa atual (nao treina o modelo permanentemente).
    """
    topic = (topic or "").strip()
    if not topic:
        return "Erro em learn_topic: o campo topic nao pode ser vazio."

    try:
        page_limit = max(1, min(int(max_pages), 5))
    except (TypeError, ValueError):
        page_limit = 3

    try:
        image_limit = max(1, min(int(max_images), 5))
    except (TypeError, ValueError):
        image_limit = 3

    report_parts = [f"[LEARN_TOPIC] Tema: {topic}"]

    web_results = web_search(topic, num_results=6)
    report_parts.append("\n[FONTES WEB]\n" + web_results)

    links = _extract_links(web_results)
    page_summaries = []
    for link in links:
        if len(page_summaries) >= page_limit:
            break
        content = browse_page(link)
        # Limita para manter contexto enxuto.
        page_summaries.append(content[:2500])

    if page_summaries:
        report_parts.append("\n[LEITURA DE PAGINAS]\n" + "\n\n".join(page_summaries))

    image_results = search_images(topic, num_results=image_limit)
    report_parts.append("\n[BUSCA DE IMAGENS]\n" + image_results)

    image_links = []
    for url in _extract_links(image_results):
        lowered = url.lower()
        if any(ext in lowered for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]):
            image_links.append(url)
    image_links = image_links[:image_limit]

    if image_links:
        try:
            image_payloads = []
            for url in image_links:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                image_payloads.append(base64.b64encode(response.content).decode("ascii"))

            vision_response = ollama.chat(
                model=vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Tema: {topic}. Analise estas imagens e explique os padroes visuais mais importantes "
                            "para ensinar esse tema de forma objetiva."
                        ),
                        "images": image_payloads,
                    }
                ],
                options={"temperature": 0.2},
            )
            visual_analysis = vision_response.get("message", {}).get("content", "")
            if visual_analysis:
                report_parts.append("\n[ANALISE VISUAL]\n" + visual_analysis)
        except Exception as exc:
            report_parts.append(
                "\n[ANALISE VISUAL]\n"
                f"Nao foi possivel analisar imagens com o modelo '{vision_model}': {exc}"
            )

    video_results = search_videos(topic, num_results=4)
    report_parts.append("\n[VIDEOS]\n" + video_results)

    report_parts.append(
        "\n[NOTA]\n"
        "Este aprendizado e contextual (apenas nesta conversa). "
        "Para persistir conhecimento, e preciso salvar resumo em memoria externa (arquivo/banco)."
    )

    return "\n".join(report_parts)


TOOL_MAP.update({"learn_topic": learn_topic})


def run_agent(user_question: str, model: str = "qwen3.5:4b", max_turns: int = 12) -> None:
    messages = [
        {
            "role": "system",
            "content": (
                "Voce e um assistente util e preciso. "
                "Quando o usuario pedir para gerar diagrama (conceitual, logico, relacionamento, ER, UML, astah), "
                "prefira usar a ferramenta generate_diagram para criar o SVG em arquivo. "
                "Quando o usuario perguntar sobre assunto que voce nao domina ou pedir para aprender um tema, "
                "use web_search para achar fontes, browse_page para extrair conteudo e, se fizer sentido, "
                "search_images e search_videos para trazer material visual. "
                "Se o usuario pedir explicitamente para voce aprender um tema, prefira usar learn_topic. "
                "Use ferramentas de internet sempre que precisar validar fatos externos."
            ),
        },
        {"role": "user", "content": user_question},
    ]

    tools = [
        web_search,
        browse_page,
        search_images,
        search_videos,
        learn_topic,
        generate_diagram,
    ]

    for _ in range(max_turns):
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=tools,
        )

        message = response["message"]
        messages.append(message)

        if not message.get("tool_calls"):
            print("\n=== RESPOSTA FINAL ===\n")
            print(message.get("content", "(sem conteudo)"))
            break

        for tool_call in message.get("tool_calls", []):
            function_data = tool_call.get("function", {})
            func_name = function_data.get("name", "")
            args = _normalize_tool_args(function_data.get("arguments", {}))

            print(f"-> Executando: {func_name} | args: {args}")

            tool_func = TOOL_MAP.get(func_name)
            if tool_func:
                try:
                    result = tool_func(**args)
                except TypeError as exc:
                    result = f"Erro de argumentos na ferramenta {func_name}: {exc}"
                except Exception as exc:
                    result = f"Erro ao executar ferramenta {func_name}: {exc}"
            else:
                result = f"Ferramenta desconhecida: {func_name}"

            messages.append(
                {
                    "role": "tool",
                    "content": str(result),
                    "name": func_name,
                }
            )
    else:
        print("Maximo de rodadas atingido.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agente Ollama com suporte a diagramas e web.")
    parser.add_argument("question", help="Pergunta/comando para o agente.")
    parser.add_argument(
        "-m",
        "--model",
        default="qwen3.5:4b",
        help="Modelo principal do agente (padrao: qwen3.5:4b).",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=12,
        help="Maximo de rodadas de tool-calling.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = _parse_args()
    run_agent(
        user_question=cli_args.question,
        model=cli_args.model,
        max_turns=cli_args.max_turns,
    )
