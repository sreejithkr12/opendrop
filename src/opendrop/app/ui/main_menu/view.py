from typing import List

from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo

from opendrop.res import path as res
from opendrop.gtk_specific.GtkWindowView import GtkWindowView


class MainMenuView(GtkWindowView):
    TITLE = 'Opendrop'

    LOGO_PATH = str(res/'images'/'logo.png')

    def setup(self):
        self.window.props.resizable = False

        body = Gtk.Grid()
        self.window.add(body)

        left_grid = Gtk.Grid(vexpand=True, row_spacing=10)
        body.attach(left_grid, 0, 0, 1, 1)

        left_grid.get_style_context().add_class('left-grid')

        left_grid_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        left_grid_css.load_from_data(bytes('''
            .left-grid {
                background-color: WHITESMOKE;
                padding: 10px;
            }
        ''', encoding='utf-8'))

        left_grid.get_style_context().add_provider(left_grid_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.logo_img_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(self.LOGO_PATH, width=150,
                                                                      height=-1)  # type: GdkPixbuf.Pixbuf
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
        self.about_btn.connect('clicked', lambda w: self.events['about_btn.on_clicked'].fire())

        right_grid = Gtk.Grid()
        body.attach(right_grid, 1, 0, 1, 1)

        actions_container = Gtk.Grid(column_homogeneous=True, column_spacing=20, row_spacing=35, margin=30)
        right_grid.attach(Gtk.Grid(vexpand=True), 0, 0, 1, 1)
        right_grid.attach(Gtk.Grid(vexpand=True), 0, 2, 1, 1)
        right_grid.attach(actions_container, 0, 1, 1, 1)

        conan_btn_container = Gtk.Grid(hexpand=False, row_spacing=5)
        # conan_btn_container.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(.5,.5,.5,.5))

        self.conan_btn = Gtk.Button()
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
        self.ift_btn.connect('clicked', lambda w: self.events['ift_btn.on_clicked'].fire())
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
        self.settings_btn.connect('clicked', lambda w: self.events['settings_btn.on_clicked'].fire())

        settings_btn_container.attach(Gtk.Grid(hexpand=True), 0, 0, 1, 1)
        settings_btn_container.attach(Gtk.Grid(hexpand=True), 2, 0, 1, 1)
        settings_btn_container.attach(self.settings_btn, 1, 0, 1, 1)

        settings_btn_lbl = Gtk.Label('Settings', wrap=True, max_width_chars=9, width_request=72,
                                     justify=Gtk.Justification.CENTER)
        settings_btn_container.attach(settings_btn_lbl, 0, 1, 3, 1)

        actions_container.attach(settings_btn_container, 0, 1, 2, 1)

        self.about_dialog = Gtk.AboutDialog(logo=self.logo_img_pixbuf, transient_for=self.window, modal=True)
        self.about_dialog.connect('delete-event', lambda *args: self.about_dialog.hide_on_delete())
        self.about_dialog.connect('response', self.handle_about_window_response)

        self.window.show_all()

    def set_version_name(self, value: str) -> None:
        display = self.logo_img_version_name_format.format(value)

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.logo_img_pixbuf.get_width(),
                                     self.logo_img_pixbuf.get_height())
        cr = cairo.Context(surface)

        Gdk.cairo_set_source_pixbuf(cr, self.logo_img_pixbuf, 0, 0)
        cr.paint()

        cr.select_font_face(*self.logo_img_version_name_font_face)
        cr.set_font_size(self.logo_img_version_name_font_size)

        # See documentation for description of tuple values:
        # https://cairographics.org/manual/cairo-cairo-scaled-font-t.html#cairo-text-extents-t
        # Text width and height are on index 2 and 3
        text_size = cr.text_extents(display)[2:4]  # type: tuple

        text_center = self.logo_img_version_name_pos[0] * surface.get_width(), \
                      self.logo_img_version_name_pos[1] * surface.get_height()
        text_bottom_left = text_center[0] - text_size[0] / 2, text_center[1] + text_size[1] / 2

        cr.move_to(*text_bottom_left)

        cr.set_source_rgba(0, 0, 0, 1)
        cr.show_text(display)

        surface = cr.get_target()
        pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, surface.get_width(), surface.get_height())

        self.logo_img.set_from_pixbuf(pixbuf)
        self.about_dialog.props.logo = pixbuf

    def set_version(self, value: str) -> None:
        self.version_lbl.props.label = self.version_lbl_format.format(value)
        self.about_dialog.props.version = value

    def set_about_info(self, program_name: str, website: str, comments: str, authors: List[str]) -> None:
        self.about_dialog.props.program_name = program_name
        self.about_dialog.props.website = website
        self.about_dialog.props.comments = comments
        self.about_dialog.props.authors = authors

    def show_about_window(self) -> None:
        self.about_dialog.show()

    def handle_about_window_response(self, w: Gtk.AboutDialog, response: Gtk.ResponseType) -> None:
        if response == Gtk.ResponseType.DELETE_EVENT or response == Gtk.ResponseType.CANCEL:
            self.about_dialog.hide()
