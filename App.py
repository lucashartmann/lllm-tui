from textual import events
from textual.app import App
from textual.widgets import TextArea, Select, Button, Static, Switch, Footer, Input
from textual.containers import HorizontalGroup, VerticalGroup, VerticalScroll, Center, Horizontal, HorizontalScroll
from textual.binding import Binding
import Midia
from Midia import ChunkedFileProcessor
from Modelo import Modelo
from textual_colorpicker import ColorPicker
from textual.color import Color
import time


class App(App):

    CSS_PATH = "Style.tcss"

    modelo = Modelo()
    file_processor = ChunkedFileProcessor()
    caminhos = list()
    nome_bot = "bot"
    nome_user = None
    cor_bot = Color(0, 128, 0)
    config = f'''
    Config:
    - seu nome: {nome_bot}
    - nome do user: {nome_user}
    Responda usando o idioma da mensagem a seguir:\n
    '''
    _stream_started_at = None
    _first_token_latency = None
    _current_response_container = None
    _current_response_widget = None

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

    def on_mount(self):
        self.run_worker(
                    self.carregar_modelos,
                    name="Carregando modelos do Ollama",
                    thread=True,
                    exclusive=True,
        )

    def compose(self):
        with Horizontal(id="h_top"):
            yield Select([("asdas", "asdasdsa")])
            yield Button("🔃", id="recarregar")
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
        # yield HorizontalScroll(id="data")
        yield Footer(show_command_palette=False)

    def on_color_picker_changed(self, evento: ColorPicker.Changed):
        self.cor_bot = evento.color_picker.color

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
        modo_edicao = self.query_one(Switch).value == True
        estrategia_resposta = "chat"
        tokens_prompt = 0
        limite_modelo = self.modelo.obter_limite_contexto()
        chunks_total = 0
        chunks_selecionados = 0
        inicio_total = time.perf_counter()

        if self.caminhos:
            imagens = []
            arquivos_texto = []

            for caminho in self.caminhos:
                ext = caminho.split(".")[-1].lower()
                if ext in ["png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff"]:
                    try:
                        img_encoded = Midia.encode_image(caminho)
                        if img_encoded:
                            imagens.append(img_encoded)
                    except Exception as e:
                        print(f"Erro ao codificar imagem {caminho}: {e}")
                elif ext in ["js", "py", "html", "tcss", "css", "md", "txt", "json", "yaml", "yml", "xml", "csv"]:
                    arquivos_texto.append(caminho)

            if modo_edicao and arquivos_texto:
                max_retry_sintaxe = self.modelo.obter_max_retry_sintaxe()
                # self._log_ui(
                # f"Retry de sintaxe configurado: {max_retry_sintaxe}")

                for arquivo in arquivos_texto:
                    # self._log_ui(f"Processando: {arquivo}")

                    def ia_callback(conteudo_chunk, prompt_chunk):
                        resposta = self.modelo.enviar_mensagem_sync(
                            prompt_chunk)
                        return resposta if resposta else ""

                    success, mensagem = self.file_processor.processar_arquivo_com_prompt_v2(
                        arquivo,
                        prompt_inicial,
                        ia_callback,
                        validar_sintaxe_python=True,
                        max_retry_sintaxe=max_retry_sintaxe,
                    )

                    if success:
                        self._log_ui(f"{arquivo} editado com sucesso!")
                    else:
                        self._log_ui(f"Erro ao editar {arquivo}: {mensagem}")
                        self.notify(f"Erro: {mensagem}")

                await self.parar_animacao()
                return

            if arquivos_texto:
                contexto_arquivos, estrategia, tokens_prompt, limite_modelo = self.modelo.montar_contexto_arquivos(
                    caminhos=arquivos_texto,
                    pergunta=prompt_inicial,
                    chunk_size=800,
                    overlap=120,
                )
                estrategia_resposta = estrategia
                contexto_stats = self.modelo.ultimo_contexto_stats or {}
                chunks_total = contexto_stats.get("chunks_total", 0)
                chunks_selecionados = contexto_stats.get(
                    "chunks_selecionados", 0)

                print(
                    f"Estratégia: {estrategia} | tokens estimados: {tokens_prompt} | limite modelo: {limite_modelo}")

                mensagem = (
                    f"{self.config}"
                    f"Pergunta do usuário:\n{prompt_inicial}\n\n"
                    f"Contexto dos arquivos:\n{contexto_arquivos}"
                )
                self._stream_started_at = time.perf_counter()
                self._first_token_latency = None

                resposta = self.modelo.enviar_mensagem(
                    mensagem,
                    on_chunk=self._update_ui_streaming,
                )

                if resposta:
                    # self._update_ui_response(resposta)
                    self._mostrar_rodape_resposta(
                        estrategia=estrategia_resposta,
                        chunks_total=chunks_total,
                        chunks_selecionados=chunks_selecionados,
                        tokens_prompt=tokens_prompt,
                        limite_modelo=limite_modelo,
                        inicio_total=inicio_total,
                    )
                else:
                    self._log_ui("Erro ao processar contexto dos arquivos")

                await self.parar_animacao()
                return

            if imagens:
                if not self.modelo.suporta_imagem():
                    self.notify(
                        "Modelo selecionado não suporta imagem. As imagens foram ignoradas.")
                    self._log_ui(
                        "Modelo sem suporte a visão; ignorando imagens.")
                    mensagem = self.config + prompt_inicial
                    self._stream_started_at = time.perf_counter()
                    self._first_token_latency = None
                    resposta = self.modelo.enviar_mensagem(
                        mensagem,
                        on_chunk=self._update_ui_streaming,
                    )
                    if resposta:
                        # self._update_ui_response(resposta)
                        self._mostrar_rodape_resposta(
                            estrategia="chat",
                            chunks_total=0,
                            chunks_selecionados=0,
                            tokens_prompt=self.modelo.estimar_tokens(mensagem),
                            limite_modelo=limite_modelo,
                            inicio_total=inicio_total,
                        )
                    else:
                        self._log_ui("Erro ao enviar mensagem sem imagem")

                    await self.parar_animacao()
                    return

                mensagem = self.config + prompt_inicial
                self._stream_started_at = time.perf_counter()
                self._first_token_latency = None
                resposta = self.modelo.enviar_mensagem(
                    mensagem,
                    caminho_image=imagens,
                    on_chunk=self._update_ui_streaming,
                )

                if resposta:
                    # self._update_ui_response(resposta)
                    self._mostrar_rodape_resposta(
                        estrategia="chat_imagem",
                        chunks_total=0,
                        chunks_selecionados=0,
                        tokens_prompt=self.modelo.estimar_tokens(mensagem),
                        limite_modelo=limite_modelo,
                        inicio_total=inicio_total,
                    )
                else:
                    self._log_ui("Erro ao enviar com imagens")

                await self.parar_animacao()
                return

        mensagem = self.config + prompt_inicial
        self._stream_started_at = time.perf_counter()
        self._first_token_latency = None
        resposta = self.modelo.enviar_mensagem(
            mensagem,
            on_chunk=self._update_ui_streaming,
        )

        if resposta:
            # self._update_ui_response(resposta)
            self._mostrar_rodape_resposta(
                estrategia="chat",
                chunks_total=0,
                chunks_selecionados=0,
                tokens_prompt=self.modelo.estimar_tokens(mensagem),
                limite_modelo=limite_modelo,
                inicio_total=inicio_total,
            )
        else:
            self._log_ui("Erro ao enviar mensagem")

        await self.parar_animacao()

    def _log_ui(self, mensagem: str):
        print(mensagem)

        def update_ui():
            bot_container = self.query_one("#bot", VerticalScroll)
            try:
                widget = bot_container.query_one(".stt_pensando", Static)
                widget.update(self._formatar_mensagem_bot(mensagem))
            except Exception:
                bot_container.mount(
                    Static(self._formatar_mensagem_bot(mensagem))
                )
            bot_container.scroll_end(animate=False)

        self.call_from_thread(update_ui)

    def _formatar_mensagem_bot(self, mensagem: str) -> str:
        return f"[{self.cor_bot.hex}]{self.nome_bot}[/]: {mensagem}"

    def _remover_widget_pensando(self, bot_container: VerticalScroll) -> None:
        try:
            widget = bot_container.query_one(".stt_pensando", Static)
            widget.remove()
        except Exception:
            pass

    def _montar_ou_atualizar_resposta_bot(self, bot_container: VerticalScroll, resposta: str) -> None:
        texto = self._formatar_mensagem_bot(resposta)
        container = self._current_response_container
        widget = self._current_response_widget

        if container is not None and widget is not None and widget.parent is container:
            widget.update(texto)
            return

        novo_widget = Static(texto, classes="stt_resposta_bot")
        novo_container = VerticalGroup(novo_widget)
        bot_container.mount(novo_container)
        self._current_response_container = novo_container
        self._current_response_widget = novo_widget

    def _update_ui_response(self, resposta: str):
        def update_ui():
            self.loading = False
            bot_container = self.query_one("#bot", VerticalScroll)
            self._remover_widget_pensando(bot_container)
            self._montar_ou_atualizar_resposta_bot(bot_container, resposta)
            bot_container.scroll_end(animate=False)

        self.call_from_thread(update_ui)

    def _update_ui_streaming(self, resposta_parcial: str):
        def update_ui():
            if self._stream_started_at and self._first_token_latency is None and resposta_parcial:
                self._first_token_latency = time.perf_counter() - self._stream_started_at

            bot_container = self.query_one("#bot", VerticalScroll)
            self._remover_widget_pensando(bot_container)
            self._montar_ou_atualizar_resposta_bot(bot_container, resposta_parcial)
            bot_container.scroll_end(animate=False)

        self.call_from_thread(update_ui)

    def _mostrar_rodape_resposta(self, estrategia: str, chunks_total: int, chunks_selecionados: int,
                                 tokens_prompt: int, limite_modelo: int, inicio_total: float):
        total = time.perf_counter() - inicio_total
        primeiro = self._first_token_latency if self._first_token_latency is not None else total
        metricas_ollama = self.modelo.ultima_metrica or {}

        prompt_real = metricas_ollama.get("prompt_eval_count")
        eval_real = metricas_ollama.get("eval_count")

        partes = [
            f"modo: {estrategia}",
            f"chunks usados: {chunks_selecionados}/{chunks_total}",
            # f"tokens no prompt (estimado): {tokens_prompt}k",
            f"janela de contexto do modelo: {limite_modelo}",
            # f"tempo até 1º token: {primeiro:.2f}s",
            f"tempo: {total:.2f}s",
        ]

        if prompt_real is not None:
            partes.append(f"tokens prompt: {prompt_real}")
        if eval_real is not None:
            partes.append(f"tokens resposta: {eval_real}")

        texto = " | ".join(partes)

        def montar():
            bot_container = self.query_one("#bot")
            print(texto)
            try:
                container = self._current_response_container
                if container is None:
                    return
                container.mount(Static(f"{texto}"))
            except Exception:
                return
        self.call_from_thread(montar)

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
            f"[{self.cor_bot.hex}]{self.nome_bot}[/]: {frames[self._frame_index % len(frames)]}")
        self._frame_index += 1

    async def carregar_modelos(self):
        select = self.query_one(Select)
        lista = list((modelo, modelo)
                     for modelo in self.modelo.listar_nome_modelos())
        select.set_options(lista)

    async def on_button_pressed(self, evento: Button.Pressed):
        match evento.button.id:
            case "recarregar":
                self.run_worker(
                    self.carregar_modelos,
                    name="Carregando modelos do Ollama",
                    thread=True,
                    exclusive=True,
                )
            case "enviar":
                if self.modelo.modelo:
                    prompt_inicial = self.query_one("#user").text

                    self._current_response_container = None
                    self._current_response_widget = None

                    await self.query_one("#bot", VerticalScroll).mount(
                        Static(prompt_inicial, classes="user"))

                    self.loading = True
                    self._frame_index = 0
                    self._loading_timer = self.set_interval(
                        0.4, self.animate_loading)

                    self.query_one("#user").text = ""

                    self.run_worker(
                        self.processamento(prompt_inicial),
                        name="AI pensando",
                        thread=True,
                        exclusive=True,
                    )

            case "enviar":
                self.notify("Selecione um modelo!")

            case "anexo":
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
