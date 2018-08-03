from typing import Optional

from gi.repository import Gtk

from opendrop.mvp2.environment import Environment
from opendrop.mvp2.gtk.componentstuff.mixins.widget import GtkWidgetComponentMixin
from opendrop.mvp2.view import View


class GtkAppWinComponentView(View):
    WINDOW_TITLE = None  # type: Optional[str]

    def _m_init(self, window: Gtk.ApplicationWindow) -> None:
        self.window = window
        self.window.props.title = self.WINDOW_TITLE


class GtkAppWinComponent(Environment, Gtk.ApplicationWindow, GtkWidgetComponentMixin):
    def _m_init(self, application: Gtk.Application, *args, **properties) -> None:
        Gtk.ApplicationWindow.__init__(self, application=application, *args, **properties)
        GtkWidgetComponentMixin._m_init(self)

        self._view_opts['window'] = self
