import re
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from difflib import unified_diff


class DiffValidationError(Exception):
    pass


class DiffApplicationError(Exception):
    pass


class DiffEditor:

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.log_buffer: List[str] = []

    def _log(self, message: str):
        if self.verbose:
            print(message)
        self.log_buffer.append(message)

    def get_logs(self) -> str:
        return "\n".join(self.log_buffer)

    def clear_logs(self):
        self.log_buffer.clear()

    @staticmethod
    def clean_diff(diff_text: str, file_path: str = None) -> str:

        lines = diff_text.splitlines(keepends=False)
        result = []
        in_code_block = False
        found_header_a = False
        found_header_b = False
        has_hunks = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue

            if line.startswith("@@"):
                has_hunks = True

            if in_code_block:
                if any(line.startswith(c) for c in ['+', '-', ' ', '@@', '---', '+++']):
                    line = DiffEditor._convert_vazio_to_empty(line)
                    result.append(line)
                continue

            if line.startswith("---") and not line.startswith("---"):
                result.append(line)
                found_header_a = True
                continue

            if line.startswith("+++") and not line.startswith("+++"):
                result.append(line)
                found_header_b = True
                continue

            if line.startswith("--- "):
                result.append(line)
                found_header_a = True
                continue

            if line.startswith("+++ "):
                result.append(line)
                found_header_b = True
                continue

            if line.startswith("diff --git"):
                continue
            if line.startswith("index "):
                continue
            if line.startswith("Binary"):
                continue

            line = DiffEditor._convert_vazio_to_empty(line)

            result.append(line)

        if result:
            result = DiffEditor._remove_empty_hunks(result)

        if has_hunks and (not found_header_a or not found_header_b):
            result_str = "\n".join(result)

            if "--- " not in result_str and "+++ " not in result_str:
                if file_path:
                    file_name = file_path.replace("\\", "/")
                else:
                    file_name = "file"

                result.insert(0, f"+++ b/{file_name}")
                result.insert(0, f"--- a/{file_name}")

        return "\n".join(result)

    @staticmethod
    def _convert_vazio_to_empty(line: str) -> str:
        if line.startswith('-') and '[VAZIO]' in line:
            return '-'
        elif line.startswith('+') and '[VAZIO]' in line:
            return '+'
        elif line.startswith(' ') and '[VAZIO]' in line:
            return ' '
        return line

    @staticmethod
    def _remove_empty_hunks(lines: List[str]) -> List[str]:
        result = []
        i = 0

        while i < len(lines):
            if not lines[i].startswith("@@"):
                result.append(lines[i])
                i += 1
                continue

            hunk_start = i
            hunk_lines = [lines[i]]
            i += 1

            has_changes = False
            while i < len(lines) and not lines[i].startswith("@@"):
                hunk_lines.append(lines[i])
                if lines[i].startswith(("+", "-")) and not lines[i].startswith(("+++", "---")):
                    has_changes = True
                i += 1

            if has_changes:
                result.extend(hunk_lines)

        return result

    @staticmethod
    def extract_file_path(diff_text: str) -> Optional[str]:
        lines = diff_text.splitlines()

        for line in lines:
            if line.startswith("+++ "):
                path = line[4:].replace("b/", "").strip()
                if not Path(path).is_absolute():
                    path = str((Path.cwd() / path).resolve())
                return path

        return None

    @staticmethod
    def parse_hunks(diff_text: str) -> List[Dict]:

        lines = diff_text.splitlines(keepends=False)
        hunks = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if line.startswith("@@"):
                m = re.search(
                    r"@@ -(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s*@@", line)
                if m:
                    old_start = int(m.group(1)) - 1
                    old_count = int(m.group(2)) if m.group(2) else 1
                    new_start = int(m.group(3)) - 1
                    new_count = int(m.group(4)) if m.group(4) else 1

                    hunk = {
                        "old_start": old_start,
                        "old_count": old_count,
                        "new_start": new_start,
                        "new_count": new_count,
                        "lines": []
                    }

                    i += 1
                    while i < len(lines) and not lines[i].startswith("@@"):
                        hunk["lines"].append(lines[i])
                        i += 1

                    hunks.append(hunk)
                    continue

            i += 1

        return hunks

    def validate_diff(self, diff_text: str, file_path: Optional[str] = None) -> Tuple[bool, str]:

        if not diff_text or not diff_text.strip():
            return False, "Diff vazio"

        clean_text = self.clean_diff(diff_text, file_path)

        if not clean_text or not clean_text.strip():
            return False, "Diff vazio após limpeza"

        lines = clean_text.splitlines()

        count_header_a = sum(1 for l in lines if l.startswith(
            "---") and not l.startswith("--- "))
        count_header_b = sum(1 for l in lines if l.startswith(
            "+++") and not l.startswith("+++ "))

        headers_a = [l for l in lines if l.startswith(
            "--- a/") or l.startswith("--- ")]
        headers_b = [l for l in lines if l.startswith(
            "+++ b/") or l.startswith("+++ ")]

        if not headers_a or not headers_b:
            return False, "Diff faltam headers (--- a/... e +++ b/...)"

        if len(headers_a) > 1 or len(headers_b) > 1:
            return False, f"Diff tem múltiplos headers - gere UM ÚNICO diff! (encontrou {len(headers_a)} '---' e {len(headers_b)} '+++')"

        tem_mudancas = any(l.lstrip().startswith(("+", "-"))
                           and not l.startswith(("+++", "---")) for l in lines)

        if not tem_mudancas:
            preview = "\n".join(lines[:10])
            return False, f"Diff não contém mudanças (sem + ou -)\n\nPrimeiras linhas:\n{preview}"

        try:
            hunks = self.parse_hunks(clean_text)
            if not hunks:
                preview = "\n".join(lines[:15])
                return False, f"Nenhum hunk encontrado (formato inválido?)\n\nDiff recebido:\n{preview}"

            for i, hunk in enumerate(hunks):
                hunk_lines = hunk["lines"]

                old_lines_in_hunk = sum(
                    1 for l in hunk_lines if l.startswith(("-", " ")))
                new_lines_in_hunk = sum(
                    1 for l in hunk_lines if l.startswith(("+", " ")))
                lines_com_mudancas = [
                    l for l in hunk_lines if l.startswith(("+", "-"))]

                if not lines_com_mudancas and hunk["old_count"] > 0:
                    return False, f"Hunk {i+1}: tem {hunk['old_count']} linhas antigas mas nenhuma mudança (+ ou -)"

                if old_lines_in_hunk != hunk["old_count"]:
                    preview = "\n".join(hunk_lines[:10])
                    return False, f"Hunk {i+1}: header diz {hunk['old_count']} linhas antigas, mas hunk contém {old_lines_in_hunk} linhas\n\nConteúdo do hunk:\n{preview}"

                if new_lines_in_hunk != hunk["new_count"]:
                    preview = "\n".join(hunk_lines[:10])
                    return False, f"Hunk {i+1}: header diz {hunk['new_count']} linhas novas, mas hunk contém {new_lines_in_hunk} linhas\n\nConteúdo do hunk:\n{preview}"
        except Exception as e:
            return False, f"Erro ao parsear hunks: {e}"

        if file_path and not os.path.exists(file_path):
            return False, f"Arquivo não existe: {file_path}"

        return True, "Diff válido"

    @staticmethod
    def normalize_line(line: str) -> str:
        line = re.sub(r"^linha\s+\d+\.\s*", "", line)

        line = re.sub(r"^\s*\d+\s*\|\s*", "", line)

        if line.strip() == "[VAZIO]" or line.strip() == "":
            return "\n"

        return line.rstrip() + "\n"

    def apply_diff(self, file_path: str, diff_text: str) -> Tuple[bool, str]:

        self._log(f"\n{'='*60}")
        self._log(f"Aplicando diff em: {file_path}")
        self._log(f"{'='*60}")

        clean_diff = self.clean_diff(diff_text, file_path)

        self._log(f"\nDiff recebido (primeiros 300 chars):")
        self._log(diff_text[:300])
        self._log(f"\nDiff após limpeza (primeiros 300 chars):")
        self._log(clean_diff[:300])

        is_valid, validation_msg = self.validate_diff(clean_diff, file_path)
        if not is_valid:
            error_msg = f"Diff inválido: {validation_msg}"
            self._log(f"\nERRO: {error_msg}")
            raise DiffValidationError(error_msg)

        if not os.path.exists(file_path):
            error_msg = f"Arquivo não existe: {file_path}"
            self._log(f"\nERRO: {error_msg}")
            raise DiffApplicationError(error_msg)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_lines = f.readlines()
            self._log(
                f"\nArquivo lido com sucesso: {len(original_lines)} linhas")
        except Exception as e:
            error_msg = f"Erro ao ler arquivo: {e}"
            self._log(f"\nERRO: {error_msg}")
            raise DiffApplicationError(error_msg)

        hunks = self.parse_hunks(clean_diff)

        if not hunks:
            error_msg = "Nenhum hunk encontrado após limpar diff"
            self._log(f"\nERRO: {error_msg}")
            self._log(f"Diff após limpeza:\n{clean_diff}")
            raise DiffValidationError(error_msg)

        self._log(f"Encontrados {len(hunks)} hunk(s)")

        modified_lines = original_lines.copy()
        offset = 0
        applied_hunks = 0

        for hunk_idx, hunk in enumerate(hunks):
            self._log(f"\nProcessando hunk {hunk_idx + 1}:")
            self._log(
                f"  Old: {hunk['old_start']}, Count: {hunk['old_count']}")
            self._log(
                f"  New: {hunk['new_start']}, Count: {hunk['new_count']}")

            try:
                success = self._apply_hunk(
                    modified_lines, hunk, offset, hunk_idx
                )
                if not success:
                    self._log(f"  Tentando fallback: aplicação linha por linha")
                    success = self._apply_hunk_fallback(
                        modified_lines, hunk, offset, hunk_idx
                    )
                    if success:
                        self._log(f"Fallback bem-sucedido")
                    else:
                        self._log(
                            f"SKIPPED: Hunk {hunk_idx + 1} não foi aplicado (linhas não encontradas)")
                        self._log(f"Continuando com próximos hunks...")
                        continue

                offset += (hunk['new_count'] - hunk['old_count'])
                applied_hunks += 1
                self._log(f"Hunk aplicado, novo offset: {offset}")

            except Exception as e:
                error_msg = f"Erro ao processar hunk {hunk_idx + 1}: {e}"
                self._log(f"  ERRO: {error_msg}")
                raise DiffApplicationError(error_msg)

        if applied_hunks == 0:
            error_msg = "Nenhum hunk pôde ser aplicado"
            self._log(f"\nERRO: {error_msg}")
            raise DiffApplicationError(error_msg)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(modified_lines)
            self._log(
                f"\nArquivo salvo com sucesso: {len(modified_lines)} linhas")
            self._log(f"{'='*60}\n")
            return True, "Diff aplicado com sucesso"

        except Exception as e:
            error_msg = f"Erro ao salvar arquivo: {e}"
            self._log(f"ERRO: {error_msg}")
            raise DiffApplicationError(error_msg)

    def _apply_hunk(self, lines: List[str], hunk: Dict, offset: int, hunk_idx: int) -> bool:

        old_start = hunk['old_start'] + offset
        old_count = hunk['old_count']
        hunk_lines = hunk['lines']

        added_lines = []

        for line in hunk_lines:
            if line.startswith("+"):
                added_lines.append(self.normalize_line(line[1:]))
            elif line.startswith(" "):
                added_lines.append(self.normalize_line(line[1:]))

        if old_start < 0 or old_start + old_count > len(lines):
            self._log(
                f"Índice fora dos limites: start={old_start}, count={old_count}, total={len(lines)}")
            return False

        current_block = lines[old_start:old_start + old_count]

        current_normalized = [self.normalize_line(l) for l in current_block]

        expected_block = []
        for line in hunk_lines:
            if line.startswith("-") or line.startswith(" "):
                expected_block.append(self.normalize_line(line[1:]))

        if current_normalized == expected_block:
            self._log(f"Bloco encontrado na posição esperada")
            lines[old_start:old_start + old_count] = added_lines
            return True

        for search_idx in range(len(lines) - old_count + 1):
            block_at_idx = lines[search_idx:search_idx + old_count]
            block_normalized = [self.normalize_line(l) for l in block_at_idx]

            if block_normalized == expected_block:
                self._log(
                    f"Bloco encontrado em posição diferente: {search_idx} (esperado {old_start})")
                lines[search_idx:search_idx + old_count] = added_lines
                return True

        self._log(f"Bloco não encontrado exatamente")
        return False

    def _apply_hunk_fallback(self, lines: List[str], hunk: Dict, offset: int, hunk_idx: int) -> bool:

        removed_lines = []
        added_lines = []

        for line in hunk['lines']:
            if line.startswith("-"):
                removed_lines.append(self.normalize_line(line[1:]))
            elif line.startswith("+"):
                added_lines.append(self.normalize_line(line[1:]))

        if not removed_lines and not added_lines:
            return True

        self._log(
            f"Fallback: {len(removed_lines)} removidas, {len(added_lines)} adicionadas")

        if hunk['new_count'] == 0 and added_lines:
            self._log(
                f"Diff diz 0 linhas novas mas tem linhas +. Removendo todas as antigas.")
            removed_lines = added_lines + removed_lines
            added_lines = []

        lines_to_remove = []
        for removed_line in removed_lines:
            if not added_lines or removed_line not in added_lines:
                lines_to_remove.append(removed_line)

        removed_count = 0
        found_any = False
        for line_to_remove in lines_to_remove:
            try:
                idx = lines.index(line_to_remove)
                lines.pop(idx)
                removed_count += 1
                found_any = True
                self._log(
                    f"Removida [{removed_count}]: {repr(line_to_remove.rstrip())}")
            except ValueError:
                removed = False

                if line_to_remove.strip() == "":

                    for i, file_line in enumerate(lines):
                        if file_line.strip() == "":
                            lines.pop(i)
                            removed_count += 1
                            found_any = True
                            self._log(
                                f"Removida [vazia] [{removed_count}]: linha vazia")
                            removed = True
                            break

                if not removed:
                    for i, file_line in enumerate(lines):

                        file_stripped = file_line.strip()
                        remove_stripped = line_to_remove.strip()

                        if remove_stripped and file_stripped:

                            remove_words = set(remove_stripped.split())
                            file_words = set(file_stripped.split())

                            if remove_words and file_words:
                                common = len(remove_words & file_words)
                                similarity = common / \
                                    max(len(remove_words), len(file_words))

                                if similarity >= 0.6:
                                    lines.pop(i)
                                    removed_count += 1
                                    found_any = True
                                    self._log(
                                        f"  Removida [fuzzy] [{removed_count}]: {repr(file_line.rstrip())}")
                                    self._log(
                                        f"    (procurava: {repr(line_to_remove.rstrip())}, similarity={similarity:.0%})")
                                    removed = True
                                    break

                if not removed:
                    self._log(
                        f"Não encontrada: {repr(line_to_remove.rstrip())}")

        if removed_lines:
            if removed_count == 0:
                self._log(
                    f"FALHA CRÍTICA: Hunk tem linhas a remover mas nenhuma foi encontrada!")
                self._log(f"Esperava remover: {removed_lines[:3]}..." if len(
                    removed_lines) > 3 else f"    Esperava remover: {removed_lines}")
                self._log(
                    f"Diff parece estar referenciando conteúdo que não existe no arquivo")
                return False

            if removed_count < len(removed_lines):
                self._log(
                    f"AVISO: Removeu apenas {removed_count}/{len(removed_lines)} linhas esperadas")

                removal_rate = removed_count / len(removed_lines)
                if removal_rate < 0.5:
                    self._log(
                        f"  FALHA: Taxa de remoção muito baixa ({removal_rate:.0%}) - diff não confiável")
                    return False

        if removed_count == 0 and not added_lines:
            self._log(f"FALHA: Nenhuma linha foi removida com sucesso")
            return False

        if not added_lines and removed_count < len(removed_lines):
            self._log(
                f"FALHA: Diff é inválido para aplicação (removed < expected, sem adições)")
            return False

        if added_lines:
            insert_pos = min(hunk['new_start'] + offset, len(lines))
            for i, added_line in enumerate(added_lines):

                if not any(l in added_line or added_line in l for l in removed_lines):
                    lines.insert(insert_pos + i, added_line)
                    self._log(f"  Adicionada: {repr(added_line.rstrip())}")

        return removed_count > 0 or added_lines


def create_diff(original_file: str, modified_content: List[str]) -> str:

    if not os.path.exists(original_file):
        return ""

    with open(original_file, "r", encoding="utf-8") as f:
        original_lines = f.readlines()

    diff_lines = unified_diff(
        original_lines,
        modified_content,
        fromfile=f"a/{original_file}",
        tofile=f"b/{original_file}",
        lineterm=""
    )

    return "\n".join(diff_lines)


__all__ = [
    "DiffEditor",
    "DiffValidationError",
    "DiffApplicationError",
    "create_diff"
]
