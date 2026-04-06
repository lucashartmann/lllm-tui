from textual.app import App
from textual.screen import Screen
from textual.widgets import Tabs, Tab, ListItem, Static
from view.widgets.list_view import ListView


class SkillsScreen(Screen):

    CSS_PATH = ["css/base.tcss", "css/skills.tcss"]

    def compose(self):
        yield Tabs(Tab("Chat", id="tab_chat"), Tab("Configuração", id="tab_config"), Tab("Skills", id="tab_skills"), Tab("Modelos", id="tab_models"))
        yield ListView(ListItem(Static("Diagramas")), ListItem(Static("Internet")))
        
    def on_screen_resume(self, event):
        self.query_one(Tabs).active = self.query_one(
            "#tab_skills", Tab).id
        
    def on_list_view_selected(self, event: ListView.Selected):
        selected_items = event.get_selected_items()
        if not selected_items:
            return
        skills = []
        for item in selected_items:
            skill_nome = item.query_one(Static).renderable.plain
            skills.append(skill_nome)
        self.app.lista_skills = skills
        self.app.notify(f"Skills '{', '.join(skills)}' selecionadas.")
        
    def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        try:
            if event.tabs.active == self.query_one("#tab_config", Tab).id:
                self.app.switch_screen("config")
            elif event.tabs.active == self.query_one("#tab_chat", Tab).id:
                self.app.switch_screen("inicio")
            elif event.tabs.active == self.query_one("#tab_models", Tab).id:
                self.app.switch_screen("models")
        except:
            pass