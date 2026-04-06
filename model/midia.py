from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import io
import base64
import re
import os
from typing import Tuple, List, Optional
from model.diff_editor import DiffEditor, DiffValidationError, DiffApplicationError

arquivos = [
    ("Code", "*.py *.js *.html *.css *.tcss *.cpp"),
    ("Pastas", ""),
    ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff"),
    ("Documentos", "*.pdf *.txt *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.odt *.ods *.odp")
]


def get_chunks_codigo(caminho_arquivo: str):
    try:
        if not caminho_arquivo:
            return []

        ext = Path(caminho_arquivo).suffix.lower()

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            codigo = f.read()

        temp_md = Path("temp_code.md")
        with open(temp_md, "w", encoding="utf-8") as f:
            f.write(f"```{ext[1:]}\n{codigo}\n```")
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(temp_md)

        document = result.document
        from docling.chunking import HybridChunker

        chunker = HybridChunker()
        chunks = list(chunker.chunk(document))

        temp_md.unlink(missing_ok=True)

        return [chunk.text for chunk in chunks]

    except Exception as e:
        print("Erro ao gerar chunks:", e)
        return []


def get_chunks_codigo_edicao(caminho_arquivo: str, tamanho_chunk: int = 1000, sobreposicao: int = 20):
    try:
        if not caminho_arquivo:
            return []

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        total = len(linhas)
        if total == 0:
            return []

        chunks = []
        inicio = 0

        while inicio < total:
            fim = min(inicio + tamanho_chunk, total)
            trecho = ""
            for i in range(inicio, fim):
                trecho += linhas[i]
            chunks.append(trecho)

            if fim == total:
                break
            inicio = fim - sobreposicao

        return chunks

    except Exception as e:
        print("Erro ao gerar chunks de edição:", e)
        return []


def get_chunks_documento(caminho_arquivo: str):

    try:
        if not caminho_arquivo:
            return []
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(caminho_arquivo)
        doc = result.document
        from docling.chunking import HybridChunker
        chunker = HybridChunker()

        chunks = list(chunker.chunk(doc))

        return [chunk.text for chunk in chunks]

    except Exception as e:
        print(f"Erro ao gerar chunks: {e}")
        return []


def encode_image(image_path):
    try:
        if image_path:
            return base64.b64encode(Path(image_path).read_bytes()).decode()
    except Exception as e:
        print(e)
        pass


def get_conteudo(caminho):
    try:
        if caminho:
            with open(file=caminho, mode="r", encoding="utf-8") as arquivo:
                conteudo = ""
                for index, linha in enumerate(arquivo.readlines(), start=1):
                    conteudo += f"{index:03d}|{linha}"
            return conteudo
    except Exception as e:
        print(e)
        pass


