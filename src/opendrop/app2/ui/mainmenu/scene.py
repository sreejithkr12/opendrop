import functools

from gi.repository import GdkPixbuf, Gtk

from opendrop.app2.ui.mainmenu.components.main_menu_window import MainMenuWindow
from opendrop.mvp2.gtk.scene import GtkSceneView, GtkScene
from opendrop.mvp2.presenter import Presenter
from opendrop.res import path as res
from opendrop.utility.events import Event


class MainMenuSceneView(GtkSceneView):
    LOGO_PATH = str(res/'images'/'logo.png')

    def _m_init(self, **opts):
        super()._m_init(**opts)
        self.on_menu_about_btn_clicked = Event()  # emits: ()
        self.on_menu_settings_btn_clicked = Event()  # emits: ()
        self.on_menu_ift_btn_clicked = Event()  # emits: ()
        self.on_menu_conan_btn_clicked = Event()  # emits: ()

        self.on_request_close = Event()  # emits: ()

        self.on_external_action = Event()  # emits: (action_name: str)
        self.on_about_dlg_response = Event()  # emits: (response: str)

    def _set_up(self) -> None:
        logo_img_pxbf = GdkPixbuf.Pixbuf.new_from_file_at_size(self.LOGO_PATH, width=150, height=-1)

        self.primary_win = MainMenuWindow(self.g_app)
        self.primary_win.connect('about-btn-clicked', lambda w: self.on_menu_about_btn_clicked.fire())
        self.primary_win.connect('settings-btn-clicked', lambda w: self.on_menu_settings_btn_clicked.fire())
        self.primary_win.connect('ift-btn-clicked', lambda w: self.on_menu_ift_btn_clicked.fire())
        self.primary_win.connect('conan-btn-clicked', lambda w: self.on_menu_conan_btn_clicked.fire())
        self.primary_win.connect('delete-event', self.hdl_primary_win_delete_event)

        self.about_dlg = Gtk.AboutDialog(logo=logo_img_pxbf, transient_for=self.primary_win, modal=True)
        self.about_dlg.connect('delete-event', lambda *_: self.about_dlg.hide_on_delete())
        self.about_dlg.connect('response', self.hdl_about_dlg_response)

    def _tear_down(self) -> None:
        self.primary_win.destroy()
        self.about_dlg.destroy()

    def show_primary_win(self) -> None:
        self.primary_win.show()

    def hide_primary_win(self) -> None:
        self.primary_win.hide()

    def show_about_dialog(self) -> None:
        self.about_dlg.show()

    def hide_about_dialog(self) -> None:
        self.about_dlg.hide()

    def external_action(self, action_name: str) -> None:
        self.on_external_action.fire(action_name)

    def hdl_about_dlg_response(self, about_dlg: Gtk.Dialog, response_id: int) -> None:
        if response_id == Gtk.ResponseType.DELETE_EVENT or response_id == Gtk.ResponseType.CANCEL:
            self.on_about_dlg_response.fire('close')
        else:
            self.on_about_dlg_response.fire('unknown')

    def hdl_primary_win_delete_event(self, primary_win: Gtk.Widget, data) -> bool:
        self.on_request_close.fire()
        return True


class MainMenuScenePresenter(Presenter):
    model = ...  # type: None
    view = ...  # type: MainMenuSceneView

    def _set_up(self) -> None:
        self._event_conns = [
            self.view.on_menu_about_btn_clicked.connect(self.hdl_menu_about_btn_clicked),
            self.view.on_about_dlg_response.connect(self.hdl_about_dlg_response)
        ]

        self.view.show_primary_win()

    def _tear_down(self) -> None:
        # Disconnect event connections.
        for conn in self._event_conns:
            conn.disconnect()

    def hdl_menu_about_btn_clicked(self) -> None:
        self.view.show_about_dialog()

    def hdl_about_dlg_response(self, response: str) -> None:
        if response == 'close':
            self.view.hide_about_dialog()


class _MainMenuScene(GtkScene):
    view = ...  # type: MainMenuSceneView
    presenter = ...  # type: MainMenuScenePresenter

    def _m_init(self, **opts):
        super()._m_init(**opts)
        self.on_response = Event()

    def _set_up(self):
        self._event_conns = [
            self.view.on_external_action.connect(self.on_response.fire),
            self.view.on_request_close.connect(functools.partial(self.on_response.fire, 'close'), strong_ref=True)
        ]

        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        print("Tearing down MainMenuScene...")
        # Disconnect event connections.
        for conn in self._event_conns:
            conn.disconnect()

        # Tear down view and presenter.
        self.presenter.tear_down()
        self.view.tear_down()


class MainMenuScene(_MainMenuScene):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=MainMenuSceneView,
            _presenter_cls=MainMenuScenePresenter,
            *args, **kwargs
        )
