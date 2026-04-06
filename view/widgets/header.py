from textual.widgets import Header, _header, Button, Switch, Input

class Header(Header):

    BINDINGS = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self):
        self.remove_children(_header.HeaderIcon)
        self.mount(Button("X", flat=True, compact=True, id="bt_pressionar"),
                   before=self.query_one(_header.HeaderTitle))

        self.mount(Switch(animate=False),
                   after=self.query_one(_header.HeaderTitle))

    def on_button_pressed(self):
        if len(self.app.screen_stack) > 2:
            self.app.pop_screen()
        else:
            self.app.exit()

    def on_show(self):
        if "dark" in self.app.classes:
            self.query_one(Switch).value = True
        else:
            self.query_one(Switch).value = False

    def on_switch_changed(self, evento: Switch.Changed):

        if evento.switch.value:
            self.app.add_class("dark")
            self.app.refresh_css()
        else:
            self.app.remove_class("dark")
            self.app.refresh_css()
