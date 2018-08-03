from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.gtk.scene import GtkSceneView, GtkScene


class MySceneView(GtkSceneView):
    pass


class MyScenePresenter(Presenter[MySceneView]):
    pass


class _MyScene(GtkScene):
    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()


class MyScene(_MyScene):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=MySceneView,
            _presenter_cls=MyScenePresenter,
            *args, **kwargs
        )
