from textual import events
from textual.app import App
from textual.binding import Binding
from database import shelve
from model.modelo import Modelo
from textual.color import Color
from view import chat, config, models, skills
from util.comandos import comandos_str

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
    CURRENT_DIRECTORY = "C:/Users/dudua/Music/Projetos/lllm-tui/skills/diagramas/"
    SKILLS = {
        "astah_uml_class": open(CURRENT_DIRECTORY + "astah/uml_class.md", "r", encoding="utf-8").read(),
        "astah_uml_sequence": open(CURRENT_DIRECTORY + "astah/uml_sequence.md", "r", encoding="utf-8").read(),
        "astah_uml_use_case": open(CURRENT_DIRECTORY + "astah/uml_use_case.md", "r", encoding="utf-8").read(),
        "brmodelo_conceitual": open(CURRENT_DIRECTORY + "brmodelo/conceitual.md", "r", encoding="utf-8").read(),
        "brmodelo_logico": open(CURRENT_DIRECTORY + "brmodelo/logico.md", "r", encoding="utf-8").read(),
    }

    SYSTEM_PROMPT = open("skills/system_prompt.md", "r", encoding="utf-8").read()

    SCREENS = {
        "inicio": chat.ChatScreen,
        "config": config.ConfigScreen,
        "skills": skills.SkillsScreen,
        "models": models.ModelsScreen,
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
