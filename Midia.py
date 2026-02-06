from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import io
import base64
import re

arquivos = [
    ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff"),
    ("Documentos", "*.pdf *.txt *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.odt *.ods *.odp"),
    ("Code", "*.py")
]


def encode_image(image_path):
    return base64.b64encode(Path(image_path).read_bytes()).decode()

def get_conteudo(caminho):
        with open(file=caminho, mode="r") as arquivo:
            conteudo = ""
            for index, linha in enumerate(arquivo.readlines(), start=1):
                conteudo += f"linha {index}. " + linha +"\n"
        return conteudo
   

def selecionar_arquivo():
    root = tk.Tk()
    root.withdraw()

    caminhos = filedialog.askopenfilenames(
        title="Selecione",
        filetypes=arquivos
    )
    
    caminhos = list(caminhos)

    root.destroy()
    return caminhos


def get_bytes(caminho):
    with open(caminho, "rb") as f:
        return f.read()
    
    
def aplicar_diff_manual(caminho, diff):
    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    diff_lines = diff.splitlines()
    i = 0

    while i < len(diff_lines):
        if diff_lines[i].startswith("@@"):
            m = re.search(r"\-(\d+)(?:,(\d+))?", diff_lines[i])
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
                
                i += 1

            linhas[start_line:start_line + original_count] = new_lines
        else:
            i += 1

    with open(caminho, "w", encoding="utf-8") as f:
        f.writelines(linhas)
    
def parse_diff(diff_text: str):
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
    
def editar_arquivo(caminho: str, diff_text: str):
    file_path, hunks = parse_diff(diff_text)

    if not hunks:
        return

    with open(caminho, "r", encoding="utf-8") as f:
        content = f.readlines()

    offset = 0

    for hunk in hunks:
        idx = hunk["start"] + offset
        new_lines = []

        for line in hunk["lines"]:
            if line.startswith("+"):
                new_lines.append(line[1:] + "\n")
            elif line.startswith(" "):
                new_lines.append(line[1:] + "\n")
                idx += 1
            elif line.startswith("-"):
                idx += 1

        content[idx - len(new_lines):idx] = new_lines
        offset += len(new_lines)

    with open(caminho, "w", encoding="utf-8") as f:
        f.writelines(content)



def get_io_bytes(caminho):
    with open(caminho, "rb") as f:
        blob = f.read()
    return io.BytesIO(blob)


if __name__ == "__main__":
    print(selecionar_arquivo())
