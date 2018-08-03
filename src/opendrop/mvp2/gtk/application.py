import asyncio
import functools
from abc import abstractmethod
from asyncio import AbstractEventLoop
from typing import Callable, Optional, Any, TypeVar, List

from gi.repository import Gtk

from opendrop.gtk_specific.GtkHookLoopPolicy import GtkHookLoopPolicy
from opendrop.utility.events import Event


class GtkApplicationScene:
    def __init__(self, g_app: Gtk.Application):
        self._g_app = g_app
        self.on_destroyed = Event()  # emits: None

    def destroy(self) -> None:
        self.on_destroyed.fire()


ST = TypeVar('ST', bound=GtkApplicationScene)


class GtkApplication:
    APPLICATION_ID = None  # type: Optional[str]

    def __init__(self):
        # TODO: CUSTOM EVENT LOOP HERE
        self.event_loop = None  # type: Optional[AbstractEventLoop]

        self._active_scenes = []  # type: List[GtkApplicationScene]

        self.g_app = Gtk.Application(application_id=self.APPLICATION_ID)

        # Connect Gtk.Application events to this instance's handlers
        for signal_name, handler in (
            ('activate', self._hdl_g_app_activate),
        ): self.g_app.connect(signal_name, handler)

        self._exit_val = None  # type: Any

    def run(self) -> Any:
        # GtkHookLoopPolicy is a bit of a hack.
        asyncio.set_event_loop_policy(GtkHookLoopPolicy())
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.event_loop = asyncio.get_event_loop()

        self.event_loop.run_forever()

        # Execution will halt here until the application quits.
        # Calling self.g_app.run() will cause self.g_app to emit an 'activate' signal, which is handled by
        # _hdl_g_app_activate(), so in a sense, the program logic will continue there.
        self.g_app.run()

        # Exit value should have been set when quit() is called.
        return self._exit_val

    def quit(self, exit_value: Any = None):
        self._exit_val = exit_value

        # Stop the event loop and reset the event loop policy to the default policy
        self.event_loop.stop()
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        asyncio.set_event_loop(asyncio.new_event_loop())

        # "Cancel" out the previous hold in _hdl_g_app_activate(), not *necessary* since we're about to call quit()
        # on the application anyway.
        self.g_app.release()

        self.g_app.quit()

    def initialise_scene(self, scene_provider: Callable[..., ST], *scene_args, **scene_kwargs) -> ST:
        new_scene = scene_provider(*scene_args, **scene_kwargs, g_app=self.g_app)
        new_scene.on_destroyed.connect(functools.partial(self.release_scene, new_scene), strong_ref=True, once=True,
                                       immediate=True)

        self._active_scenes.append(new_scene)

        return new_scene

    def release_scene(self, scene: GtkApplicationScene) -> None:
        self._active_scenes.remove(scene)

    def _hdl_g_app_activate(self, g_app: Gtk.Application):
        # Increase the use count of self.g_app, otherwise, the application will quit after this function returns since
        # _main() is not immediately executed (it is queued onto the event loop) so when this function returns, the use
        # count will remain at zero. See documentation for Gio.Application.hold()[1] and Gio.Application.release()[2].
        # [1] https://lazka.github.io/pgi-docs/Gio-2.0/classes/Application.html#Gio.Application.hold
        # [2] https://lazka.github.io/pgi-docs/Gio-2.0/classes/Application.html#Gio.Application.release
        self.g_app.hold()

        self.event_loop.create_task(self._main())

    @abstractmethod
    async def _main(self): pass
