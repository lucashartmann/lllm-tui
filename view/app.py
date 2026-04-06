from textual import events
from textual.app import App
from textual.binding import Binding
from model.midia import ChunkedFileProcessor
from model.modelo import Modelo
from textual.color import Color
from view import chat, config, models, skills

class App(App):
    
    modelo = Modelo()
    file_processor = ChunkedFileProcessor()
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
    _stream_started_at = None
    _first_token_latency = None
    _current_response_container = None
    _current_response_widget = None
    lista_skills = []
    
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
            self.modelo.unload_model()
        self.exit()

    def on_mount(self):
            self.push_screen("inicio")