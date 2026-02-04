from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import io
from enum import Enum
import base64

arquivos = [
    ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff"),
    ("Documentos", "*.pdf *.txt *.doc *.docx *.xls *.xlsx *.ppt *.pptx *.odt *.ods *.odp"),
    ("Code", "*.py")
]


def encode_image(image_path):
    return base64.b64encode(Path(image_path).read_bytes()).decode()

def get_conteudo(caminho):
    with open(file=caminho, mode="r") as arquivo:
        conteudo = arquivo.read()

    return conteudo


def selecionar_arquivo():
    root = tk.Tk()
    root.withdraw()

    caminhos = filedialog.askopenfilenames(
        title="Selecione",
        filetypes=arquivos
    )

    root.destroy()
    return caminhos


def get_bytes(caminho):
    with open(caminho, "rb") as f:
        return f.read()


def get_io_bytes(caminho):
    with open(caminho, "rb") as f:
        blob = f.read()
    return io.BytesIO(blob)


if __name__ == "__main__":
    print(selecionar_arquivo())
