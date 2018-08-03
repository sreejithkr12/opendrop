import functools
from typing import TypeVar

from gi.repository import Gtk

from opendrop.mvp2.environment import Environment
from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.view import View
from opendrop.utility.events import Event

MT, VT, PT = TypeVar('MT'), TypeVar('VT', bound=View), TypeVar('PT', bound=Presenter)


class GtkSceneView(View):
    def _m_init(self, g_app: Gtk.Application):
        self.g_app = g_app


class GtkScene(Environment):
    def _m_init(self, g_app: Gtk.Application) -> None:
        self.g_app = g_app

        self.on_destroyed = Event()  # emits: ()

        self._view_opts['g_app'] = g_app

    def _tear_down(self):
        pass

    def destroy(self) -> None:
        self._tear_down()
        self.on_destroyed.fire()
