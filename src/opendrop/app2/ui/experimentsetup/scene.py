import asyncio
from typing import Any, Type, Sequence, Mapping

from gi.repository import Gtk

from opendrop import observer
from opendrop.app2.analysis import IFTAnalysisConfiguration
from opendrop.app2.ui.observerchooser.observer_chooser_dlg import ObserverChooserDialog, ObserverChooserDialogReceiver
from opendrop.mvp2.gtk.scene import GtkSceneView, GtkScene
from opendrop.mvp2.presenter import Presenter
from opendrop.observer.bases import ObserverType
from opendrop.utility.events import Event
from .components.experiment_setup_window import ExperimentSetupWindow


class ExperimentSetupSceneView(GtkSceneView):
    class ObserverChooserDlgHandle:
        def __init__(self, target_dlg: ObserverChooserDialog):
            self._target_dlg = target_dlg

        def show(self) -> None:
            self._target_dlg.show()

        def destroy(self) -> None:
            self._target_dlg.destroy()

    def _m_init(self, setup_win_cls: Type[ExperimentSetupWindow], *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)
        self._setup_win_cls = setup_win_cls

        self.on_go_back = Event()  # emits: ()

    def _set_up(self) -> None:
        self.primary_win = self._setup_win_cls(self.g_app)

    def _tear_down(self) -> None:
        self.primary_win.destroy()

    def set_config_obj(self, model: Any) -> None:
        self.primary_win.set_config_obj(model)

    def go_back(self) -> None:
        self.on_go_back.fire()

    def show_primary_win(self) -> None:
        self.primary_win.show()

    def hide_primary_win(self) -> None:
        self.primary_win.hide()

    def new_observer_chooser_dlg(self, dlg_rcv: ObserverChooserDialogReceiver, o_types: Sequence[ObserverType])\
            -> 'ExperimentSetupSceneView.ObserverChooserDlgHandle':
        dlg = ObserverChooserDialog(o_types, modal=True, transient_for=self.primary_win)
        dlg.connect('delete-event', lambda *_: True)
        dlg_rcv.set_target_dlg(dlg)
        return self.ObserverChooserDlgHandle(dlg)


class ExperimentSetupScenePresenter(Presenter):
    view = ...  # type: ExperimentSetupSceneView

    def _m_init(self, config_obj: IFTAnalysisConfiguration, **kwargs) -> None:
        super()._m_init(**kwargs)
        self._config_obj = config_obj

    def _set_up(self) -> None:
        asyncio.get_event_loop().create_task(self._aset_up())

    async def _aset_up(self) -> None:
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
        self.view.set_config_obj(self._config_obj)



class _ExperimentSetupScene(GtkScene):
    view = ...  # type: ExperimentSetupSceneView
    presenter = ...  # type: ExperimentSetupScenePresenter

    class Response:
        pass

    class ResponseReturn(Response):
        pass

    def _m_init(self, config_obj: Any, *args, _setup_win_cls: Type[ExperimentSetupWindow], **kwargs):
        super()._m_init(*args, **kwargs)

        self.on_response = Event()  # emits: (response: Response)

        self._view_opts['setup_win_cls'] = _setup_win_cls
        self._presenter_opts['config_obj'] = config_obj

    def _set_up(self):
        self._event_conns = [
            self.view.on_go_back.connect(self.hdl_view_go_back)
        ]

        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        # Disconnect event connections.
        for conn in self._event_conns:
            conn.disconnect()

        # Tear down view and presenter.
        self.presenter.tear_down()
        self.view.tear_down()

    def hdl_view_go_back(self) -> None:
        self._go_back()

    def _go_back(self) -> None:
        self.on_response.fire(self.ResponseReturn())


class ExperimentSetupScene(_ExperimentSetupScene):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ExperimentSetupSceneView,
            _presenter_cls=ExperimentSetupScenePresenter,
            *args, **kwargs
        )