def contar_linhas(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(e)
        return 0


def selecionar_arquivo():
    try:
        root = tk.Tk()
        root.withdraw()

        caminhos = filedialog.askopenfilenames(
            title="Selecione",
            filetypes=arquivos
        )

        caminhos = list(caminhos)

        root.destroy()
        return caminhos
    except Exception as e:
        print(e)
        pass


def get_bytes(caminho):
    try:
        if caminho:
            with open(caminho, "rb") as f:
                return f.read()
    except Exception as e:
        print(e)
        pass


def limpar_diff(diff: str) -> str:

    linhas = diff.splitlines()
    resultado = []
    dentro_bloco = False
    for linha in linhas:
        if linha.strip().startswith("```"):
            dentro_bloco = not dentro_bloco
            continue
        if linha.startswith("diff --git") or linha.startswith("index "):
            continue
        resultado.append(linha)
    return "\n".join(resultado)


def _normalizar_linha_diff(linha: str) -> str:
    linha = linha.rstrip("\n").rstrip("\r")
    linha = re.sub(r"^linha\s+\d+\.\s?", "", linha)
    return linha + "\n"


def _normalizar_linha_arquivo(linha: str) -> str:
    return linha.rstrip("\n").rstrip("\r") + "\n"


def aplicar_diff_manual(caminho, diff):
    if not caminho:
        print(f"Erro: caminho vazio")
        return False

    print(f"DEBUG: Aplicando diff em: {caminho}")
    print(f"DEBUG: Diff recebido (primeiros 200 chars): {diff[:200]}")

    try:
        diff = limpar_diff(diff)
        print(f"DEBUG: Diff após limpar (primeiros 200 chars): {diff[:200]}")

        if not os.path.exists(caminho):
            print(f"ERRO: Arquivo não existe: {caminho}")
            return False

        print(
            f"DEBUG: Arquivo existe, tamanho: {os.path.getsize(caminho)} bytes")

        with open(caminho, "r", encoding="utf-8") as f:
            linhas_originais = f.readlines()
            print(f"DEBUG: Arquivo lido, {len(linhas_originais)} linhas")
            if len(linhas_originais) > 0:
                print(f"DEBUG: Primeiras 3 linhas do arquivo:")
                for i, l in enumerate(linhas_originais[:3]):
                    print(f"  {i+1}: {repr(l)}")

        linhas = [_normalizar_linha_arquivo(l) for l in linhas_originais]

        diff_lines = diff.splitlines()
        i = 0
        offset = 0

        while i < len(diff_lines):
            if diff_lines[i].startswith("@@"):
                hunk_header = diff_lines[i]
                print(f"DEBUG: Processando hunk: {hunk_header}")
                try:
                    match = re.match(
                        r"@@[\s]*-([0-9]+),?([0-9]*)\s+\+([0-9]+),?([0-9]*)\s*@@", hunk_header)
                    if match:
                        old_start = int(match.group(1)) - 1
                        old_count = int(match.group(
                            2)) if match.group(2) else 1
                        new_start = int(match.group(3)) - 1
                        new_count = int(match.group(
                            4)) if match.group(4) else 1
                        print(
                            f"DEBUG: old_start={old_start}, old_count={old_count}, new_start={new_start}, new_count={new_count}")
                    else:
                        print(
                            f"WARNING: Não conseguiu parsear hunk header: {hunk_header}")
                        i += 1
                        continue

                    i += 1
                    hunk_lines = []
                    while i < len(diff_lines) and not diff_lines[i].startswith("@@"):
                        hunk_lines.append(diff_lines[i])
                        i += 1

                    print(f"DEBUG: Linhas no hunk: {len(hunk_lines)}")

                    if old_start >= len(linhas):
                        print(
                            f"WARNING: old_start ({old_start}) >= len(linhas) ({len(linhas)})")
                        continue

                    removed_lines = []
                    added_lines = []
                    context_before = []
                    context_after = []

                    for line in hunk_lines:
                        if line.startswith("-"):
                            removed_lines.append(line[1:])
                        elif line.startswith("+"):
                            added_lines.append(line[1:])
                        elif line.startswith(" "):
                            # Contexto
                            if not removed_lines and not added_lines:
                                context_before.append(line[1:])
                            else:
                                context_after.append(line[1:])

                    print(
                        f"DEBUG: {len(removed_lines)} linhas removidas, {len(added_lines)} adicionadas")
                    print(
                        f"DEBUG: Context before: {len(context_before)}, after: {len(context_after)}")

                    actual_start = old_start + offset
                    print(
                        f"DEBUG: Aplicando em índice {actual_start} (offset={offset})")

                    if removed_lines:
                        block_end = actual_start + len(removed_lines)
                        if block_end > len(linhas):
                            block_end = len(linhas)

                        current_block = linhas[actual_start:block_end]
                        print(
                            f"DEBUG: Bloco atual: {[l.rstrip() for l in current_block]}")
                        print(f"DEBUG: Esperado: {removed_lines}")

                        current_normalized = [_normalizar_linha_arquivo(
                            l).rstrip() for l in current_block]
                        removed_normalized = [_normalizar_linha_arquivo(
                            l).rstrip() for l in removed_lines]

                        if current_normalized == removed_normalized:
                            print(
                                "DEBUG: Bloco corresponde exatamente! Aplicando...")
                            linhas[actual_start:block_end] = [
                                l + "\n" for l in added_lines]
                            offset += len(added_lines) - len(removed_lines)
                        else:
                            print(
                                "DEBUG: Bloco não corresponde exatamente. Tentando correspondência fuzzy...")
                            for j, remover in enumerate(removed_lines):
                                remover_norm = _normalizar_linha_arquivo(
                                    remover).rstrip()
                                for k in range(len(linhas)):
                                    if _normalizar_linha_arquivo(linhas[k]).rstrip() == remover_norm:
                                        print(
                                            f"DEBUG: Encontrada linha removida em {k}: {remover_norm[:50]}...")
                                        linhas[k] = "__REMOVED__\n"

                            linhas = [l for l in linhas if l !=
                                      "__REMOVED__\n"]

                            if added_lines:
                                insert_pos = actual_start
                                if insert_pos > len(linhas):
                                    insert_pos = len(linhas)
                                for a, added in enumerate(added_lines):
                                    linhas.insert(insert_pos + a, added + "\n")

                            offset += len(added_lines) - len(removed_lines)
                    else:
                        if added_lines:
                            insert_pos = actual_start
                            if insert_pos > len(linhas):
                                insert_pos = len(linhas)
                            for a, added in enumerate(added_lines):
                                linhas.insert(insert_pos + a, added + "\n")
                            offset += len(added_lines)

                except Exception as e:
                    print(f"ERRO ao aplicar hunk: {e}")
                    import traceback
                    traceback.print_exc()
                    i += 1
                    continue
            else:
                i += 1

        with open(caminho, "w", encoding="utf-8") as f:
            f.writelines(linhas)

        print(f"Sucesso: diff aplicado em {caminho}")
        return True

    except Exception as e:
        print(f"Erro ao aplicar diff: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def parse_diff(diff_text: str):
    try:
        diff_text = limpar_diff(diff_text)
        file_path = None
        hunks = []

        lines = diff_text.splitlines()

        for line in lines:
            if line.startswith("+++ "):
                file_path = line[4:].strip()

            elif line.startswith("@@"):
                match = re.match(
                    r"@@ -([0-9]+),?([0-9]*) \+([0-9]+),?([0-9]*) @@", line)
                if match:
                    hunks.append({
                        'old_start': int(match.group(1)),
                        'old_count': int(match.group(2) or 1),
                        'new_start': int(match.group(3)),
                        'new_count': int(match.group(4) or 1)
                    })

            elif hunks:
                hunks[-1]['lines'] = hunks[-1].get('lines', []) + [line]

        if file_path and not Path(file_path).is_absolute():
            file_path = str((Path.cwd() / file_path).resolve())

        return file_path, hunks
    except Exception as e:
        print(e)
        pass


class ChunkedFileProcessor:

    MAX_CHUNK_SIZE = 3000
    CHUNK_OVERLAP = 500

    def __init__(self):
        self.diff_editor = DiffEditor(verbose=True)

    def divide_arquivo_em_chunks(self, caminho_arquivo: str) -> list:

        try:
            if not os.path.exists(caminho_arquivo):
                return []

            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                conteudo_completo = f.read()

            if len(conteudo_completo) <= self.MAX_CHUNK_SIZE:
                linhas = conteudo_completo.split("\n")
                conteudo_numerado = self._numerar_linhas(linhas)
                return [{
                    'numero': 1,
                    'conteudo': conteudo_numerado,
                    'linhas_info': (1, len(linhas))
                }]

            print(
                f"Arquivo grande ({len(conteudo_completo)} chars), dividindo em chunks")
            linhas = conteudo_completo.split("\n")
            chunks = []

            palavras_por_linha = sum(len(l.split())
                                     for l in linhas) / max(len(linhas), 1)
            linhas_por_chunk = max(
                10, int(self.MAX_CHUNK_SIZE / (palavras_por_linha * 5)))
            linhas_overlap = max(3, int(linhas_por_chunk * 0.2))

            i = 0
            chunk_num = 1

            while i < len(linhas):
                fim = min(i + linhas_por_chunk, len(linhas))
                chunk_linhas = linhas[i:fim]

                trecho_numerado = []
                for idx, linha in enumerate(chunk_linhas):
                    linha_real = i + idx + 1
                    trecho_numerado.append(f"{linha_real:03d}|{linha}")

                chunks.append({
                    'numero': chunk_num,
                    'conteudo': "\n".join(trecho_numerado),
                    'linhas_info': (i + 1, fim)
                })

                i = fim - linhas_overlap
                chunk_num += 1

            return chunks

        except Exception as e:
            print(f"ERRO ao dividir arquivo: {e}")
            return []

    @staticmethod
    def _numerar_linhas(linhas: list) -> str:

        resultado = []
        for i, linha in enumerate(linhas, 1):
            if not linha.endswith('\n'):
                linha = linha + '\n'
            resultado.append(f"{i:03d}|{linha}")
        return "\n".join(resultado)

    def processar_arquivo_com_prompt_v2(self, caminho_arquivo: str, prompt_inicial: str,
                                        callback_ia=None, validar_sintaxe_python: bool = True,
                                        max_retry_sintaxe: int = 1,
                                        caminho_saida: Optional[str] = None) -> Tuple[bool, str]:

        if not callback_ia:
            return False, "callback_ia é obrigatório"

        if not os.path.exists(caminho_arquivo):
            return False, f"Arquivo não existe: {caminho_arquivo}"

        print(f"\n{'='*70}")
        print(f"Iniciando processamento V2 de: {caminho_arquivo}")
        print(f"Prompt: {prompt_inicial}")
        print(f"{'='*70}\n")

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            conteudo_original = f.read()

        caminho_destino = caminho_saida or caminho_arquivo

        if caminho_saida:
            try:
                Path(caminho_destino).parent.mkdir(parents=True, exist_ok=True)
                with open(caminho_destino, "w", encoding="utf-8") as f:
                    f.write(conteudo_original)
            except Exception as e:
                return False, f"Erro ao preparar arquivo de saída {caminho_destino}: {e}"

        caminho_relativo = caminho_arquivo.replace("\\", "/")

        prompt_v2 = f"""ARQUIVO ATUAL ({caminho_relativo}):
{conteudo_original}

TAREFA: {prompt_inicial}

REGRAS:
1. Retorne o ARQUIVO COMPLETO com as mudanças aplicadas
2. Use formato: LINHA 001: conteúdo
3. Inclua TODAS as linhas, mesmo as que não mudam
4. NÃO escreva explicações, SÓ o arquivo

EXEMPLO:
LINHA 001: def hello():
LINHA 002:     print("oi")

SUA RESPOSTA:"""

        print("Aguardando resposta da IA...")
        try:
            resposta_ia = callback_ia(conteudo_original, prompt_v2)
            print(f"Resposta recebida: {len(resposta_ia)} caracteres")
        except Exception as e:
            return False, f"Erro ao chamar a IA: {e}"

        if resposta_ia.strip().upper() == "SEM_MUDANCAS":
            print("Nenhuma mudança necessária")
            return True, "Arquivo não modificado"

        linhas_novas = self._extrair_linhas_resposta(resposta_ia)

        if not linhas_novas:
            return False, f"Não foi possível extrair conteúdo da resposta: {resposta_ia[:200]}"

        novo_conteudo = '\n'.join(linhas_novas)

        if validar_sintaxe_python and caminho_arquivo.lower().endswith(".py"):
            sintaxe_ok, erro_sintaxe = self._validar_sintaxe_python(
                novo_conteudo)

            tentativa = 0
            while not sintaxe_ok and tentativa < max_retry_sintaxe:
                tentativa += 1
                print(
                    f"Código Python inválido, tentando correção automática ({tentativa}/{max_retry_sintaxe})...")

                prompt_retry_sintaxe = f"""ARQUIVO ATUAL ({caminho_relativo}):
{conteudo_original}

TAREFA: {prompt_inicial}

A resposta anterior gerou ERRO DE SINTAXE PYTHON:
{erro_sintaxe}

REGRAS:
1. Retorne o ARQUIVO COMPLETO corrigido
2. Use formato: LINHA 001: conteúdo
3. Preserve indentação Python correta
4. NÃO escreva explicações, SÓ o arquivo

SUA RESPOSTA:"""

                try:
                    resposta_retry = callback_ia(
                        conteudo_original, prompt_retry_sintaxe)
                    print(
                        f"Resposta de correção recebida: {len(resposta_retry)} caracteres")
                except Exception as e:
                    return False, f"Erro ao chamar a IA no retry de sintaxe: {e}"

                linhas_retry = self._extrair_linhas_resposta(resposta_retry)
                if not linhas_retry:
                    continue

                linhas_novas = linhas_retry
                novo_conteudo = '\n'.join(linhas_novas)
                sintaxe_ok, erro_sintaxe = self._validar_sintaxe_python(
                    novo_conteudo)

            if not sintaxe_ok:
                return False, f"Código Python inválido após correção automática: {erro_sintaxe}"

        print(f"Extraídas {len(linhas_novas)} linhas da resposta")

        diff = self._gerar_diff(
            conteudo_original, novo_conteudo, caminho_relativo)

        print(f"Diff gerado automaticamente ({len(diff)} caracteres)")
        print(f"Primeiras 200 chars do diff: {diff[:200]}")

        is_valid, validation_msg = self.diff_editor.validate_diff(
            diff, caminho_destino)

        if not is_valid:
            print(f"Diff gerado é inválido: {validation_msg}")
            print(f"Tentando fallback direto...")

            try:
                with open(caminho_destino, "w", encoding="utf-8") as f:
                    f.write('\n'.join(linhas_novas))
                print("Arquivo atualizado diretamente (fallback)")
                return True, f"Arquivo editado com sucesso (fallback): {caminho_destino}"
            except Exception as e:
                return False, f"Falhou diff e fallback: {e}"

        print(f"Aplicando diff...")
        try:
            success, apply_msg = self.diff_editor.apply_diff(
                caminho_destino, diff)
            print(f"Diff aplicado com sucesso: {apply_msg}")
            return True, f"Arquivo editado com sucesso: {caminho_destino}"
        except Exception as e:
            # Ultimate fallback
            print(f"Erro ao aplicar diff: {e}")
            print(f"Tentando escrever diretamente...")
            try:
                with open(caminho_destino, "w", encoding="utf-8") as f:
                    f.write('\n'.join(linhas_novas))
                print("Arquivo atualizado diretamente (ultimate fallback)")
                return True, f"Arquivo editado com sucesso (fallback): {caminho_destino}"
            except Exception as e2:
                return False, f"Erro ao aplicar diff e fallback: {e2}"

    @staticmethod
    def _validar_sintaxe_python(codigo: str) -> Tuple[bool, str]:
        try:
            compile(codigo, "<generated>", "exec")
            return True, "ok"
        except SyntaxError as e:
            linha = e.lineno if e.lineno is not None else "?"
            coluna = e.offset if e.offset is not None else "?"
            return False, f"linha {linha}, coluna {coluna}: {e.msg}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _extrair_linhas_resposta(resposta: str) -> List[str]:
        linhas = []

        pattern = re.compile(r'^LINHA\s*\d+:\s?(.*)$', re.MULTILINE)
        matches = pattern.findall(resposta)

        if matches:
            for match in pattern.finditer(resposta):
                linhas.append(match.group(1))
            return linhas

        lines = resposta.split('\n')
        resultado = []
        dentro_codigo = False

        for line in lines:
            if line.strip().startswith('```'):
                dentro_codigo = not dentro_codigo
                continue
            if dentro_codigo:
                resultado.append(line)

        if resultado:
            return resultado

        return [l for l in lines if l.strip() and not l.startswith('#') and '---' not in l and '+++' not in l]

    @staticmethod
    def _gerar_diff(original: str, novo: str, caminho: str) -> str:

        from difflib import unified_diff

        original_lines = original.splitlines()
        novo_lines = novo.splitlines()

        diff_generator = unified_diff(
            original_lines,
            novo_lines,
            fromfile=f'a/{caminho}',
            tofile=f'b/{caminho}',
            lineterm=''
        )

        diff = '\n'.join(diff_generator)

        if not diff.strip():
            return ''

        return diff

   

    def _corrigir_contagem_hunk(self, diff_text: str, caminho_arquivo: str) -> Optional[str]:

        import re
        lines = diff_text.splitlines(keepends=False)
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if line.startswith("@@"):
                match = re.search(
                    r"@@\s*-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s*@@", line)
                if match:
                    old_start = int(match.group(1))
                    new_start = int(match.group(3))

                    i += 1
                    hunk_lines = []
                    while i < len(lines) and not lines[i].startswith("@@"):
                        hunk_lines.append(lines[i])
                        i += 1

                    old_count = sum(
                        1 for l in hunk_lines if l.startswith(("-", " ")))
                    new_count = sum(
                        1 for l in hunk_lines if l.startswith(("+", " ")))

                    if old_count > 0:
                        new_header = f"@@ -{old_start},{old_count} +{new_start},{new_count} @@"
                        result.append(new_header)
                        result.extend(hunk_lines)
                        continue

            result.append(line)
            i += 1

        if result:
            return "\n".join(result)
        return None

    @staticmethod
    def _contar_linhas_arquivo(caminho: str) -> int:
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except:
            return 0


def get_io_bytes(caminho):
    try:
        if caminho:
            with open(caminho, "rb") as f:
                blob = f.read()
            return io.BytesIO(blob)
    except Exception as e:
        print(e)
        pass


if __name__ == "__main__":
    print(selecionar_arquivo())
