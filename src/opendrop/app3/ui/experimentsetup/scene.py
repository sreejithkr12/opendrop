import asyncio
from abc import abstractmethod
from typing import Any, Sequence, Generic, TypeVar

from gi.repository import Gtk
from typing_extensions import Protocol

from opendrop import observer
from opendrop.app2.ui.observerchooser.observer_chooser_dlg import ObserverChooserDialog, ObserverChooserDialogReceiver
from opendrop.mvp2.gtk.application import GtkApplicationScene
from opendrop.observer.bases import ObserverType
from opendrop.utility.events import Event

VT = TypeVar('VT')
PT = TypeVar('PT')
CT = TypeVar('CT')


class SetupWindowViewProvider(Protocol[VT]):
    @abstractmethod
    def __call__(self, window: Gtk.Window) -> VT: pass


class SetupWindowPresenterProvider(Protocol[PT, VT, CT]):
    @abstractmethod
    def __call__(self, view: VT, config_obj: CT) -> PT: pass


class ExperimentSetupSceneView(Generic[VT]):
    class ObserverChooserDlgHandle:
        def __init__(self, target_dlg: ObserverChooserDialog):
            self._target_dlg = target_dlg

        def show(self) -> None:
            self._target_dlg.show()

        def destroy(self) -> None:
            self._target_dlg.destroy()

    def __init__(self, g_app: Gtk.Application, setup_win_view_pvdr: SetupWindowViewProvider[VT]) -> None:
        self._g_app = g_app
        self._setup_view_cls = setup_win_view_pvdr

        self.on_go_back = Event()  # emits: ()

        self._build_ui()

    def _build_ui(self) -> None:
        self._primary_win = Gtk.ApplicationWindow(application=self._g_app)
        self.primary_win_view = self._setup_view_cls(self._primary_win)

    def destroy(self) -> None:
        self._primary_win.destroy()

    def set_config_obj(self, model: Any) -> None:
        self._primary_win.set_config_obj(model)

    def go_back(self) -> None:
        self.on_go_back.fire()

    def show_primary_win(self) -> None:
        self._primary_win.show()

    def hide_primary_win(self) -> None:
        self._primary_win.hide()

    def new_observer_chooser_dlg(self, dlg_rcv: ObserverChooserDialogReceiver, o_types: Sequence[ObserverType])\
            -> ObserverChooserDlgHandle:
        dlg = ObserverChooserDialog(o_types, modal=True, transient_for=self._primary_win)
        dlg.connect('delete-event', lambda *_: True)  # Return true to prevent destroying the dialog.
        dlg_rcv.set_target_dlg(dlg)
        return self.ObserverChooserDlgHandle(dlg)


class ExperimentSetupScenePresenter(Generic[PT, VT, CT]):
    def __init__(self, view: ExperimentSetupSceneView[VT], config_obj: CT,
                 setup_win_presenter_cls: SetupWindowPresenterProvider[PT, VT, CT])\
            -> None:
        self.view = view
        self._config_obj = config_obj
        self._setup_win_presenter = setup_win_presenter_cls(view.primary_win_view, config_obj)
        asyncio.get_event_loop().create_task(self._post_init())

    async def _post_init(self) -> None:
        self.view.show_primary_win()

        # outer = self
        #
        # class Receiver(ObserverChooserDialogReceiver):
        #     def __init__(self):
        #         super().__init__()
        #         self.done = asyncio.Event()
        #
        #     def response_ok(self):
        #         outer._config_obj.change_observer(self.observer_type, self.options)
        #         outer.view.set_config_obj(outer._config_obj)
        #         self.done.set()
        #
        #     def response_cancel(self):
        #         outer.view.go_back()
        #         self.done.set()
        #
        # dlg_rcv = Receiver()
        #
        # dlg_h = self.view.new_observer_chooser_dlg(dlg_rcv, self._config_obj.available_observer_types)
        # dlg_h.show()
        #
        # await dlg_rcv.done.wait()
        # dlg_h.destroy()

        #self._config_obj.change_observer(imageacquisition.types.USB_CAMERA, {'camera_index': 0})

        self._config_obj.change_observer(observer.types.IMAGE_SLIDESHOW, {'image_paths': [
            '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image0.png',
            '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image1.png',
            '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image2.png',
            '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image3.png',
            '/Users/Eugene/PycharmProjects/opendrop/tests/samples/images/image4.png'
        ], 'timestamps': range(5)})


class ExperimentSetupScene(GtkApplicationScene):
    class Response:
        pass

    class ResponseReturn(Response):
        pass

    def __init__(self, config_obj: Any, *args, _setup_win_view_cls: type,
                 _setup_win_presenter_cls: type, **kwargs):
        super().__init__(*args, **kwargs)

        self.on_response = Event()  # emits: (response: Response)

        self._view = ExperimentSetupSceneView(g_app=self._g_app, setup_win_view_pvdr=_setup_win_view_cls)
        self._presenter = ExperimentSetupScenePresenter(self._view, config_obj=config_obj,
                                                        setup_win_presenter_cls=_setup_win_presenter_cls)

        self._set_up()

    def _set_up(self) -> None:
        self._event_conns = [
            self._view.on_go_back.connect(self.hdl_view_go_back)
        ]

    def destroy(self) -> None:
        # Disconnect event connections.
        for conn in self._event_conns:
            conn.disconnect()

        # Tear down view and presenter.
        # self._presenter.destroy()
        self._view.destroy()

        super().destroy()

    def hdl_view_go_back(self) -> None:
        self._go_back()

    def _go_back(self) -> None:
        self.on_response.fire(self.ResponseReturn())
