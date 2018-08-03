from typing import Optional, Any

from gi.repository import Gtk, GObject, GdkPixbuf


class ItemExplorer(Gtk.Grid):
    _selection = None  # type: Optional[str]

    def __init__(self, **properties):
        super().__init__(**properties)

        # Column format: (id, icon name, name)
        self._model = Gtk.ListStore(str, GdkPixbuf.Pixbuf, str)

        tree_view_sw = Gtk.ScrolledWindow()
        self.attach(tree_view_sw, 0, 0, 1, 1)

        self._tree_view = Gtk.TreeView.new_with_model(self._model)
        self._tree_view.props.hexpand=True
        self._tree_view.props.vexpand=True
        self._tree_view.props.activate_on_single_click = True
        self._tree_view.props.search_column = 2  # Name column
        self._tree_view.get_selection().set_mode(Gtk.SelectionMode.BROWSE)
        tree_view_sw.add(self._tree_view)

        name_col = Gtk.TreeViewColumn(title='Name')
        self._tree_view.append_column(name_col)

        name_col_cell_icon = Gtk.CellRendererPixbuf()
        name_col.pack_start(name_col_cell_icon, False)
        name_col.add_attribute(name_col_cell_icon, 'pixbuf', 1)

        name_col_cell_name = Gtk.CellRendererText(xpad=5, ypad=5)
        name_col.pack_start(name_col_cell_name, True)
        name_col.add_attribute(name_col_cell_name, 'text', 2)

        self._tree_view.connect('row-activated', self._hdl_tree_view_row_activated)
        self._tree_view.get_selection().connect('changed', self._hdl_tree_selection_changed)

    def new_item(self, id_: str, icon: GdkPixbuf.Pixbuf, name: str) -> 'ItemHandle':
        iter_ = self._model.append((id_, icon, name))
        return ItemHandle(self._model, Gtk.TreeRowReference(self._model, self._model.get_path(iter_)))

    def _item_id_from_path(self, path: Gtk.TreePath) -> str:
        return self._item_id_from_iter(self._model.get_iter(path))

    def _item_id_from_iter(self, iter_: Gtk.TreeIter) -> str:
        return self._model.get_value(iter_, 0)

    def _hdl_tree_selection_changed(self, tree_selection: Gtk.TreeSelection) -> None:
        iter_ = tree_selection.get_selected()[1]

        if iter_ is None:
            self._set_selection(None)
            return

        self._set_selection(self._item_id_from_iter(iter_))

    def _hdl_tree_view_row_activated(self, tree_view: Gtk.TreeView, path: Gtk.TreePath, col: Gtk.TreeViewColumn) -> None:
        self._set_selection(self._item_id_from_path(path))

    @GObject.Property
    def selection(self) -> str:
        return self._selection

    def _set_selection(self, id_: Optional[str]) -> None:
        self._selection = id_
        self.notify('selection')


class ItemHandle(GObject.GObject):
    def __init__(self, model: Gtk.TreeModel, rowref: Gtk.TreeRowReference):
        self._model = model
        self._rowref = rowref

        super().__init__()

    def _model_get_value(self, idx: int) -> Any:
        return self._model.get_value(self._model.get_iter(self._rowref.get_path()), idx)

    @GObject.Property
    def id(self) -> str:
        return self._model_get_value(0)

    @GObject.Property
    def icon(self) -> GdkPixbuf.Pixbuf:
        return self._model_get_value(1)

    @GObject.Property
    def name(self) -> str:
        return self._model_get_value(2)
