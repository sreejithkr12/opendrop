from pytest import raises

from opendrop.mvp2.datatypes import ViewPresenterState
from opendrop.mvp2.view import View


def test_initialisation():
    checkpoints = []

    # Test view class.
    class MyView(View):
        def _m_init(self, **kwargs):
            checkpoints.append(('_init', kwargs))

    # Construct new view.
    extra_opts = {'my_opt0': 0, 'my_opt1': 1}
    my_view = MyView(**extra_opts)

    # Verify checkpoints.

    assert checkpoints == [
        ('_init', extra_opts)
    ]


def test_set_up():
    checkpoints = []

    # Test view class.
    class MyView(View):
        def _m_init(self):
            pass

        def _set_up(self):
            checkpoints.append(('_set_up', self.state))

    # Construct new view.
    my_view = MyView()
    assert my_view.state == ViewPresenterState.INITIALISED
    my_view.set_up()
    assert my_view.state == ViewPresenterState.UP

    assert checkpoints == [
        ('_set_up', ViewPresenterState.SETTING_UP)
    ]


def test_tear_down():
    checkpoints = []

    # Test view class.
    class MyView(View):
        def _m_init(self):
            pass

        def _tear_down(self):
            checkpoints.append(('_tear_down', self.state))

    # Construct and set up new view.
    my_view = MyView()
    my_view.set_up()

    # Tear down view
    my_view.tear_down()

    # Verify checkpoints.
    assert checkpoints == [
        ('_tear_down', ViewPresenterState.TEARING_DOWN)
    ]

def test_set_up_called_twice_and_after_tear_down():
    # Test view class.
    class MyView(View):
        pass

    # Construct new view.
    my_view = MyView()

    my_view.set_up()

    # set_up() can't be called twice.
    with raises(ValueError):
        my_view.set_up()

        my_view.tear_down()

    # set_up() can't be called after tear_down().
    with raises(ValueError):
        my_view.set_up()


def test_tear_down_before_set_up_and_called_twice():
    # Test view class.
    class MyView(View):
        pass

    # Construct new view.
    my_view = MyView()

    # tear_down() can't be called before set_up().
    with raises(ValueError):
        my_view.tear_down()

    my_view.set_up()
    my_view.tear_down()

    # tear_down() can't be called twice.
    with raises(ValueError):
        my_view.tear_down()

