from opendrop.mvp2.gtk.componentstuff.app_win import GtkAppWinComponentView, GtkAppWinComponent
from opendrop.mvp2.presenter import Presenter


class MyWindowView(GtkAppWinComponentView):
    pass


class MyWindowPresenter(Presenter[MyWindowView]):
    pass


class _MyWindow(GtkAppWinComponent):
    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()


class MyWindow(_MyWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=MyWindowView,
            _presenter_cls=MyWindowPresenter,
            *args, **kwargs
        )
