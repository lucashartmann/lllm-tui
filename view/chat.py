from textual import events
import asyncio
from textual.screen import Screen, ModalScreen
from textual.widgets import TextArea, Select, Button, Static, Switch, Footer, Input, Tab, Tabs
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll, Center
from textual.binding import Binding
from model import modelo
import time
from textual_diff_view import DiffView, LoadError
from textual.app import App, ComposeResult
from textual import containers
from textual.reactive import var
from textual import widgets
from view.widgets.header import Header
import os
from pathlib import Path
from textual.containers import Horizontal
from util.selecionar_arquivo import selecionar_arquivo
from tools import arquivo, diagrama, internet
from view.widgets.container_comandos import ContainerComandos


class DiffScreen(ModalScreen):
    BINDINGS = [
        ("space", "toggle('split')", "Toggle split"),
        ("a", "toggle('annotations')", "Toggle annotations"),
    ]

    split = var(True)
    annotations = var(True)

    def __init__(self, original: str, modified: str) -> None:
        self.original = original
        self.modified = modified
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="dialog"):
            yield containers.VerticalScroll(id="diff-container")
            yield widgets.Footer()

    async def on_mount(self) -> None:
        try:
            diff_view = await DiffView.load(self.original, self.modified)
        except LoadError as error:
            self.notify(str(error), title="Failed to load code",
                        severity="error")
        else:
            diff_view.data_bind(DiffScreen.split, DiffScreen.annotations)
            await self.query_one("#diff-container").mount(diff_view)


