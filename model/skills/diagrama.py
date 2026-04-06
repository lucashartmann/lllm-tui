from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional

import ollama


DEFAULT_MODEL = "qwen3.5:4b"
DEFAULT_SKILL_FILE = Path(__file__).resolve().parents[1] / "BrModelo - Astah.md"


def _read_skill_prompt(skill_file: Optional[str] = None) -> str:
	"""Carrega o prompt do skill que define as regras de desenho."""
	path = Path(skill_file) if skill_file else DEFAULT_SKILL_FILE
	if not path.exists():
		raise FileNotFoundError(f"Arquivo de skill nao encontrado: {path}")
	return path.read_text(encoding="utf-8")


def _build_system_prompt(skill_text: str) -> str:
	"""Monta o prompt de sistema com foco em retorno estrito de SVG."""
	return (
		"Voce e um gerador de diagramas SVG. "
		"Siga estritamente as instrucoes abaixo para escolher o tipo de diagrama, layout, estilo e SVG final. "
		"Retorne apenas SVG valido, sem markdown, sem explicacoes extras.\n\n"
		"=== SKILL ===\n"
		f"{skill_text}\n"
		"=== FIM SKILL ===\n"
	)


def _build_user_prompt(request: str, style: str = "auto") -> str:
	style = (style or "auto").strip().lower()
	if style not in {"auto", "brmodelo", "astah"}:
		raise ValueError("style deve ser um destes valores: auto, brmodelo, astah")

	style_hint = {
		"auto": "Escolha automaticamente entre BR Modelo e Astah conforme o contexto.",
		"brmodelo": "Use obrigatoriamente estilo BR Modelo (ER conceitual).",
		"astah": "Use obrigatoriamente estilo Astah (UML correspondente).",
	}[style]

	return (
		f"Solicitacao do usuario:\n{request}\n\n"
		f"Diretiva de estilo: {style_hint}\n"
		"Importante: responda somente com SVG bruto, sem cercas de codigo."
	)


def _extract_svg(content: str) -> str:
	"""Extrai o primeiro bloco SVG valido do texto retornado."""
	if not content:
		raise ValueError("Resposta vazia do modelo.")

	text = content.strip()

	if text.startswith("<svg") and text.endswith("</svg>"):
		return text

	match = re.search(r"<svg\b[\s\S]*?</svg>", text, flags=re.IGNORECASE)
	if not match:
		raise ValueError("Nao foi encontrado bloco SVG na resposta do modelo.")
	return match.group(0).strip()


def generate_diagram_svg(
	request: str,
	model: str = DEFAULT_MODEL,
	style: str = "auto",
	skill_file: Optional[str] = None,
) -> str:
	"""
	Gera SVG de diagrama usando Ollama com regras do skill.

	Parameters
	----------
	request:
		Texto descrevendo o diagrama desejado.
	model:
		Modelo Ollama (ex.: qwen3.5:4b, llama3.1:8b).
	style:
		auto | brmodelo | astah
	skill_file:
		Caminho opcional para arquivo markdown de skill.
	"""
	if not request or not request.strip():
		raise ValueError("request nao pode ser vazio.")

	skill_text = _read_skill_prompt(skill_file)
	system_prompt = _build_system_prompt(skill_text)
	user_prompt = _build_user_prompt(request.strip(), style=style)

	response = ollama.chat(
		model=model,
		messages=[
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		],
		options={"temperature": 0.2},
	)

	content = response.get("message", {}).get("content", "")
	return _extract_svg(content)


def save_svg(svg: str, output_file: str) -> Path:
	"""Salva o SVG em arquivo e retorna o caminho absoluto."""
	if not svg.strip().startswith("<svg"):
		raise ValueError("Conteudo fornecido nao parece um SVG valido.")

	path = Path(output_file)
	if path.suffix.lower() != ".svg":
		path = path.with_suffix(".svg")

	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(svg, encoding="utf-8")
	return path.resolve()


def generate_and_save_diagram(
	request: str,
	output_file: str,
	model: str = DEFAULT_MODEL,
	style: str = "auto",
	skill_file: Optional[str] = None,
) -> Path:
	"""Atalho para gerar e salvar o diagrama em um unico passo."""
	svg = generate_diagram_svg(
		request=request,
		model=model,
		style=style,
		skill_file=skill_file,
	)
	return save_svg(svg, output_file)


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Gera diagramas SVG (BR Modelo/Astah) usando Ollama.",
	)
	parser.add_argument(
		"request",
		help="Descricao do diagrama desejado.",
	)
	parser.add_argument(
		"-o",
		"--output",
		default="diagrama.svg",
		help="Arquivo de saida SVG (padrao: diagrama.svg).",
	)
	parser.add_argument(
		"-m",
		"--model",
		default=DEFAULT_MODEL,
		help=f"Modelo Ollama (padrao: {DEFAULT_MODEL}).",
	)
	parser.add_argument(
		"-s",
		"--style",
		choices=["auto", "brmodelo", "astah"],
		default="auto",
		help="Forca estilo de diagrama: auto, brmodelo ou astah.",
	)
	parser.add_argument(
		"--skill-file",
		default=str(DEFAULT_SKILL_FILE),
		help="Caminho para o arquivo markdown de regras do diagrama.",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = _parse_args()
	output_path = generate_and_save_diagram(
		request=args.request,
		output_file=args.output,
		model=args.model,
		style=args.style,
		skill_file=args.skill_file,
	)
	print(f"Diagrama salvo em: {output_path}")