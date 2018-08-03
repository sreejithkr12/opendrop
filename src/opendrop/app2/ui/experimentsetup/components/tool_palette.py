from gi.repository import Gtk

from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponentView, GtkGridComponent
from opendrop.mvp2.presenter import Presenter


class ToolPaletteView(GtkGridComponentView):
    pass


class ToolPalettePresenter(Presenter[ToolPaletteView]):
    pass


class ToolPaletteModel:
    pass


class _ToolPalette(GtkGridComponent):
    def _m_init(self, target: Gtk.Widget, *args, **kwargs):
    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()


class ToolPalette(_ToolPalette):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ToolPaletteView,
            _presenter_cls=ToolPalettePresenter,
            *args, **kwargs
        )
