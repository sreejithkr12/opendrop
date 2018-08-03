from unittest.mock import Mock

from opendrop.mvp2.gtk.scene import GtkScene
from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.view import View


# Stub view and presenter classes.
class BlankView(View):
    pass


class BlankPresenter(Presenter):
    pass


def test_init():
    checkpoints = []

    # Test scene class.
    class MyScene(GtkScene):
        def _m_init(self, **opts):
            super()._m_init(**opts)
            checkpoints.append(('_init', self.g_app))

    g_app = Mock()
    my_scene = MyScene(g_app=g_app, _view_cls=BlankView, _presenter_cls=BlankPresenter)

    assert checkpoints == [
        ('_init', g_app)
    ]


def test_destroy():
    checkpoints = []

    # Test scene class.
    class MyScene(GtkScene):
        def _m_init(self, **opts):
            super()._m_init(**opts)

        def _tear_down(self):
            checkpoints.append(('_tear_down',))

    my_scene = MyScene(g_app=Mock(), _view_cls=BlankView, _presenter_cls=BlankPresenter)

    cb = Mock()
    my_scene.on_destroyed.connect(cb, immediate=True)

    my_scene.destroy()
    cb.assert_called_once_with()

    assert checkpoints == [
        ('_tear_down',)
    ]
