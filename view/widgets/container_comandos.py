from textual import events
from textual.containers import VerticalScroll
from textual.widgets import Static, TextArea
from util.comandos import comandos_str
from textual.events import Click, Focus, Key
from textual.binding import Binding


class ContainerComandos(VerticalScroll):
    # usuario pode clicar nas opçoes, isso retorna a opcao escolhida
    # usuario pode escolher usando setas e enter, isso retorna a opcao escolhida
    # o container tambem tem suas opçoes atualiozados quando o usuario digita um comando, entao o container tem um metodo para atualizar as opçoes

    BINDINGS = [
        Binding("enter", "selecionar_comando", "Selecionar comando"),
        Binding("up", "navegar_cima", "Navegar para cima"),
        Binding("down", "navegar_baixo", "Navegar para baixo"),
    ]

    def action_selecionar_comando(self):
        if isinstance(self.focused, Static):
            self.screen.query_one(TextArea).text = self.focused.content
            self.screen.query_one(TextArea).focus()

    def action_navegar_cima(self):
        if self.focused and self.children.index(self.focused) > 0:
            self.children[self.children.index(self.focused) - 1].focus()
            self.focused.remove_class("focused")
            self.focused = self.children[self.children.index(self.focused) - 1]
            self.children[self.children.index(
                self.focused) - 1].add_class("focused")

    def action_navegar_baixo(self):
        if self.focused and self.children.index(self.focused) < len(self.children) - 1:
            self.children[self.children.index(self.focused) + 1].focus()
            self.focused.remove_class("focused")
            self.focused = self.children[self.children.index(self.focused) + 1]
            self.children[self.children.index(
                self.focused) + 1].add_class("focused")

    def __init__(self):
        super().__init__()
        self.focused = None
        self.can_focus_children = True
        self.can_focus = True

    def _on_mount(self, event):
        return super()._on_mount(event)

    def compose(self):
        for comando in comandos_str.split("\n"):
            yield Static(comando)

    def atualizar_comandos(self, comandos):
        for child in self.children:
            child.remove()
        for comando in comandos:
            self.mount(Static(comando))
        self.children[0].focus()

    def on_click(self, event):
        if isinstance(event.widget, Static):
            self.focus()
            if self.focused:
                self.focused.remove_class("focused")
            event.widget.focus()
            event.widget.add_class("focused")
            self.focused = event.widget
