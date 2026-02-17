from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import io
import base64
import re
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from pathlib import Path

arquivos = [
    ("Code", "*.py *.js *.html *.css *.tcss *.cpp"),
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

        converter = DocumentConverter()
        result = converter.convert(temp_md)

        document = result.document

        chunker = HybridChunker()
        chunks = list(chunker.chunk(document))

        temp_md.unlink(missing_ok=True)

        return [chunk.text for chunk in chunks]

    except Exception as e:
        print("Erro ao gerar chunks:", e)
        return []


def get_chunks_documento(caminho_arquivo: str):

    try:
        if not caminho_arquivo:
            return []

        converter = DocumentConverter()
        result = converter.convert(caminho_arquivo)
        doc = result.document

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
                    conteudo += f"linha {index}. " + linha + "\n"
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


def aplicar_diff_manual(caminho, diff):
    if not caminho:
        print(f"Erro: caminho vazio")
        return False

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        diff_lines = diff.splitlines()
        i = 0

        while i < len(diff_lines):
            if diff_lines[i].startswith("@@"):
                m = re.search(
                    r"\-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?", diff_lines[i])

                if not m:
                    print(f"Erro ao parsear linha hunk: {diff_lines[i]}")
                    i += 1
                    continue

                start_line = int(m.group(1)) - 1
                original_count = int(m.group(2)) if m.group(2) else 1

                i += 1
                new_lines = []

                while i < len(diff_lines) and not diff_lines[i].startswith("@@"):
                    linha = diff_lines[i]

                    if linha.startswith("+"):
                        new_lines.append(linha[1:] + "\n")
                    elif linha.startswith("-"):
                        pass
                    elif linha.startswith(" "):
                        new_lines.append(linha[1:] + "\n")
                    else:
                        print(
                            f"Aviso: linha sem prefixo válido: {repr(linha)}")

                    i += 1

                linhas[start_line:start_line + original_count] = new_lines
                print(
                    f"Aplicado hunk: removidas {original_count} linhas em {start_line}, adicionadas {len(new_lines)}")
            else:
                i += 1

        with open(caminho, "w", encoding="utf-8") as f:
            f.writelines(linhas)

        print(f"Sucesso: diff aplicado em {caminho}")
        return True

    except Exception as e:
        print(f"Erro ao aplicar diff: {type(e).__name__}: {e}")
        return False


def parse_diff(diff_text: str):
    try:
        file_path = None
        hunks = []

        lines = diff_text.splitlines()

        for line in lines:
            if line.startswith("+++ "):
                file_path = line.replace("+++ ", "").replace("b/", "").strip()

            elif line.startswith("@@"):
                match = re.search(r"\+(\d+),?(\d+)?", line)
                start = int(match.group(1)) - 1
                hunks.append({"start": start, "lines": []})

            elif hunks:
                hunks[-1]["lines"].append(line)

        return file_path, hunks
    except Exception as e:
        print(e)
        pass


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
