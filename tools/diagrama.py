from pathlib import Path
from typing import Optional

import io
import os
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from view.app import App
import ollama
import numpy as np
# import cairosvg

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

    return Path(path).read_text(encoding="utf-8")

from llama_index.core.tools import FunctionTool

diagram_skill_tool = FunctionTool.from_defaults(
    fn=get_diagram_skill,
    name="get_diagram_skill",
    description="""
Use essa função quando o usuário pedir para gerar diagramas,
como UML, BRModelo, banco de dados, entidade-relacionamento, etc.

Ela retorna instruções (.md) que você deve seguir para gerar um SVG.
"""
)



# def svg_to_png(svg_content: str, output_path: str = "output.png"):
#     cairosvg.svg2png(
#         bytestring=svg_content.encode("utf-8"),
#         write_to=output_path
#     )
#     return output_path

def generate_diagram_svg(request: str, model="llama3") -> str:
    skill = get_diagram_skill(request)

    system = f"""
Você é um gerador de SVG.
Responda APENAS com SVG válido.

{skill}
"""

    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": request},
        ]
    )

    return response["message"]["content"]