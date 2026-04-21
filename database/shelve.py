from pathlib import Path
import shelve


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = str(DATA_DIR / "modelo.db")


def _ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with shelve.open(DB_PATH) as db:
        db.setdefault("modelo", "")


_ensure_db()

def salvar_modelo(modelo):
    _ensure_db()
    with shelve.open(DB_PATH) as db:
        db['modelo'] = modelo
        print("Modelo salvo no banco de dados com sucesso!")
        print(db['modelo'])
        
def carregar_modelo():
    _ensure_db()
    with shelve.open(DB_PATH) as db:
        modelo = db.get('modelo', "")
        print(f"Modelo carregado do banco de dados: {modelo}")
        if modelo:
            return modelo
        return ""