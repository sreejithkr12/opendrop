from typing import List, Optional, Any

from gi.repository import Gtk, GObject, GdkPixbuf

from opendrop.app2.ui.experimentsetup.configurettes.bases import Configurette
from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponentView, GtkGridComponent
from opendrop.mvp2.presenter import Presenter
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.events import Event


class ObjectExplorer(Gtk.Grid):
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

        self._tree_view.connect('row-activated', self.hdl_tree_view_row_activated)
        self._tree_view.get_selection().connect('changed', self.hdl_tree_selection_changed)

    def new_object(self, id_: str, icon: GdkPixbuf.Pixbuf, name: str) -> 'ItemHandle':
        iter_ = self._model.append((id_, icon, name))
        return ObjectHandle(self._model, Gtk.TreeRowReference(self._model, self._model.get_path(iter_)))

    def object_id_from_path(self, path: Gtk.TreePath) -> str:
        return self.object_id_from_iter(self._model.get_iter(path))

    def object_id_from_iter(self, iter_: Gtk.TreeIter) -> str:
        return self._model.get_value(iter_, 0)

    def hdl_tree_selection_changed(self, tree_selection: Gtk.TreeSelection) -> None:
        iter_ = tree_selection.get_selected()[1]

        if iter_ is None:
            self._set_selection(None)
            return

        self._set_selection(self.object_id_from_iter(iter_))

    def hdl_tree_view_row_activated(self, tree_view: Gtk.TreeView, path: Gtk.TreePath, col: Gtk.TreeViewColumn) -> None:
        self._set_selection(self.object_id_from_path(path))

    @GObject.Property
    def selection(self) -> str:
        return self._selection

    def _set_selection(self, id_: Optional[str]) -> None:
        self._selection = id_
        self.notify('selection')


class ObjectHandle(GObject.GObject):
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


class ConfigurationSidebarView(GtkGridComponentView):
    class EmptyEditor(Gtk.Label):
        def __init__(self):
            super().__init__(justify=Gtk.Justification.CENTER, wrap=True)
            self.set_markup(
                '<span font_desc=\'11.0\'>{}</span>'
                .format('Select an item to configure.')
            )

    def _m_init(self, **opts):
        super()._m_init(**opts)
        self.bn_selection = AtomicBindableAdapter()  # type: AtomicBindableAdapter[str]

    def _set_up(self) -> None:
        self.container.props.width_request = 200
        self.container.props.hexpand = False

        # header_lbl = Gtk.Label(hexpand=True)
        # header_lbl.set_markup(
        #     '<span font_desc=\'11.0\'>{}</span>'
        #     .format('Configuration')
        # )
        # header_lbl.get_style_context().add_class('gray-box')
        # header_lbl_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        # header_lbl_css.load_from_data(bytes('''
        #      .gray-box {
        #          background-color: gainsboro;
        #          padding: 10px 5px 10px 5px;
        #      }
        #  ''', encoding='utf-8'))
        # header_lbl.get_style_context().add_provider(header_lbl_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        #
        # self.container.attach(header_lbl, 0, 0, 1, 1)

        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.container.attach(paned, 0, 0, 1, 1)

        self._explorer = ObjectExplorer(expand=True, height_request=100)

        self.bn_selection.getter = lambda: self._explorer.selection
        self._explorer.connect('notify::selection', lambda *_: self.bn_selection.poke())

        self._editor_ctn = Gtk.ScrolledWindow(expand=True, height_request=100)
        self._current_editor = None  # type: Optional[Gtk.Widget]
        self.change_editor(None)

        paned.pack1(self._explorer, resize=True, shrink=False)
        paned.pack2(self._editor_ctn, resize=True, shrink=False)

    @AtomicBindable.property_adapter
    def selection(self) -> AtomicBindable[str]:
        return self.bn_selection

    def new_explorer_object(self, id_: str, icon: GdkPixbuf.Pixbuf, name: str) -> ObjectHandle:
        return self._explorer.new_object(id_, icon, name)

    def change_editor(self, new_editor: Optional[Gtk.Widget]) -> None:
        if self._current_editor is not None:
            self._editor_ctn.remove(self._current_editor)
            self._current_editor.destroy()
            self._current_editor = None

        if new_editor is None:
            new_editor = self.EmptyEditor()

        self._editor_ctn.add(new_editor)
        self._current_editor = new_editor
        new_editor.show()


class ConfigurationSidebarModel:
    def __init__(self):
        self.on_new_configurette = Event()  # emits: (new_configurette: Configurette)
        self._configurettes = []  # type: List[Configurette]

    def add_configurette(self, cfette: Configurette) -> None:
        self._configurettes.append(cfette)
        self.on_new_configurette.fire(cfette)

    def find_configurette_by_id(self, id_: str) -> Configurette:
        for cfette in self._configurettes:
            if cfette._id == id_:
                return cfette
        else:
            raise ValueError("No configurette with id '{}' found".format(id_))


class ConfigurationSidebarPresenter(Presenter[ConfigurationSidebarView]):
    def _set_up(self):
        self._event_conns = [
            self.model.on_new_configurette.connect(self.hdl_model_new_configurette),
            self.view.bn_selection.on_changed.connect(self.hdl_view_selection_changed)
        ]

        self._active_editor = None  # type: Optional[str]

    def _tear_down(self) -> None:
        # Disconnect event connections.
        for conn in self._event_conns:
            conn.disconnect()

    def hdl_model_new_configurette(self, cfette: Configurette) -> None:
        self.view.new_explorer_object(id_=cfette._id, icon=cfette._icon, name=cfette._name)

    def hdl_view_selection_changed(self) -> None:
        cfette_id = self.view.selection

        if self._active_editor == cfette_id:
            # This editor is already active.
            return

        self._active_editor = cfette_id

        if cfette_id is None:
            self.view.change_editor(None)
        else:
            cfette = self.model.find_configurette_by_id(cfette_id)
            cfette_editor = cfette.create_editor()
            self.view.change_editor(cfette_editor)


class _ConfigurationSidebar(GtkGridComponent):
    view = ...  # type: ConfigurationSidebarView
    presenter = ...  # type: ConfigurationSidebarPresenter

    def _m_init(self, **opts) -> None:
        super()._m_init(**opts)
        self._model = ConfigurationSidebarModel()

    def _set_up(self) -> None:
        self.view.set_up()

        self.presenter.model = self._model
        self.presenter.set_up()

    def _tear_down(self) -> None:
        # Tear down view and presenter.
        self.presenter.tear_down()
        self.view.tear_down()

    def add_configurette(self, cfette: Configurette) -> None:
        self._model.add_configurette(cfette)


class ConfigurationSidebar(_ConfigurationSidebar):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ConfigurationSidebarView,
            _presenter_cls=ConfigurationSidebarPresenter,
            *args, **kwargs,
        )
