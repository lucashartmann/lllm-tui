from pathlib import Path
import uuid
import re
from llama_index.core.tools import FunctionTool
import ollama
import cairosvg
from typing import Optional
from database import shelve

SKILLS_ROOT = r"C:\Users\dudua\Music\Projetos\lllm-tui\skills\diagramas"

SKILL_FILES = {
    "brmodelo_conceitual": SKILLS_ROOT + "/brmodelo/" + "conceitual.md",
    "brmodelo_logico": SKILLS_ROOT + "/brmodelo/" + "logico.md",
    "uml_class": SKILLS_ROOT + "/astah/" + "uml_class.md",
    "uml_sequence": SKILLS_ROOT + "/astah/" + "uml_sequence.md",
    "uml_use_case": SKILLS_ROOT + "/astah/" + "uml_use_case.md",
}


def get_diagram_skill(request: str) -> str:
    text = request.lower()

    if "banco" in text or "entidade" in text or "er" in text:
        if "logico" in text or "tabela" in text or "fk" in text:
            path = SKILL_FILES["brmodelo_logico"]
        else:
            path = SKILL_FILES["brmodelo_conceitual"]

    elif "sequencia" in text:
        path = SKILL_FILES["uml_sequence"]

    elif "caso de uso" in text:
        path = SKILL_FILES["uml_use_case"]

    elif "classe" in text or "uml" in text:
        path = SKILL_FILES["uml_class"]

    else:
        path = SKILL_FILES["brmodelo_conceitual"]
        
    print(f"Skill selecionada: {path}")

    return Path(path).read_text(encoding="utf-8")


def svg_to_png(svg: str):
    filename = f"diagram_{uuid.uuid4().hex}.png"
    print(f"Convertendo SVG para PNG: {filename}")
    cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        write_to=filename
    )
    return filename


def _sanitize_svg_output(content: str) -> str:
    text = (content or "").strip()

    fence_match = re.search(r"```(?:svg)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    svg_match = re.search(r"<svg\b.*?</svg>", text, flags=re.IGNORECASE | re.DOTALL)
    if svg_match:
        text = svg_match.group(0).strip()

    return text


def _resolve_model(model: Optional[str] = None) -> str:
    candidate = (model or "").strip() 
    if candidate:
        return candidate

    try:
        listed = ollama.list()
        models = getattr(listed, "models", [])
        if models:
            first = getattr(models[0], "model", "")
            if first:
                return first
    except Exception:
        pass

    raise ValueError("Nenhum modelo Ollama configurado para gerar diagrama")


def gerar_diagrama(request: str, model: Optional[str] = None) -> str:
    if shelve.carregar_modelo():
        model_name = shelve.carregar_modelo()
    else:
        model_name = _resolve_model(model)
    skill = get_diagram_skill(request)

    system = f"""
Você é um gerador de diagramas em SVG.

REGRAS:
- Responda APENAS com SVG puro
- NÃO use markdown
- NÃO explique
- NÃO escreva texto fora do <svg>
- Comece diretamente com <svg>
- NUNCA envolva a resposta em ``` ou ```svg
- NUNCA inclua texto antes ou depois do SVG
- NUNCA retorne comentários, explicações ou blocos de código markdown

{skill}
"""

    print(f"gerar_diagrama - MODEL: {model_name}")

    response = ollama.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": request},
        ]
    )

    content = _sanitize_svg_output(response["message"]["content"])
    
    print("[DIAGRAM TOOL RESPONSE]")
    print(content)

    if content.startswith("<svg") and content.endswith("</svg>"):
        path = svg_to_png(content)
    else:
        raise ValueError("Modelo não retornou um SVG valido")
        
    print(f"Diagrama salvo em: {path}")

    return {
        "svg": content,
        "png_path": path
    }


diagram_tool = FunctionTool.from_defaults(
    fn=gerar_diagrama,
    name="generate_diagram",
    description="""
Gera um diagrama em SVG.

- Retorna SVG válido
- Se necessário, pode ser convertido para PNG
- NÃO salvar automaticamente em arquivo

Use quando o usuário pedir:
- UML
- BRModelo
- Diagramas
"""
)
