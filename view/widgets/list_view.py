from textual.widgets import ListView, ListItem
from typing import ClassVar, Iterable, Optional
from textual.await_complete import AwaitComplete
from textual.await_remove import AwaitRemove
from textual.binding import Binding, BindingType
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets._list_item import ListItem


class ListView(VerticalScroll, can_focus=True, can_focus_children=False):
    """A vertical list view widget.

    Displays a vertical list of `ListItem`s which can be highlighted and
    selected using the mouse or keyboard.

    Attributes:
        index: The index in the list that's currently highlighted.
    """

    ALLOW_MAXIMIZE = True

    DEFAULT_CSS = """
    ListView {
        background: $surface;
        & > ListItem {
            color: $foreground;
            height: auto;
            overflow: hidden hidden;
            width: 1fr;

            &.-hovered {
                background: $block-hover-background;
            }
            
            &.-highlight {
                color: $block-cursor-blurred-foreground;
                background: $block-cursor-blurred-background;
                text-style: $block-cursor-blurred-text-style;
            }

            &.-selected {
                color: $accent;
                background: $accent 20%;
                text-style: bold;
            }
        }

        &:focus {
            background-tint: $foreground 5%;
            & > ListItem.-highlight {
                color: $block-cursor-foreground;
                background: $block-cursor-background;
                text-style: $block-cursor-text-style;
            }

            & > ListItem.-selected {
                color: $accent;
                background: $accent 30%;
                text-style: bold;
            }
        }

    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "select_cursor", "Select", show=False),
        Binding("ctrl+enter", "toggle_select_cursor", "Toggle Select", show=False),
        Binding("up", "cursor_up", "Cursor up", show=False),
        Binding("down", "cursor_down", "Cursor down", show=False),
    ]
    """
    | Key(s) | Description |
    | :- | :- |
    | enter | Select the current item. |
    | up | Move the cursor up. |
    | down | Move the cursor down. |
    """

    index = reactive[Optional[int]](None, init=False)
    """The index of the currently highlighted item."""

    class Highlighted(Message):
        """Posted when the highlighted item changes.

        Highlighted item is controlled using up/down keys.
        Can be handled using `on_list_view_highlighted` in a subclass of `ListView`
        or in a parent widget in the DOM.
        """

        ALLOW_SELECTOR_MATCH = {"item"}
        """Additional message attributes that can be used with the [`on` decorator][textual.on]."""

        def __init__(self, list_view: ListView, item: ListItem | None) -> None:
            super().__init__()
            self.list_view: ListView = list_view
            """The view that contains the item highlighted."""
            self.item: ListItem | None = item
            """The highlighted item, if there is one highlighted."""

        @property
        def control(self) -> ListView:
            """The view that contains the item highlighted.

            This is an alias for [`Highlighted.list_view`][textual.widgets.ListView.Highlighted.list_view]
            and is used by the [`on`][textual.on] decorator.
            """
            return self.list_view

    class Selected(Message):
        """Posted when a list item is selected, e.g. when you press the enter key on it.

        Can be handled using `on_list_view_selected` in a subclass of `ListView` or in
        a parent widget in the DOM.
        """

        ALLOW_SELECTOR_MATCH = {"item"}
        """Additional message attributes that can be used with the [`on` decorator][textual.on]."""

        def __init__(self, list_view: ListView, item: ListItem, index: int) -> None:
            super().__init__()
            self.list_view: ListView = list_view
            """The view that contains the item selected."""
            self.item: ListItem = item
            """The selected item."""
            self.index = index
            """Index of the selected item."""

        @property
        def control(self) -> ListView:
            """The view that contains the item selected.

            This is an alias for [`Selected.list_view`][textual.widgets.ListView.Selected.list_view]
            and is used by the [`on`][textual.on] decorator.
            """
            return self.list_view

    def __init__(
        self,
        *children: ListItem,
        initial_index: int | None = 0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """
        Initialize a ListView.

        Args:
            *children: The ListItems to display in the list.
            initial_index: The index that should be highlighted when the list is first mounted.
            name: The name of the widget.
            id: The unique ID of the widget used in CSS/query selection.
            classes: The CSS classes of the widget.
            disabled: Whether the ListView is disabled or not.
        """
        super().__init__(
            *children, name=name, id=id, classes=classes, disabled=disabled
        )
        self._initial_index = initial_index
        self.selected_indices: set[int] = set()


    def watch_index(self, old_index: int | None, new_index: int | None) -> None:
        """Updates the highlighting when the index changes."""

        if new_index is not None:
            selected_widget = self._nodes[new_index]
            if selected_widget.region:
                self.scroll_to_widget(self._nodes[new_index], animate=False)
            else:
                # Call after refresh to permit a refresh operation
                self.call_after_refresh(
                    self.scroll_to_widget, selected_widget, animate=False
                )

        if self._is_valid_index(old_index):
            old_child = self._nodes[old_index]
            assert isinstance(old_child, ListItem)
            old_child.highlighted = False
            # Remove selected class if not in selected_indices
            if old_index not in self.selected_indices:
                old_child.remove_class("-selected")

        if (
            new_index is not None
            and self._is_valid_index(new_index)
            and not self._nodes[new_index].disabled
        ):
            new_child = self._nodes[new_index]
            assert isinstance(new_child, ListItem)
            new_child.highlighted = True
            # Add selected class if in selected_indices
            if new_index in self.selected_indices:
                new_child.add_class("-selected")
            self.post_message(self.Highlighted(self, new_child))
        else:
            self.post_message(self.Highlighted(self, None))



    def clear(self) -> AwaitRemove:
        """Clear all items from the ListView.

        Returns:
            An awaitable that yields control to the event loop until
                the DOM has been updated to reflect all children being removed.
        """
        await_remove = self.query("ListView > ListItem").remove()
        self.index = None
        self.selected_indices.clear()
        return await_remove


    def pop(self, index: Optional[int] = None) -> AwaitComplete:
        """Remove last ListItem from ListView or
           Remove ListItem from ListView by index

        Args:
            index: index of ListItem to remove from ListView

        Returns:
            An awaitable that yields control to the event loop until
                the DOM has been updated to reflect item being removed.
        """
        if len(self) == 0:
            raise IndexError("pop from empty list")

        index = index if index is not None else -1
        item_to_remove = self.query("ListItem")[index]
        normalized_index = index if index >= 0 else index + len(self)

        async def do_pop() -> None:
            """Remove the item and update the highlighted index."""
            await item_to_remove.remove()
            
            # Update selected_indices when an item is removed
            if normalized_index in self.selected_indices:
                self.selected_indices.remove(normalized_index)
            
            # Adjust indices in selected_indices for items after the removed one
            new_selected = set()
            for sel_index in self.selected_indices:
                if sel_index < normalized_index:
                    new_selected.add(sel_index)
                elif sel_index > normalized_index:
                    new_selected.add(sel_index - 1)
            self.selected_indices = new_selected
            
            if self.index is not None:
                if normalized_index < self.index:
                    self.index -= 1
                elif normalized_index == self.index:
                    old_index = self.index
                    # Force a re-validation of the index
                    self.index = self.index
                    # If the index hasn't changed, the watcher won't be called
                    # but we need to update the highlighted item
                    if old_index == self.index:
                        self.watch_index(old_index, self.index)

        return AwaitComplete(do_pop())

    def remove_items(self, indices: Iterable[int]) -> AwaitComplete:
        """Remove ListItems from ListView by indices

        Args:
            indices: index(s) of ListItems to remove from ListView

        Returns:
            An awaitable object that waits for the direct children to be removed.
        """
        items = self.query("ListItem")
        items_to_remove = [items[index] for index in indices]
        normalized_indices = set(
            index if index >= 0 else index + len(self) for index in indices
        )

        async def do_remove_items() -> None:
            """Remove the items and update the highlighted index."""
            await self.remove_children(items_to_remove)
            
            # Update selected_indices when items are removed
            removed_indices = sorted(normalized_indices)
            new_selected = set()
            for sel_index in self.selected_indices:
                if sel_index not in normalized_indices:
                    # Count how many indices before this one were removed
                    removed_before = sum(1 for r_idx in removed_indices if r_idx < sel_index)
                    new_selected.add(sel_index - removed_before)
            self.selected_indices = new_selected
            
            if self.index is not None:
                removed_before_highlighted = sum(
                    1 for index in normalized_indices if index < self.index
                )
                if removed_before_highlighted:
                    self.index -= removed_before_highlighted
                elif self.index in normalized_indices:
                    old_index = self.index
                    # Force a re-validation of the index
                    self.index = self.index
                    # If the index hasn't changed, the watcher won't be called
                    # but we need to update the highlighted item
                    if old_index == self.index:
                        self.watch_index(old_index, self.index)

        return AwaitComplete(do_remove_items())


    def action_toggle_select_cursor(self) -> None:
        """Toggle selection of the current item (Ctrl+Enter)."""
        if self.index is None:
            return
        
        if self.index in self.selected_indices:
            self.selected_indices.remove(self.index)
            if self._is_valid_index(self.index):
                self._nodes[self.index].remove_class("-selected")
        else:
            self.selected_indices.add(self.index)
            if self._is_valid_index(self.index):
                self._nodes[self.index].add_class("-selected")

    def get_selected_items(self) -> list[ListItem]:
        """Return a list of selected ListItem widgets.
        
        Returns:
            A list of ListItem widgets that are currently selected.
        """
        selected_items = []
        for index in sorted(self.selected_indices):
            if self._is_valid_index(index):
                item = self._nodes[index]
                assert isinstance(item, ListItem)
                selected_items.append(item)
        return selected_items

  