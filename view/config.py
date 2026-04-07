from textual.screen import Screen
from textual.widgets import Checkbox
from textual.containers import Vertical, Grid, VerticalScroll, Horizontal, HorizontalGroup
from textual.widgets import Button, Input, Select, Tabs, Tab, Footer, MaskedInput
from model.skills import diagrama, internet
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
        yield Input(placeholder="nome do bot", value="bot", id="input_nome_bot")
        yield Input(placeholder="seu nome", id="input_nome_user")
        yield MaskedInput(placeholder="temperatura", mask="0.0", id="input_temperatura")
        yield MaskedInput(placeholder="máximo de tokens", mask="0000", id="input_max_tokens")
        yield MaskedInput(placeholder="top_p", mask="0.0", id="input_top_p")
        
        yield ColorPicker()
        

    def on_checkbox_changed(self, event: Checkbox.Changed):
        pass

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

    def on_select_changed(self):
        if self.app.modelo.modelo:
            self.app.modelo.unload_model()
        self.app.modelo.set_modelo(self.query_one(Select).value)

    def on_input_changed(self, evento: Input.Changed):
        if evento.input.id == "input_nome_bot":
            self.app.nome_bot = evento.input.value
        else:
            self.app.nome_user = evento.input.value

        self.config = f'''
            Config:
            - seu nome: {self.app.nome_bot}
            - nome do user: {self.app.nome_user}
            Responda usando o idioma da mensagem a seguir:\n
            '''
