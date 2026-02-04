from textual.app import App
from textual.widgets import TextArea, Input, Select, Button, Static
from textual.containers import Horizontal, HorizontalGroup, Vertical, VerticalGroup, VerticalScroll

import Midia
from Modelo import Modelo


class App(App):

    CSS_PATH = "Style.tcss"

    modelo = Modelo()
    
    base = "Responda usando o idioma da mensagem a seguir: \n"

    def compose(self):
        with HorizontalGroup(id="hg_bot"):
            yield Select((modelo, modelo) for modelo in self.modelo.listar_nome_modelos())
            yield VerticalScroll(id="bot")
        with HorizontalGroup(id="hg_user"):
            yield Button("📎", id="anexo")
            yield TextArea(id="user")
            yield Button("Enviar", id="enviar")

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
                    if camingo[-4:] in [".png", ".jpg", ".jpeg", ".gif", ".bmp",".webp", ".tiff"]:
                        imagens.append(Midia.encode_image(camingo))
                    else:
                        conteudo = Midia.get_conteudo(camingo)
            if self.caminhos and conteudo and imagens:
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
        elif evento.button.id == "enviar":
            self.notify("Selecione um modelo!")

        if evento.button.id == "anexo":
            self.caminhos = Midia.selecionar_arquivo()

    def on_select_changed(self):
        self.modelo.set_modelo(self.query_one(Select).value)
