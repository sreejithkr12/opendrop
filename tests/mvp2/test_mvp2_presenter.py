from unittest.mock import Mock

from pytest import raises

from opendrop.mvp2.datatypes import ViewPresenterState
from opendrop.mvp2.presenter import Presenter
from opendrop.mvp2.view import View


# todo: make presenter templated

# Stub view class.
class BlankView(View):
    pass


def test_initialisation():
    checkpoints = []

    # Test presenter class.
    class MyPresenter(Presenter):
        def _m_init(self, **kwargs):
            checkpoints.append(('_init', kwargs))

    # Construct new presenter.
    extra_opts = {'my_opt0': 0, 'my_opt1': 1}
    my_presenter = MyPresenter(**extra_opts)

    # Verify checkpoints.

    assert checkpoints == [
        ('_init', extra_opts)
    ]


def test_set_up():
    checkpoints = []

    # Test presenter class.
    class MyPresenter(Presenter):
        def _set_up(self):
            checkpoints.append(('_set_up', (self.state, self.view.state)))

    # Construct new presenter.
    my_presenter = MyPresenter()
    assert my_presenter.state == ViewPresenterState.INITIALISED
    assert my_presenter.view is None

    # Try to setup when view is None.
    with raises(ValueError):
        my_presenter.set_up()

    # Assign `my_presenter` a view
    my_view = BlankView()
    my_presenter.view = my_view

    # but don't setup the view, presenter still shouldn't be able to set up.
    with raises(ValueError):
        my_presenter.set_up()

    # The presenter's assigned view must be set up
    my_view.set_up()

    # before the presenter can be set up
    my_presenter.set_up()
    assert my_presenter.state == ViewPresenterState.UP

    assert checkpoints == [
        ('_set_up', (ViewPresenterState.SETTING_UP, ViewPresenterState.UP))
    ]


def test_change_view_when_up():
    # Test presenter class.
    class MyPresenter(Presenter):
        pass

    # Construct new presenter.
    my_view = BlankView()
    my_view.set_up()
    my_presenter = MyPresenter()
    my_presenter.view = my_view

    my_presenter.set_up()

    # Make sure view can't be changed after presenter is set up.
    with raises(ValueError):
        my_presenter.view = Mock()


def test_tear_down():
    checkpoints = []

    # Test presenter class.
    class MyPresenter(Presenter):
        def _tear_down(self):
            checkpoints.append(('_tear_down', self.state))

    # Construct new presenter.
    my_view = BlankView()
    my_view.set_up()
    my_presenter = MyPresenter()
    my_presenter.view = my_view

    my_presenter.set_up()
    my_presenter.tear_down()

    # Verify checkpoints.
    assert checkpoints == [
        ('_tear_down', ViewPresenterState.TEARING_DOWN)
    ]

    # Make sure view can't be changed after presenter is teared down.
    with raises(ValueError):
        my_presenter.view = Mock()


def test_change_view_while_setting_up_or_tearing_down():
    checkpoints = []

    # Test presenter class.
    class MyPresenter(Presenter):
        def _set_up(self):
            try:
                self.view = Mock()
            except ValueError:
                checkpoints.append(('change view in _set_up failed',))

        def _tear_down(self):
            try:
                self.view = Mock()
            except ValueError:
                checkpoints.append(('change view in _tear_down failed',))

    # Construct new presenter.
    my_view = BlankView()
    my_view.set_up()
    my_presenter = MyPresenter()
    my_presenter.view = my_view

    my_presenter.set_up()

    # Verify checkpoints.
    assert checkpoints == [
        ('change view in _set_up failed',)
    ]

    # Clear checkpoints
    checkpoints = []

    my_presenter.tear_down()

    # Verify checkpoints.
    assert checkpoints == [
        ('change view in _tear_down failed',)
    ]


def test_set_up_called_twice_and_after_tear_down():
    # Test presenter class.
    class MyPresenter(Presenter):
        pass

    # Construct new presenter.
    my_view = BlankView()
    my_view.set_up()
    my_presenter = MyPresenter()
    my_presenter.view = my_view

    my_presenter.set_up()

    # set_up() can't be called twice.
    with raises(ValueError):
        my_presenter.set_up()

    my_presenter.tear_down()

    # set_up() can't be called after tear_down().
    with raises(ValueError):
        my_presenter.set_up()


def test_tear_down_before_set_up_and_called_twice():
    # Test presenter class.
    class MyPresenter(Presenter):
        pass

    # Construct new presenter.
    my_view = BlankView()
    my_view.set_up()
    my_presenter = MyPresenter()
    my_presenter.view = my_view

    # tear_down() can't be called before set_up().
    with raises(ValueError):
        my_presenter.tear_down()

    my_presenter.set_up()
    my_presenter.tear_down()

    # tear_down() can't be called twice.
    with raises(ValueError):
        my_presenter.tear_down()


# TODO: Test warn if the view is torn down first before the presenter is torn down