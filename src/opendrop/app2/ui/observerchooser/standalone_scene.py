"""Convenience scene with an imageacquisition chooser window."""

from opendrop.app2.ui.observerchooser.observer_chooser_dlg import ObserverChooserDialog
from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.gtk.scene import GtkSceneView, GtkScene
from opendrop.observer.service import ObserverService


class ObserverChooserSceneView(GtkSceneView):
    def _m_init(self, observer_service: ObserverService, **kwargs) -> None:
        super()._m_init(**kwargs)
        self._observer_service = observer_service

    def _set_up(self) -> None:
        self.observer_chooser_win = ObserverChooserDialog(o_types=self._observer_service.get_types())
        self.observer_chooser_win.show()

        def hdl_response(w, resp):
            print(resp, w.observer_type, w.options)

        self.observer_chooser_win.connect('response', hdl_response)


class ObserverChooserScenePresenter(Presenter):
    pass


class _ObserverChooserScene(GtkScene):
    def _m_init(self, observer_service: ObserverService, *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)
        self._view_opts['observer_service'] = observer_service  # todo: move into presenter

    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()


class ObserverChooserScene(_ObserverChooserScene):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ObserverChooserSceneView,
            _presenter_cls=ObserverChooserScenePresenter,
            *args, **kwargs
        )
