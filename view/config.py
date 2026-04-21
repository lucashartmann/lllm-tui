from textual.screen import Screen
from textual.widgets import Checkbox, Static
from textual.containers import Vertical, Grid, VerticalScroll, Horizontal, HorizontalGroup
from textual.widgets import Button, Input, Select, Tabs, Tab, Footer, MaskedInput
from tools import diagrama, internet
from textual_colorpicker import ColorPicker

class ConfigScreen(Screen):

    CSS_PATH = ["css/base.tcss", "css/config.tcss"]

    def on_screen_resume(self):
        self.query_one(Tabs).active = self.query_one(
            "#tab_config", Tab).id
        # TODO: carregar dados do modelo

    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        try:
            if event.tabs.active == self.query_one("#tab_chat", Tab).id:
                self.app.switch_screen("inicio")
            elif event.tabs.active == self.query_one("#tab_skills", Tab).id:
                self.app.switch_screen("skills")
            elif event.tabs.active == self.query_one("#tab_models", Tab).id:
                self.app.switch_screen("models")
        except:
            pass

    def compose(self):
        yield Tabs(Tab("Chat", id="tab_chat"), Tab("Configuração", id="tab_config"), Tab("Skills", id="tab_skills"), Tab("Modelos", id="tab_models"))
        yield Static("Nome do bot")
        yield Input(placeholder="nome do bot", value="bot", id="input_nome_bot")
        yield Static("Seu nome")
        yield Input(placeholder="seu nome", id="input_nome_user")
        yield Static("Cor do bot")
        yield ColorPicker()
        
        with Grid(id="grid_config"):
            yield Static("Temperatura")
            yield MaskedInput(placeholder="temperatura", template="0.0", id="input_temperatura")
            yield Static("Máximo de tokens")
            yield MaskedInput(placeholder="máximo de tokens", template="0000", id="input_max_tokens")
            yield Static("Top P")
            yield MaskedInput(placeholder="top_p", template="0.0", id="input_top_p")
            yield Static("Num Keep")
            yield MaskedInput(placeholder="num_keep", template="5", id="input_num_keep")
            yield Static("Seed")
            yield MaskedInput(placeholder="seed", template="42", id="input_seed")
            yield Static("Num Predict")
            yield MaskedInput(placeholder="num_predict", template="100", id="input_num_predict")
            yield Static("Top K")
            yield MaskedInput(placeholder="top_k", template="20", id="input_top_k")
            yield Static("Min P")
            yield MaskedInput(placeholder="min_p", template="0.0", id="input_min_p")
            yield Static("Typical P")
            yield MaskedInput(placeholder="typical_p", template="0.7", id="input_typical_p")
            yield Static("Repeat Last N")
            yield MaskedInput(placeholder="repeat_last_n", template="33", id="input_repeat_last_n")
            yield Static("Repeat Penalty")
            yield MaskedInput(placeholder="repeat_penalty", template="1.2", id="input_repeat_penalty")
            yield Static("Presence Penalty")
            yield MaskedInput(placeholder="presence_penalty", template="1.5", id="input_presence_penalty")
            yield Static("Frequency Penalty")
            yield MaskedInput(placeholder="frequency_penalty", template="1.0", id="input_frequency_penalty")
            yield Static("Penalize Newline")
            yield MaskedInput(placeholder="stop", template='["\\n", "user:"]', id="input_stop")
            yield Static("Numa")
            yield MaskedInput(placeholder="numa", template="false", id="input_numa")
            yield Static("Context Size")
            yield MaskedInput(placeholder="num_ctx", template="1024", id="input_num_ctx")
            yield Static("Batch Size")
            yield MaskedInput(placeholder="num_batch", template="2", id="input_num_batch")
            yield Static("Number of GPUs")
            yield MaskedInput(placeholder="num_gpu", template="1", id="input_num_gpu")
            yield Static("Main GPU")
            yield MaskedInput(placeholder="main_gpu", template="0", id="input_main_gpu")
            yield Static("Use Mmap")
            yield MaskedInput(placeholder="use_mmap", template="true", id="input_use_mmap")
            yield Static("Num Thread")
            yield MaskedInput(placeholder="num_thread", template="8", id="input_num_thread")

    
    def on_color_picker_changed(self, evento: ColorPicker.Changed):
        self.app.cor_bot = evento.color_picker.color

    async def on_button_pressed(self, evento: Button.Pressed):
        match evento.button.id:
            case "recarregar":
                self.run_worker(
                    self.carregar_modelos,
                    name="Carregando modelos do Ollama",
                    thread=True,
                    exclusive=True,
                )
        
    def on_input_changed(self, evento: Input.Changed):
        match evento.input.id:
            case "input_nome_bot":
                self.app.nome_bot = evento.input.value
            case "input_nome_user":
                self.app.nome_user = evento.input.value
            case "input_temperatura":
                self.app.modelo.set_temperatura(float(evento.input.value))
            case "input_max_tokens":
                self.app.modelo.set_max_tokens(int(evento.input.value))
            case "input_top_p":
                self.app.modelo.set_top_p(float(evento.input.value))
            case "input_num_keep":
                self.app.modelo.set_num_keep(int(evento.input.value))
            case "input_seed":
                self.app.modelo.set_seed(int(evento.input.value))
            case "input_num_predict":
                self.app.modelo.set_num_predict(int(evento.input.value))
            case "input_top_k":
                self.app.modelo.set_top_k(int(evento.input.value))
            case "input_min_p":
                self.app.modelo.set_min_p(float(evento.input.value))
            case "input_typical_p":
                self.app.modelo.set_typical_p(float(evento.input.value))
            case "input_repeat_last_n":
                self.app.modelo.set_repeat_last_n(int(evento.input.value))
            case "input_repeat_penalty":
                self.app.modelo.set_repeat_penalty(float(evento.input.value))
            case "input_presence_penalty":
                self.app.modelo.set_presence_penalty(float(evento.input.value))
            case "input_frequency_penalty":
                self.app.modelo.set_frequency_penalty(float(evento.input.value))
            case "input_stop":
                self.app.modelo.set_stop(eval(evento.input.value))

        self.app.config = f'''
            Config:
            - seu nome: {self.app.nome_bot}
            - nome do user: {self.app.nome_user}
            Responda usando o idioma da mensagem a seguir:\n
            '''
