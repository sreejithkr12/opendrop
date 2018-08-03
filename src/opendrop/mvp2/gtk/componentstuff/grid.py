from gi.repository import Gtk

from opendrop.mvp2.environment import Environment
from opendrop.mvp2.gtk.componentstuff.mixins.widget import GtkWidgetComponentMixin
from opendrop.mvp2.view import View


class GtkGridComponentView(View):
    def _m_init(self, container: Gtk.Grid):
        self.container = container


class GtkGridComponent(Environment, Gtk.Grid, GtkWidgetComponentMixin):
    def _m_init(self, **properties):
        Gtk.Grid.__init__(self, **properties)
        GtkWidgetComponentMixin._m_init(self)

        self._view_opts['container'] = self
