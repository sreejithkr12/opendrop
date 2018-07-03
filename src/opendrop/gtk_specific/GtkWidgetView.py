from gi.repository import Gtk

from opendrop.gtk_specific.GtkView import GtkView
from opendrop.mvp.View import View


class GtkWidgetView(GtkView):

    """Each view represents a Gtk widget.

    Attributes:
        container  The container widget that should store all child widgets.
    """

    def __init__(self, gtk_app: Gtk.Application) -> None:
        super().__init__(gtk_app)

        self._initialized = False  # type: bool

        self.container = Gtk.Box()  # type: Gtk.Box

        self.events.on_setup_done.connect(self.post_setup, once=True)

    def post_setup(self) -> None:
        if not self.hidden:
            self.container.show()

        self._initialized = True

    @View.hidden.setter
    def hidden(self, value: bool) -> None:
        View.hidden.__set__(self, value)

        if not self._initialized or self.destroyed:
            return

        if value:
            self.container.hide()
        else:
            self.container.show()

    def destroy(self) -> None:
        View.destroy(self)

        self.container.destroy()
