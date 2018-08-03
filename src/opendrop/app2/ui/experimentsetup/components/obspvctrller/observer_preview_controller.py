import functools
from collections import namedtuple
from typing import Callable, List, overload, TypeVar, Optional

from gi.repository import GObject, Gtk

from opendrop.observer.bases import ObserverPreview


T = TypeVar('T')


class ObserverPreviewControllerProvider:
    RealControllerProvider = Callable[['ObserverModelProtocol'], Gtk.Widget]
    EditorContainer = namedtuple('EditorContainer', ('should_control', 'provider'))

    _editors = []  # type: List[EditorContainer]

    @classmethod
    def new_for_preview(cls, preview: ObserverPreview) -> Gtk.Widget:
        for (should_control, controller_provider) in cls._editors:
            if not should_control(preview): continue
            return controller_provider(preview)
        else:
            raise ValueError('Could not find a controller for preview `{}`'.format(preview))

    @overload
    @classmethod
    def register_controller(cls, should_control: Callable[[ObserverPreview], bool], provider: RealControllerProvider)\
            -> None: ...

    @overload
    @classmethod
    def register_controller(cls, should_control: Callable[[ObserverPreview], bool]) -> Callable[[T], T]: ...

    @classmethod
    def register_controller(cls, should_control, provider=None, _decorator: bool = False):
        if provider is None:
            return functools.partial(cls.register_controller, should_control, _decorator=True)

        cls._editors.append(cls.EditorContainer(should_control, provider))

        if _decorator:
            return provider


class ObserverPreviewControllerWrapper(Gtk.Box):
    _preview = None  # type: Optional[ObserverPreview]
    _current_preview_controller = None  # type: Optional[Gtk.Widget]

    @GObject.Property
    def preview(self) -> Optional[ObserverPreview]:
        return self._preview

    @preview.setter
    def preview(self, new_preview: Optional[ObserverPreview]) -> None:
        if self._current_preview_controller is not None:
            self._current_preview_controller.destroy()
            self._current_preview_controller = None

        self._preview = new_preview

        if new_preview is None:
            return

        self._current_preview_controller = ObserverPreviewControllerProvider.new_for_preview(new_preview)
        self.add(self._current_preview_controller)
        self._current_preview_controller.show()


ObserverPreviewController = ObserverPreviewControllerWrapper
