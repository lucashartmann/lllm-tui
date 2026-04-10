from textual.app import App
from textual.screen import Screen
from textual.widgets import Tabs, Tab, ListView, ListItem, Checkbox, Static
from textual.containers import Grid, Container
from model.modelo import Modelo


class ModelsScreen(Screen):

    CSS_PATH = ["css/base.tcss", "css/models.tcss"]

    async def carregar_modelos(self):
        modelos = self.modelo.listar_nome_modelos()
        detalhes = []

        if modelos:
            for modelo in modelos:
                info = self.modelo._show_model_info2(modelo)
                info["name"] = modelo
                detalhes.append(info)
                print(info)

        if detalhes != self.modelos and detalhes:
            self.modelos = detalhes

        if not self.modelos and detalhes:
            self.query_one(ListView).append(
                ListItem(Static("Nenhum modelo encontrado")))
            return

        if not detalhes:
            return

        if self.modelos:
            for modelo in self.modelos:
                container = Container()
                item = ListItem(container)
                self.query_one(ListView).append(item)
                item.mount(container)
                if "name" in modelo.keys():
                    container.mount(
                        Static(f"Nome: {str(modelo['name'])}", id="modelo_nome"))
                if "contexto" in modelo.keys():
                    container.mount(
                        Static(f"Contexto: {str(modelo['contexto'])}", id="modelo_contexto"))
                if "capabilidades" in modelo.keys():
                    container.mount(Static(
                        f"Capabilidades: {str(modelo['capabilidades'])}", id="modelo_capabilidades"))
                if "parametros" in modelo.keys():
                    container.mount(
                        Static(f"Parâmetros: {str(modelo['parametros'])}", id="modelo_parametros"))
                if "quantizacao" in modelo.keys():
                    container.mount(
                        Static(f"Quantização: {str(modelo['quantizacao'])}", id="modelo_quantizacao"))
                # if modelo["completion"]:
                #     container.mount(Static(f"Completion: {str(modelo['completion'])}"))
                # if modelo["insert"]:
                #     container.mount(Static(f"Insert: {str(modelo['insert'])}"))
                # if modelo["arquitetura"]:
                #     container.mount(Static(str(modelo["arquitetura"])))
                if "embedding" in modelo.keys():
                    container.mount(
                        Static(f"Embedding: {str(modelo['embedding'])}", id="modelo_embedding"))
                if "layers" in modelo.keys():
                    container.mount(
                        Static(f"Layers: {str(modelo['layers'])}", id="modelo_layers"))

    def __init__(self, name=None, id=None, classes=None):
        super().__init__(name, id, classes)
        self.modelo = Modelo()
        self.modelos = []

    def on_screen_resume(self, event):
        self.query_one(Tabs).active = self.query_one(
            "#tab_models", Tab).id

        self.run_worker(
            self.carregar_modelos,
            name="Carregando modelos do Ollama",
            thread=False,
            exclusive=True,
        )

        if self.app.modelo.modelo:
            for item in self.query(ListItem):
                nome = item.query_one(
                    "#modelo_nome", Static).content.replace("Nome: ", "")
                if nome == self.app.modelo.modelo:
                    item.add_class("modelo-selecionado")
                else:
                    item.remove_class("modelo-selecionado")

    def compose(self):
        yield Tabs(Tab("Chat", id="tab_chat"), Tab("Configuração", id="tab_config"), Tab("Skills", id="tab_skills"), Tab("Modelos", id="tab_models"))
        yield ListView()

    def on_list_view_selected(self, event: ListView.Selected):
        if self.app.modelo.modelo:
            for item in self.query(ListItem):
                nome = item.query_one(
                    "#modelo_nome", Static).content.replace("Nome: ", "")
                if nome == self.app.modelo.modelo:
                    item.remove_class("modelo-selecionado")
        item = event.item
        if item is None:
            return
        nome_modelo = item.query_one(
            "#modelo_nome", Static).content.replace("Nome: ", "")
        self.app.modelo.set_modelo(nome_modelo)
        item.add_class("modelo-selecionado")
        self.app.notify(f"Modelo '{nome_modelo}' selecionado.")

    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        try:
            if event.tabs.active == self.query_one("#tab_config", Tab).id:
                self.app.switch_screen("config")
            elif event.tabs.active == self.query_one("#tab_skills", Tab).id:
                self.app.switch_screen("skills")
            elif event.tabs.active == self.query_one("#tab_chat", Tab).id:
                self.app.switch_screen("inicio")
        except:
            pass
