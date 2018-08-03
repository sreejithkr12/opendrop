import functools

import cairo
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GObject, GdkPixbuf

from opendrop.res import path as res
from opendrop.utility.events import Event


class MainMenuWindowView:
    WINDOW_TITLE = 'Main menu'

    LOGO_PATH = str(res/'images'/'logo.png')

    def __init__(self, window: Gtk.Window) -> None:
        self.window = window

        # Events:
        self.on_about_btn_clicked = Event()  # emits: ()
        self.on_settings_btn_clicked = Event()  # emits: ()
        self.on_ift_btn_clicked = Event()  # emits: ()
        self.on_conan_btn_clicked = Event()  # emits: ()

        self._build_ui()

    def _build_ui(self) -> None:
        self.window.props.resizable = False

        body = Gtk.Grid()
        self.window.add(body)

        left_grid = Gtk.Grid(vexpand=True, row_spacing=10)
        body.attach(left_grid, 0, 0, 1, 1)

        left_grid.get_style_context().add_class('left-grid')

        left_grid_css = Gtk.CssProvider()
        left_grid_css.load_from_data(bytes('''
            .left-grid {
                background-color: WHITESMOKE;
                padding: 10px;
            }
        ''', encoding='utf-8'))

        left_grid.get_style_context().add_provider(left_grid_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.logo_img_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(self.LOGO_PATH, width=150, height=-1)
        self.logo_img_version_name_format = "'{}'"
        self.logo_img_version_name_font_face = 'Arial', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD
        self.logo_img_version_name_font_size = 16
        self.logo_img_version_name_pos = 0.50, 0.93

        self.logo_img = Gtk.Image()
        self.logo_img.set_from_pixbuf(self.logo_img_pixbuf)
        left_grid.attach(self.logo_img, 0, 0, 1, 1)

        self.version_lbl_format = 'Version: {}'
        self.version_lbl = Gtk.Label(self.version_lbl_format.format('dev'))
        left_grid.attach(self.version_lbl, 0, 1, 1, 1)

        left_grid.attach(Gtk.Grid(vexpand=True), 0, 2, 1, 1)

        self.about_btn = Gtk.Button('About', margin_top=10)
        left_grid.attach(self.about_btn, 0, 3, 1, 1)
        self.about_btn.connect('clicked', lambda w: self.on_about_btn_clicked.fire())

        right_grid = Gtk.Grid()
        body.attach(right_grid, 1, 0, 1, 1)

        actions_container = Gtk.Grid(column_homogeneous=True, column_spacing=20, row_spacing=35, margin=30)
        right_grid.attach(Gtk.Grid(vexpand=True), 0, 0, 1, 1)
        right_grid.attach(Gtk.Grid(vexpand=True), 0, 2, 1, 1)
        right_grid.attach(actions_container, 0, 1, 1, 1)

        conan_btn_container = Gtk.Grid(hexpand=False, row_spacing=5)
        # conan_btn_container.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(.5,.5,.5,.5))

        self.conan_btn = Gtk.Button()
        self.conan_btn.connect('clicked', lambda w: self.on_conan_btn_clicked.fire())

        conan_btn_img_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(str(res/'images'/'conan_btn.png'), width=32,
                                                                      height=32)
        conan_btn_img = Gtk.Image.new_from_pixbuf(conan_btn_img_pixbuf)
        self.conan_btn.set_image(conan_btn_img)

        conan_btn_container.attach(Gtk.Grid(hexpand=True), 0, 0, 1, 1)
        conan_btn_container.attach(Gtk.Grid(hexpand=True), 2, 0, 1, 1)
        conan_btn_container.attach(self.conan_btn, 1, 0, 1, 1)

        conan_btn_lbl = Gtk.Label('Contact Angle', wrap=True, max_width_chars=9, width_request=72,
                                  justify=Gtk.Justification.CENTER)
        conan_btn_container.attach(conan_btn_lbl, 0, 1, 3, 1)

        actions_container.attach(conan_btn_container, 1, 0, 1, 1)

        ift_btn_container = Gtk.Grid(hexpand=False, row_spacing=5)
        # ift_btn_container.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(.5,.5,.5,.5))

        self.ift_btn = Gtk.Button()
        self.ift_btn.connect('clicked', lambda w: self.on_ift_btn_clicked.fire())
        ift_btn_img_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(str(res/'images'/'ift_btn.png'), width=32,
                                                                    height=32)
        ift_btn_img = Gtk.Image.new_from_pixbuf(ift_btn_img_pixbuf)
        self.ift_btn.set_image(ift_btn_img)

        ift_btn_container.attach(Gtk.Grid(hexpand=True), 0, 0, 1, 1)
        ift_btn_container.attach(Gtk.Grid(hexpand=True), 2, 0, 1, 1)
        ift_btn_container.attach(self.ift_btn, 1, 0, 1, 1)

        ift_btn_lbl = Gtk.Label('IFT', wrap=True, max_width_chars=9, width_request=72, justify=Gtk.Justification.CENTER)
        ift_btn_container.attach(ift_btn_lbl, 0, 1, 3, 1)

        actions_container.attach(ift_btn_container, 0, 0, 1, 1)

        settings_btn_container = Gtk.Grid(hexpand=False, row_spacing=5)

        self.settings_btn = Gtk.Button.new_from_icon_name('preferences-system', Gtk.IconSize.DND)
        self.settings_btn.connect('clicked', lambda w: self.on_settings_btn_clicked.fire())

        settings_btn_container.attach(Gtk.Grid(hexpand=True), 0, 0, 1, 1)
        settings_btn_container.attach(Gtk.Grid(hexpand=True), 2, 0, 1, 1)
        settings_btn_container.attach(self.settings_btn, 1, 0, 1, 1)

        settings_btn_lbl = Gtk.Label('Settings', wrap=True, max_width_chars=9, width_request=72,
                                     justify=Gtk.Justification.CENTER)
        settings_btn_container.attach(settings_btn_lbl, 0, 1, 3, 1)

        actions_container.attach(settings_btn_container, 0, 1, 2, 1)

        body.show_all()

    @GObject.Signal
    def about_btn_clicked(self) -> None: pass

    @GObject.Signal
    def settings_btn_clicked(self) -> None: pass

    @GObject.Signal
    def ift_btn_clicked(self) -> None: pass

    @GObject.Signal
    def conan_btn_clicked(self) -> None: pass


class MainMenuWindowPresenter:
    def __init__(self, view: MainMenuWindowView):
        pass


class MainMenuWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._view = MainMenuWindowView(self)
        self._presenter = MainMenuWindowPresenter(self._view)
        self._set_up()

    def _set_up(self) -> None:
        # Connect to view events.
        self._event_conns = [
            self._view.on_about_btn_clicked.connect(functools.partial(self.emit, 'about_btn_clicked'), strong_ref=True),
            self._view.on_settings_btn_clicked.connect(functools.partial(self.emit, 'settings_btn_clicked'), strong_ref=True),
            self._view.on_ift_btn_clicked.connect(functools.partial(self.emit, 'ift_btn_clicked'), strong_ref=True),
            self._view.on_conan_btn_clicked.connect(functools.partial(self.emit, 'conan_btn_clicked'), strong_ref=True),
        ]

    def do_destroy(self) -> None:
        # Disconnect event connections.
        for conn in self._event_conns:
            conn.disconnect()

    @GObject.Signal
    def about_btn_clicked(self) -> None: pass

    @GObject.Signal
    def settings_btn_clicked(self) -> None: pass

    @GObject.Signal
    def ift_btn_clicked(self) -> None: pass

    @GObject.Signal
    def conan_btn_clicked(self) -> None: pass