class ChatScreen(Screen):

    CSS_PATH = ["css/base.tcss", "css/chat.tcss"]

    def __init__(self, name=None, id=None, classes=None):
        super().__init__(name, id, classes)

        self.caminhos = []
        self.nome_bot = self.app.nome_bot
        self.nome_user = self.app.nome_user
        self.cor_bot = self.app.cor_bot
        self.config = f'''
        Config:
        - seu nome: {self.app.nome_bot}
        - nome do user: {self.app.nome_user}
        Responda usando o idioma da mensagem a seguir:\n
        '''
        self.app.modelo = self.app.modelo

    BINDINGS = [
        Binding("ctrl+z", "parar", "parar modelo")
    ]

    def on_screen_resume(self):
        self.query_one(Tabs).active = self.query_one(
            "#tab_chat", Tab).id

    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        try:
            if event.tabs.active == self.query_one("#tab_config", Tab).id:
                self.app.switch_screen("config")
            elif event.tabs.active == self.query_one("#tab_skills", Tab).id:
                self.app.switch_screen("skills")
            elif event.tabs.active == self.query_one("#tab_models", Tab).id:
                self.app.switch_screen("models")
        except:
            pass

    def action_parar(self):
        if self.app.modelo.modelo:
            stop = self.app.modelo.descarregar_modelo()
            if stop:
                self.notify("Modelo parado com sucesso")

    def compose(self):
        yield Tabs(Tab("Chat", id="tab_chat"), Tab("Configuração", id="tab_config"), Tab("Skills", id="tab_skills"), Tab("Modelos", id="tab_models"))
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
        # yield HorizontalScroll(id="data")
        yield Footer(show_command_palette=False)

    def _gerar_resposta(self, prompt_inicial) -> str | None:
        resposta = None
        mensagem = self.app.SYSTEM_PROMPT + "\n" + self.config + "\n" + prompt_inicial

        if self.caminhos:
            arquivos = []
            imagens = []
            audios = []
            videos = []
            for caminho in self.caminhos:
                if os.path.isdir(caminho):
                    for root, dirs, files in os.walk(caminho):
                        for file in files:
                            caminho_completo = os.path.join(root, file)
                            if arquivo.is_image_file(caminho_completo):
                                imagens.append(caminho_completo)
                            elif arquivo.is_audio_file(caminho_completo):
                                audios.append(caminho_completo)
                            elif arquivo.is_video_file(caminho_completo):
                                videos.append(caminho_completo)
                            arquivos.append(caminho_completo)
                else:
                    if arquivo.is_image_file(caminho):
                        imagens.append(caminho)
                    elif arquivo.is_audio_file(caminho):
                        audios.append(caminho)
                    elif arquivo.is_video_file(caminho):
                        videos.append(caminho)
                    arquivos.append(caminho)

            if self.query_one(Switch).value == True:
                arquivo.MODEL = self.app.modelo.modelo
                if len(arquivos) > 1:
                    arquivo.alterar_lista_arquivos(arquivos, mensagem)
                else:
                    arquivo.edit_file(arquivos[0], mensagem)
            else:
                mensagem += "\n\nOs seguintes arquivos foram enviados:\n"
                for caminho in arquivos:
                    mensagem += f"-{caminho}\n"

                resposta = self.app.modelo.enviar_mensagem_com_ferramentas(
                    mensagem)

        else:
            resposta = self.app.modelo.enviar_mensagem_com_ferramentas(
                mensagem)

        return resposta

    async def processamento(self, prompt_inicial) -> None:
        resposta = await asyncio.to_thread(self._gerar_resposta, prompt_inicial)
        await self.parar_animacao()

        print(resposta)
        if resposta:
            bot_container = self.query_one(
                "#bot", VerticalScroll)
            try:
                widget = bot_container.query_one(".stt_pensando", Static)
                widget.remove_class("stt_pensando")
                widget.update(
                    f"[{self.app.cor_bot.hex}]{self.app.nome_bot}[/]: {resposta}")
            except:
                bot_container.mount(
                    Static(
                        f"[{self.app.cor_bot.hex}]{self.app.nome_bot}[/]: {resposta}")
                )
            bot_container.scroll_end(animate=False)

    async def parar_animacao(self):
        self.carregando_mensagem = False
        if hasattr(self, "_loading_timer") and self._loading_timer is not None:
            self._loading_timer.stop()

    async def animate_loading(self):
        bot_container = self.query_one("#bot", VerticalScroll)
        try:
            widget = bot_container.query_one(".stt_pensando", Static)
        except:
            widget = Static(classes="stt_pensando")
            bot_container.mount(widget)
        bot_container.scroll_end(animate=False)
        frames = ["●○○", "○●○", "○○●"]
        if not self.carregando_mensagem:
            return
        widget.update(
            f"[{self.app.cor_bot.hex}]{self.app.nome_bot}[/]: {frames[self._frame_index % len(frames)]}")
        self._frame_index += 1

    def comandos(self, prompt_inicial):
        comando = prompt_inicial.split()[0][1:]
        argumento = " ".join(prompt_inicial.split()[1:])

        if comando in ["modelo", "model"]:
            self.app.modelo.set_modelo(argumento)
            self.notify(f"Modelo {argumento} carregado com sucesso!")

        elif comando in ["listar_modelos", "list_models"]:
            modelos_disponiveis = self.app.modelo.listar_modelos()
            self.notify("Modelos disponíveis:\n" +
                        "\n".join(modelos_disponiveis))

        elif comando in ["ajuda", "help"]:
            self.notify(self.app.comandos)

        elif comando in ["novo", "new"]:
            self.query_one("#bot", VerticalScroll).clear()
            self.caminhos = []
            self.notify("Nova conversa iniciada!")

        elif comando in ["temperatura"]:
            try:
                valor = float(argumento)
                if self.app.modelo.set_temperatura(valor):
                    self.notify(f"Temperatura ajustada para {valor}")
                else:
                    self.notify(
                        "Valor inválido para temperatura. Use um número entre 0.0 e 2.0 (ex: /temperatura 0.7)")
            except ValueError:
                self.notify(
                    "Valor inválido para temperatura. Use um número (ex: /temperatura 0.7)")

        elif comando in ["max_tokens"]:
            try:
                valor = int(argumento)
                if self.app.modelo.set_max_tokens(valor):
                    self.notify(f"Max tokens ajustado para {valor}")
                else:
                    self.notify(
                        "Valor inválido para max tokens. Use um número inteiro (ex: /max_tokens 150)")
            except ValueError:
                self.notify(
                    "Valor inválido para max tokens. Use um número inteiro (ex: /max_tokens 150)")

        elif comando in ["top_p"]:
            try:
                valor = float(argumento)
                if self.app.modelo.set_top_p(valor):
                    self.notify(f"Top_p ajustado para {valor}")
                else:
                    self.notify(
                        "Valor inválido para top_p. Use um número entre 0.0 e 1.0 (ex: /top_p 0.9)")
            except ValueError:
                self.notify(
                    "Valor inválido para top_p. Use um número (ex: /top_p 0.9)")

    async def on_button_pressed(self, evento: Button.Pressed):
        if self.app.modelo.modelo and evento.button.id == "enviar":
            prompt_inicial = self.query_one("#user").text

            if prompt_inicial.lower().startswith("/"):
                self.comandos(prompt_inicial)
                return

            await self.query_one("#bot", VerticalScroll).mount(
                Static(prompt_inicial, classes="user"))

            self.carregando_mensagem = True
            self._frame_index = 0
            self._loading_timer = self.set_interval(0.4, self.animate_loading)

            self.query_one("#user").text = ""

            self.run_worker(
                self.processamento(prompt_inicial),
                name="AI pensando",
                exclusive=True,
            )

        elif evento.button.id == "enviar":
            self.notify("Selecione um modelo!")

        elif evento.button.id == "anexo":
            lista1 = selecionar_arquivo()
            lista2 = self.caminhos
            self.caminhos = list(set(lista2 + lista1))

            if self.caminhos:
                nomes = list(str(stt.name)
                             for stt in self.query_one("#hg_arquivos").query(Static))
                for caminho in self.caminhos:
                    if caminho not in nomes:
                        self.query_one(
                            "#hg_arquivos", HorizontalGroup).styles.display = "block"
                        self.query_one("#hg_arquivos", HorizontalGroup).mount(
                            Static(f"[red]X[/] {caminho.split("/")[-1]}", name=caminho))

    def on_click(self, evento: events.Click):
        if evento.widget.parent.id == "hg_arquivos":
            caminho = evento.widget.name
            self.caminhos.remove(caminho)
            evento.widget.remove()

            if not self.caminhos:
                self.query_one(
                    "#hg_arquivos", HorizontalGroup).styles.display = "none"

    def on_select_changed(self):
        if self.app.modelo.modelo:
            self.app.modelo.unload_model()
        self.app.modelo.set_modelo(self.query_one(Select).value)

    def on_text_area_changed(self, event: TextArea.Changed):
        if event.text_area.text.startswith("/"):
            container = ContainerComandos()
            print(event.text_area.text[0:])
            novo_comandos = ""
            for comando in self.app.comandos.split("\n"):
                if comando.startswith(event.text_area.text[0:]):
                    novo_comandos += comando + "\n"

            if novo_comandos:
                container = ContainerComandos()
                try:
                    container = self.query_one(ContainerComandos)
                except:
                    self.mount(container, after=self.query_one("#hg_arquivos"))

                container.atualizar_comandos(novo_comandos.split("\n"))

        else:
            try:
                container = self.query_one(ContainerComandos)
                container.remove()
            except:
                pass
