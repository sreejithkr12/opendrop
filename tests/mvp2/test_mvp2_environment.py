from unittest.mock import Mock

from opendrop.mvp2.environment import Environment
from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.view import View


# Stub view and presenter classes.
class BlankView(View):
    pass

class BlankPresenter(Presenter):
    pass


def test_initialisation():
    checkpoints = []

    # Test environment class.
    class MyEnvironment(Environment):
        def _m_init(self, *args, **kwargs):
            checkpoints.append(('_init', (args, kwargs)))

            self._view_opts['my_view_opt'] = 1
            self._presenter_opts['my_presenter_opt'] = 2

        def _set_up(self):
            checkpoints.append(('_set_up', (self.view, self.presenter)))

    # View and presenter providers.
    the_view = None
    the_presenter = None

    class MyView:
        def __init__(self, *args, **kwargs):
            nonlocal the_view
            checkpoints.append(('MyView.__init__', (args, kwargs)))
            the_view = self

    class MyPresenter:
        def __init__(self, *args, **kwargs):
            nonlocal the_presenter
            checkpoints.append(('MyPresenter.__init__', (args, kwargs)))
            the_presenter = self

    # Construct new environment.
    my_args = (1, 2, 3)
    my_kwargs = dict(my_opt0=0, my_opt1=1)
    my_env = MyEnvironment(_view_cls=MyView, _presenter_cls=MyPresenter, *my_args, **my_kwargs)

    # Verify checkpoints.

    # No preference to the order that view_provider() and presenter_provider() should be called.
    checkpoints[1:3] = sorted(checkpoints[1:3])

    assert checkpoints == [
        ('_init', (my_args, my_kwargs)),
        ('MyPresenter.__init__', ((), {'my_presenter_opt': 2})),
        ('MyView.__init__', ((), {'my_view_opt': 1})),
        ('_set_up', (the_view, the_presenter))
    ]


def test_set_up_view_and_presenter():
    checkpoints = []

    # Test environment class.
    class MyEnvironment(Environment):
        def _set_up(self):
            self.view.set_up()
            self.presenter.set_up()

            checkpoints.append(('_set_up success',))

    my_env = MyEnvironment(_view_cls=BlankView, _presenter_cls=BlankPresenter)

    assert checkpoints == [
        ('_set_up success',)
    ]
