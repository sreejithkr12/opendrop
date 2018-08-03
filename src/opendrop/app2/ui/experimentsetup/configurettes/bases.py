from abc import abstractmethod

from gi.repository import GdkPixbuf, Gtk


class Configurette:
    def __init__(self, id_: str, icon: GdkPixbuf.Pixbuf, name: str):
        self._id = id_
        self._icon = icon
        self._name = name

    @abstractmethod
    def create_editor(self) -> Gtk.Widget:
        pass
