from textual.app import App
from textual.widgets import TextArea, Select, Button, Static, Switch
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll, Center

import Midia
from Modelo import Modelo


class App(App):

    CSS_PATH = "Style.tcss"

    modelo = Modelo()
    caminhos = None

    base = "Responda usando o idioma da mensagem a seguir: \n"

    def compose(self):
        yield Select((modelo, modelo) for modelo in self.modelo.listar_nome_modelos())
        yield VerticalScroll(id="bot")
        with HorizontalGroup(id="hg_user"):
            yield TextArea(id="user")
            with VerticalGroup():
                yield Button("Enviar", id="enviar")
                yield Button("📎", id="anexo")
            with VerticalGroup(id="hg_editar_arquivos"):
                    yield Static("Editar Arquivo:")
                    with Center():
                        yield Switch()

    def on_button_pressed(self, evento: Button.Pressed):
        if self.modelo.modelo and evento.button.id == "enviar":
            mensagem = self.query_one("#user").text
            self.query_one("#bot", VerticalScroll).mount(
                Static(mensagem, classes="user"))
            mensagem = ""
            mensagem = self.base + self.query_one("#user").text
            if self.caminhos:
                conteudo = ""
                imagens = []
                for camingo in self.caminhos:
                    if camingo[-4:] in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"]:
                        imagens.append(Midia.encode_image(camingo))
                    else:
                        conteudo = Midia.get_conteudo(camingo)
            if self.caminhos and conteudo and imagens:
                if self.query_one(Switch).value == True:
                    mensagem = mensagem + "Gere um diff unificado (git diff). Não escreva nada além do diff."
                mensagem = mensagem + "\n" + conteudo
                resposta = self.modelo.enviar_mensagem(
                    mensagem, caminho_image="".join(imagem for imagem in imagens))
            elif self.caminhos and conteudo:
                mensagem = mensagem + "\n" + conteudo
                resposta = self.modelo.enviar_mensagem(mensagem)
            elif self.caminhos and imagens:
                resposta = self.modelo.enviar_mensagem(
                    mensagem, caminho_image="".join(imagem for imagem in imagens))
            else:
                resposta = self.modelo.enviar_mensagem(mensagem)

            self.caminhos = None

            self.query_one("#bot", VerticalScroll).mount(
                Static(f"[yellow]bot[/]: {resposta}"))
            
            self.query_one("#user").text = ""
            
        elif evento.button.id == "enviar":
            self.notify("Selecione um modelo!")

        if evento.button.id == "anexo":
            self.caminhos = Midia.selecionar_arquivo()

    def on_select_changed(self):
        self.modelo.set_modelo(self.query_one(Select).value)
