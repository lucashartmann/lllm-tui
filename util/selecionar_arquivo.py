import tkinter as tk
from tkinter import filedialog


def selecionar_arquivo():
    try:
        root = tk.Tk()
        root.withdraw()

        caminhos = filedialog.askopenfilenames(
            title="Selecione",
            filetypes=(
                ("Todos os arquivos", "*.*"),
            )

        )

        caminhos = list(caminhos)

        root.destroy()
        return caminhos
    except Exception as e:
        print(e)
        pass

if __name__ == "__main__":
    print(selecionar_arquivo())
