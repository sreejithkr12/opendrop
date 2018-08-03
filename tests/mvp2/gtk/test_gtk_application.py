import functools
import gc
import weakref
from asyncio import AbstractEventLoop

from opendrop.mvp2.gtk.application import GtkApplication
from opendrop.mvp2.gtk.scene import GtkScene
from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.view import View


# Stub view and presenter classes.
class BlankView(View):
    pass


class BlankPresenter(Presenter):
    pass


def test_quit():
    target_exit_val = object()

    class MyApplication(GtkApplication):
        async def _main(self):
            self.quit(target_exit_val)

    # Create and run the test application.
    my_app = MyApplication()
    exit_val = my_app.run()

    # Test exit value.
    assert exit_val == target_exit_val


def test_quit_with_no_arguments():
    target_exit_val = object()

    class MyApplication(GtkApplication):
        async def _main(self):
            self.quit()

    # Create and run the test application.
    my_app = MyApplication()
    exit_val = my_app.run()

    # Test exit value.
    assert exit_val is None


def test_initialise_scene_and_quit():
    checkpoints = []

    # Test scene class.
    class MyScene(GtkScene):
        def _m_init(self, one, two, a, b, *args, **kwargs):
            super()._m_init(*args, **kwargs)
            checkpoints.append(('_init', (self.g_app, self, (one, two), {'a': a, 'b': b})))

    MyScene = functools.partial(MyScene,
        _view_cls=BlankView,
        _presenter_cls=BlankPresenter
    )

    my_scene_args = (1, 2)
    my_scene_kwargs = {'a': 3, 'b': 4}

    class MyApplication(GtkApplication):
        async def _main(self):
            my_scene = self.initialise_scene(MyScene, *my_scene_args, **my_scene_kwargs)

            checkpoints.append(('_main', (self.g_app, my_scene, self.event_loop)))

            self.quit()

    # Create and run the test application.
    my_app = MyApplication()
    my_app.run()

    # Verify checkpoints.
    checkpoint0 = checkpoints.pop(0)
    checkpoint1 = checkpoints.pop(0)

    the_gtk_app = checkpoint0[1][0]
    the_scene = checkpoint0[1][1]

    assert checkpoint0[0] == '_init'
    assert checkpoint0[1][2:4] == (my_scene_args, my_scene_kwargs)

    assert checkpoint1[0] == '_main'
    assert checkpoint1[1][0] is the_gtk_app
    assert checkpoint1[1][1] is the_scene
    assert isinstance(checkpoint1[1][2], AbstractEventLoop)


def test_initialise_scene_holds_reference():
    checkpoints = []

    # Test scene class.
    class MyScene(GtkScene):
        pass

    MyScene = functools.partial(MyScene,
        _view_cls=BlankView,
        _presenter_cls=BlankPresenter
    )

    class MyApplication(GtkApplication):
        async def _main(self):
            my_scene = self.initialise_scene(MyScene)
            my_scene_wref = weakref.ref(my_scene)

            del my_scene
            gc.collect()

            checkpoints.append(('_main', my_scene_wref()))

            self.quit()

    my_app = MyApplication()
    my_app.run()

    assert checkpoints[0][0] == '_main'
    assert checkpoints[0][1] is not None


def test_destroy_scene_releases_reference():
    checkpoints = []

    # Test scene class.
    class MyScene(GtkScene):
        pass

    MyScene = functools.partial(MyScene,
        _view_cls=BlankView,
        _presenter_cls=BlankPresenter
    )

    class MyApplication(GtkApplication):
        async def _main(self):
            my_scene = self.initialise_scene(MyScene)
            my_scene_wref = weakref.ref(my_scene)

            del my_scene
            my_scene_wref().destroy()
            gc.collect()

            checkpoints.append(('_main', my_scene_wref()))

            self.quit()

    my_app = MyApplication()
    my_app.run()

    assert checkpoints[0][0] == '_main'
    assert checkpoints[0][1] is None
