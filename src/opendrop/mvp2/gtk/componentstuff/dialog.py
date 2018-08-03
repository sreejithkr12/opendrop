from typing import Optional

from gi.repository import Gtk

from opendrop.mvp2.environment import Environment
from opendrop.mvp2.gtk.componentstuff.mixins.widget import GtkWidgetComponentMixin
from opendrop.mvp2.view import View


class GtkDialogComponentView(View):
    WINDOW_TITLE = None  # type: Optional[str]

    def _m_init(self, dialog: Gtk.Dialog) -> None:
        self.dialog = dialog
        self.dialog.props.title = self.WINDOW_TITLE


class GtkDialogComponent(Environment, Gtk.Dialog, GtkWidgetComponentMixin):
    def _m_init(self, *args, **properties) -> None:
        Gtk.Dialog.__init__(self, *args, **properties)
        GtkWidgetComponentMixin._m_init(self)

        self._view_opts['dialog'] = self
