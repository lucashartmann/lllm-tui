from pathlib import Path

from textual import events
from textual.app import App
from textual.binding import Binding
from database import shelve
from model.modelo import Modelo
from textual.color import Color
from view.chat import ChatScreen
from view.config import ConfigScreen
from view.models import ModelsScreen
from view.skills import SkillsScreen
from util.comandos import comandos_str


BASE_DIRECTORY = Path(__file__).resolve().parents[1]


def read_resource(*parts: str) -> str:
    return BASE_DIRECTORY.joinpath(*parts).read_text(encoding="utf-8")

class App(App):

    modelo = Modelo()
    comandos = str(comandos_str)
    caminhos = list()
    nome_bot = "bot"
    nome_user = None
    cor_bot = Color(0, 128, 0)
    config_str = f'''
    Config:
    - seu nome: {nome_bot}
    - nome do user: {nome_user}
    Responda usando o idioma da mensagem a seguir:\n
    '''
    CURRENT_DIRECTORY = BASE_DIRECTORY / "skills" / "diagramas"
    SKILLS = {
        "astah_uml_class": read_resource("skills", "diagramas", "astah", "uml_class.md"),
        "astah_uml_sequence": read_resource("skills", "diagramas", "astah", "uml_sequence.md"),
        "astah_uml_use_case": read_resource("skills", "diagramas", "astah", "uml_use_case.md"),
        "brmodelo_conceitual": read_resource("skills", "diagramas", "brmodelo", "conceitual.md"),
        "brmodelo_logico": read_resource("skills", "diagramas", "brmodelo", "logico.md"),
    }

    SYSTEM_PROMPT = read_resource("skills", "system_prompt.md")

    SCREENS = {
        "inicio": ChatScreen,
        "config": ConfigScreen,
        "skills": SkillsScreen,
        "models": ModelsScreen,
    }

    BINDINGS = [
        Binding("ctrl+q", "sair", "sair"),
        Binding("ctrl+c", "sair", "sair"),
    ]

    WIDTH_BREAKPOINS = {
        34: "tamanho-34",
        64: "tamanho-64",
        98: "tamanho-98",
        128: "tamanho-128",
        192: "tamanho-192",
    }

    def on_resize(self, event: events.Resize) -> None:
        for cls in self.WIDTH_BREAKPOINS.values():
            self.remove_class(cls)

        for w in sorted(self.WIDTH_BREAKPOINS, reverse=True):
            if event.size.width > w:
                self.add_class(self.WIDTH_BREAKPOINS[w])
                break

    def action_sair(self):
        self.notify("Saindo...")
        if self.modelo.modelo:
            self.modelo.descarregar_modelo()
        self.exit()

    def on_mount(self):
        if shelve.carregar_modelo():
            self.modelo.modelo = shelve.carregar_modelo()
            print(f"Modelo carregado do shelve: {self.modelo.modelo}")
        self.push_screen("inicio")
