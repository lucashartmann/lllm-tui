from textual.app import App
from textual.widgets import TextArea, Select, Button, Static, Switch
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll, Center
from textual.events import Click

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
        yield HorizontalGroup(id="hg_arquivos")
        with HorizontalGroup(id="hg_user"):
            yield TextArea(id="user")
            with VerticalGroup(id="vg_botoes"):
                yield Button("Enviar", id="enviar", flat=True)
                yield Button("📎", id="anexo", flat=True)
            with VerticalGroup(id="hg_editar_arquivos"):
                yield Static("Editar Arquivo:")
                with Center():
                    yield Switch()

    def on_button_pressed(self, evento: Button.Pressed):
        if self.modelo.modelo and evento.button.id == "enviar":

            prompt_inicial = self.query_one("#user").text

            self.query_one("#bot", VerticalScroll).mount(
                Static(prompt_inicial, classes="user"))

            mensagem = self.base + prompt_inicial

            if self.caminhos:
                conteudo = ""
                imagens = []
                codigo = False

                for caminho in self.caminhos:
                    if caminho[-4:] in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"]:
                        imagens.append(Midia.encode_image(caminho))
                    else:
                        conteudo = "\nArquivo: " + caminho + \
                            "\nConteúdo:" + f"\n{Midia.get_conteudo(caminho)}"
                        codigo = True

                if codigo:
                    print("elif conteudo:")
                    if self.query_one(Switch).value == True:
                        print("if self.query_one(Switch).value == True:")
                        mensagem = f'''
                        Você é um editor de código.
                        
                        Tarefa:
                        {prompt_inicial}

                        Regras:
                        - Gere APENAS um diff unificado (git diff)
                        - Não explique nada
                        - Não use markdown
                        - Não escreva texto fora do diff
                        - IMPORTANTE!: Ignore linha (como linha 1.) por exemplo, só está no código para te dizer em qual linha o código está no arquivo
                        - Responda usando o idioma que esta sendo usando na 'Tarefa:'
                        
                        {conteudo}
                        '''

                        resposta_diff = ""
                        if imagens and codigo:
                            resposta_diff = self.modelo.enviar_mensagem(
                                mensagem, caminho_image="".join(imagem for imagem in imagens))
                        else:
                            resposta_diff = self.modelo.enviar_mensagem(
                                mensagem)
                        if resposta_diff:
                            caminho, _ = Midia.parse_diff(resposta_diff)
                            Midia.aplicar_diff_manual(caminho, resposta_diff)

                            mensagem = f'''
                                    Explique essa mudança que você fez na última conversa:
                                    {resposta_diff}
                                    
                                    o prompt era: 
                                    {prompt_inicial}
                                    '''
                    else:
                        mensagem += conteudo

                    resposta = self.modelo.enviar_mensagem(mensagem)

                elif imagens:
                    resposta = self.modelo.enviar_mensagem(
                        mensagem, caminho_image="".join(imagem for imagem in imagens))

            else:
                resposta = self.modelo.enviar_mensagem(mensagem)

            self.caminhos = None

            if resposta:
                self.query_one("#bot", VerticalScroll).mount(
                    Static(f"[yellow]bot[/]: {resposta}"))

                self.query_one("#user").text = ""

        elif evento.button.id == "enviar":
            self.notify("Selecione um modelo!")

        elif evento.button.id == "anexo":
            self.caminhos = Midia.selecionar_arquivo()

            if self.caminhos:
                for caminho in self.caminhos:
                    self.query_one(
                        "#hg_arquivos", HorizontalGroup).styles.display = "block"
                    self.query_one("#hg_arquivos", HorizontalGroup).mount(
                        Static(f"[red]X[/] {caminho.split("/")[-1]}", name=caminho))

    def on_click(self, evento: Click):
        if evento.widget.parent.id == "hg_arquivos":
            caminho = evento.widget.name
            self.caminhos.remove(caminho)
            evento.widget.remove()

            if not self.caminhos:
                self.query_one(
                    "#hg_arquivos", HorizontalGroup).styles.display = "none"

    def on_select_changed(self):
        self.modelo.set_modelo(self.query_one(Select).value)
