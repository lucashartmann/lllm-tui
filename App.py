from textual import events
from textual.app import App
from textual.widgets import TextArea, Select, Button, Static, Switch, Footer, Input
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll, Center, Horizontal
from textual.binding import Binding
import Midia
from Modelo import Modelo
from textual_colorpicker import ColorPicker

class App(App):

    CSS_PATH = "Style.tcss"

    modelo = Modelo()
    caminhos = list()
    nome_bot = "bot"
    nome_user = None
    cor_bor = "yellow"
    config = f'''
    Config:
    - seu nome: {nome_bot}
    - nome do user: {nome_user}
    Responda usando o idioma da mensagem a seguir:\n
    '''

    BINDINGS = [
        Binding("ctrl+q", "sair", "sair"),
        Binding("ctrl+c", "sair", "sair"),
        Binding("ctrl+z", "parar", "parar modelo")
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

        # print(f"width do terminal: {event.size.width}")

        for w in sorted(self.WIDTH_BREAKPOINS, reverse=True):
            if event.size.width > w:
                self.add_class(self.WIDTH_BREAKPOINS[w])
                break

    def action_parar(self):
        if self.modelo.modelo:
            stop = self.modelo.unload_model()
            if stop:
                self.notify("Modelo parado com sucesso")

    def action_sair(self):
        self.notify("Saindo...")
        if self.modelo.modelo:
            self.modelo.unload_model()
        self.exit()

    def compose(self):
        with Horizontal(id="h_top"):
            yield Select((modelo, modelo) for modelo in self.modelo.listar_nome_modelos())
            yield Input(placeholder="nome do bot", value="bot", id="input_nome_bot")
            yield Input(placeholder="seu nome")
            yield ColorPicker()
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
        yield Footer(show_command_palette=False)
        
    def on_color_picker_changed(self, evento: ColorPicker.Changed):
        self.cor_bor = evento.color_picker.color

    def on_input_changed(self, evento: Input.Changed):
        if evento.input.id == "input_nome_bot":
            self.nome_bot = evento.input.value
        else:
            self.nome_user = evento.input.value
            
        self.config = f'''
            Config:
            - seu nome: {self.nome_bot}
            - nome do user: {self.nome_user}
            Responda usando o idioma da mensagem a seguir:\n
            '''

    async def processamento(self, prompt_inicial) -> None:
        resposta = None
        mensagem = self.config + prompt_inicial

        if self.caminhos:
            print(self.caminhos)
            imagens = []
            codigos = dict()
            for caminho in self.caminhos:
                if caminho.split(".")[-1] in ["png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff"]:
                    imagens.append(Midia.encode_image(caminho))
                elif caminho.split(".")[-1] in ["js", "py", "html", "tcss", "css"]:
                    codigos[caminho] = Midia.get_chunks_codigo(caminho)
                    print(Midia.get_chunks_codigo(caminho))

            if codigos:
                print(codigos)
                for arquivo, chunks in codigos.items():
                    for chunk in chunks:
                        if self.query_one(Switch).value == True:
                            mensagem = f'''
                                {arquivo}
                                {chunk}
                                
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
                                
                                Config:
                                - seu nome: {self.nome_bot}
                                - nome do user: {self.nome_user}
                                
                                '''

                            resposta_diff = ""
                            if imagens:
                                resposta_diff = self.modelo.enviar_mensagem(
                                    mensagem, caminho_image="".join(imagem for imagem in imagens))
                            else:
                                resposta_diff = self.modelo.enviar_mensagem(
                                    mensagem)

                            if resposta_diff:
                                print("prompt inicial:", prompt_inicial)
                                print("Resposta diff:", resposta_diff)

                                caminho, _ = Midia.parse_diff(
                                    resposta_diff)
                                Midia.aplicar_diff_manual(
                                    caminho, resposta_diff)

                                mensagem = f'''
                                            Explique essa mudança que você fez na última conversa:
                                            {resposta_diff}
                                            
                                            o prompt era: 
                                            {prompt_inicial}
                                            '''

                                resposta = self.modelo.enviar_mensagem(
                                    mensagem)

                                if resposta:
                                    def update_ui():
                                        self.loading = False
                                        bot_container = self.query_one(
                                            "#bot", VerticalScroll)
                                        try:
                                            widget = bot_container.query_one(
                                                ".stt_pensando", Static)
                                            widget.update(
                                                f"[{self.cor_bor.hex}]{self.nome_bot}[/]: {resposta}")
                                        except:
                                            bot_container.mount(
                                                Static(
                                                    f"[{self.cor_bor.hex}]{self.nome_bot}[/]: {resposta}")
                                            )
                                        bot_container.scroll_end(animate=False)
                                    self.call_from_thread(update_ui)
                            else:
                                self.notify("Erro ao gerar diff")
                        else:
                            mensagem = f'''
                                {arquivo}
                                {chunk}
                                
                                
                                Tarefa:
                                {prompt_inicial}
                                '''

                            resposta = self.modelo.enviar_mensagem(
                                mensagem)

                            if resposta:
                                def update_ui():
                                    self.loading = False
                                    bot_container = self.query_one(
                                        "#bot", VerticalScroll)
                                    try:
                                        widget = bot_container.query_one(
                                            ".stt_pensando", Static)
                                        widget.update(
                                            f"[{self.cor_bor.hex}]{self.nome_bot}[/]: {resposta}")
                                    except:
                                        bot_container.mount(
                                            Static(
                                                f"[{self.cor_bor.hex}]{self.nome_bot}[/]: {resposta}")
                                        )
                                    bot_container.scroll_end(animate=False)
                                self.call_from_thread(update_ui)

                return

            elif imagens:
                resposta = self.modelo.enviar_mensagem(
                    mensagem, caminho_image="".join(imagem for imagem in imagens))

        else:
            resposta = self.modelo.enviar_mensagem(mensagem)

        print(resposta)
        if resposta:
            async def update_ui():
                await self.parar_animacao()
                bot_container = self.query_one(
                    "#bot", VerticalScroll)
                try:
                    widget = bot_container.query_one(".stt_pensando", Static)
                    widget.remove_class("stt_pensando")
                    widget.update(f"[{self.cor_bor.hex}]{self.nome_bot}[/]: {resposta}")
                except:
                    bot_container.mount(
                        Static(
                            f"[{self.cor_bor.hex}]{self.nome_bot}[/]: {resposta}")
                    )
                bot_container.scroll_end(animate=False)
            self.call_from_thread(update_ui)

    async def parar_animacao(self):
        self.loading = False
        self._loading_timer.stop()

    async def animate_loading(self):
        bot_container = self.query_one("#bot", VerticalScroll)
        try:
            widget = bot_container.query_one(".stt_pensando", Static)
        except:
            widget = Static(classes="stt_pensando")
            bot_container.mount(widget)
        frames = ["●○○", "○●○", "○○●"]
        if not self.loading:
            return
        widget.update(
            f"[{self.cor_bor.hex}]{self.nome_bot}[/]: {frames[self._frame_index % len(frames)]}")
        self._frame_index += 1

    async def on_button_pressed(self, evento: Button.Pressed):
        if self.modelo.modelo and evento.button.id == "enviar":
            prompt_inicial = self.query_one("#user").text

            await self.query_one("#bot", VerticalScroll).mount(
                Static(prompt_inicial, classes="user"))

            self.loading = True
            self._frame_index = 0
            self._loading_timer = self.set_interval(0.4, self.animate_loading)

            self.query_one("#user").text = ""

            self.run_worker(
                self.processamento(prompt_inicial),
                name="AI pensando",
                thread=True,
                exclusive=True,
            )

        elif evento.button.id == "enviar":
            self.notify("Selecione um modelo!")

        elif evento.button.id == "anexo":
            lista1 = Midia.selecionar_arquivo()
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
        if self.modelo.modelo:
            self.modelo.unload_model()
        self.modelo.set_modelo(self.query_one(Select).value)
