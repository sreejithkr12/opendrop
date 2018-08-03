from typing import Optional, List

from gi.repository import Gtk, Gdk

from opendrop.app.ui.core.experiment_setup.dash import ExperimentSetupDashView
from opendrop.gtk_specific.GtkWidgetView import GtkWidgetView
from opendrop.gtk_specific.GtkWindowView import GtkWindowView
from opendrop.gtk_specific.shims import mouse_move_event_from_event_motion, mouse_button_event_from_event_button, \
    key_code_from_gdk_keyval
from opendrop.image_filter.bases import ImageFilter
from opendrop.observer.bases import ObserverPreview
from opendrop.observer.gtk import PreviewViewer, PreviewViewerController

DASH_ORDER = [
    'physical_quantities',
    'scale',
    'threshold',
    'drop_region',
]


class ExperimentSetupView(GtkWindowView):
    TITLE = 'Experiment Setup'

    class DashOrderingContainer:
        def __init__(self, view: GtkWidgetView, wrapper: 'DashWrapper') -> None:
            self.view = view  # type: GtkWidgetView
            self.wrapper = wrapper  # type: DashWrapper

    def setup(self) -> None:
        self.dashes = []  # type: List[ExperimentSetupView.DashOrderingContainer]

        # Keep the view hidden initially until a preview is set
        self.hidden = True
        self.window.set_default_size(800, 600)

        # -- Build UI --

        # Body
        body = Gtk.Grid()

        # Viewer
        viewer_container = Gtk.Grid()
        body.attach(viewer_container, 0, 0, 1, 1)

        self.viewer = PreviewViewer(hexpand=True, vexpand=True)
        viewer_container.attach(self.viewer, 0, 0, 1, 1)

        viewer_controller = PreviewViewerController(viewer=self.viewer)
        viewer_container.attach(viewer_controller, 0, 1, 1, 1)
        # End viewer

        # Parameters/Dash container
        dash_container_outer = Gtk.Grid()

        # Dash container header bg
        dash_container_header_bg = Gtk.Box()
        dash_container_header_bg.get_style_context().add_class('gray-box')

        dash_container_header_bg_css = Gtk.CssProvider()  # type: Gtk.CssProvider
        dash_container_header_bg_css.load_from_data(bytes('''
            .gray-box {
                background-color: gainsboro;
            }
        ''', encoding='utf-8'))

        dash_container_header_bg.get_style_context().add_provider(dash_container_header_bg_css,
                                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        dash_container_outer.attach(dash_container_header_bg, 0, 0, 1, 1)
        # End dash container header bg

        # Dash container header
        dash_container_header_lbl = Gtk.Label(margin=5, margin_top=10, margin_bottom=10)
        dash_container_header_lbl.set_markup('<span font_desc=\'11.0\'>{}</span>'.format('Parameters'))
        dash_container_header_bg.add(dash_container_header_lbl)
        # End dash container header

        self.dash_container = Gtk.Grid(hexpand=False, vexpand=True)
        dash_container_outer.attach(self.dash_container, 0, 1, 1, 1)

        body.attach(dash_container_outer, 1, 0, 1, 1)
        # End parameters/dash container

        # Navigation bar
        navigation_bar = Gtk.Grid(column_spacing=5)
        navigation_bar.props.margin = 5

        # Cancel button
        self.cancel_btn = Gtk.Button(label='Cancel')
        self.cancel_btn.connect('clicked', lambda w: self.events['cancel_btn.on_clicked'].fire())
        navigation_bar.attach(self.cancel_btn, 0, 0, 1, 1)
        # End cancel button

        # Spacing
        navigation_bar.attach(Gtk.Box(hexpand=True), 1, 0, 1, 1)
        # End spacing

        # Begin button
        self.begin_btn = Gtk.Button(label='Begin')
        self.begin_btn.connect('clicked', lambda w: self.events['begin_btn.on_clicked'].fire())
        navigation_bar.attach(self.begin_btn, 3, 0, 1, 1)
        # End begin button

        body.attach(navigation_bar, 0, 1, 2, 1)
        # End navigation bar

        self.window.add(body)
        # End body

        body.show_all()

        # Event forwarding
        def _handle_viewer_motion_notify_event(widget: Gtk.Widget, event: Gdk.EventMotion):
            event = mouse_move_event_from_event_motion(event)
            event.pos = self.viewer.rel_from_abs(event.pos)
            self.events['viewer.on_mouse_move'].fire(event)

        def _handle_viewer_button_press_event(widget: Gtk.Widget, event: Gdk.EventButton):
            event = mouse_button_event_from_event_button(event)
            event.pos = self.viewer.rel_from_abs(event.pos)
            self.events['viewer.on_button_press'].fire(event)

        def _handle_viewer_button_release_event(widget: Gtk.Widget, event: Gdk.EventButton):
            event = mouse_button_event_from_event_button(event)
            event.pos = self.viewer.rel_from_abs(event.pos)
            self.events['viewer.on_button_release'].fire(event)

        def _handle_viewer_focus_in(widget: Gtk.Widget, event: Gdk.EventFocus):
            self.events['viewer.on_focus_in'].fire()

        def _handle_viewer_focus_out(widget: Gtk.Widget, event: Gdk.EventFocus):
            self.events['viewer.on_focus_out'].fire()

        self.viewer.connect('motion-notify-event', _handle_viewer_motion_notify_event)
        self.viewer.connect('button-press-event', _handle_viewer_button_press_event)
        self.viewer.connect('button-release-event', _handle_viewer_button_release_event)
        self.viewer.connect('focus-in-event', _handle_viewer_focus_in)
        self.viewer.connect('focus-out-event', _handle_viewer_focus_out)

        def _handle_button_press_event(widget: Gtk.Widget, event: Gdk.EventButton) -> None:
            self.events['on_mouse_button_press'].fire(mouse_button_event_from_event_button(event))

        def _handle_key_press_event(widget: Gtk.Widget, event: Gdk.EventKey) -> None:
            if event.keyval == Gdk.KEY_Escape:
                self.window.set_focus(None)

            curr_widget_focused = self.window.get_focus()

            if curr_widget_focused is not None and isinstance(curr_widget_focused, Gtk.Entry):
                return

            self.events['on_key_press'].fire(key_code_from_gdk_keyval(event.keyval))

        self.window.connect('button-press-event', _handle_button_press_event)
        self.window.connect('key-press-event', _handle_key_press_event)

    def set_viewer_preview(self, preview: Optional[ObserverPreview]) -> None:
        self.viewer.preview = preview

        self.hidden = False

    def redraw_viewer(self) -> None:
        self.viewer.queue_draw()

    def reorder_dash(self) -> None:
        for child in self.dash_container.get_children():
            self.dash_container.remove(child)

        self.dashes = [*sorted(
            self.dashes,
            key=lambda c: DASH_ORDER.index(c.view.ID) if c.view.ID in DASH_ORDER else len(DASH_ORDER))
        ]

        for dash in self.dashes:
            self.dash_container.attach(dash.wrapper, 0, len(self.dash_container.get_children()), 1, 1)

    def add_dash(self, dash_view: ExperimentSetupDashView) -> None:
        dash_view.toplevel = self.window
        dash_name = dash_view.NAME if dash_view.NAME is not None else type(dash_view).__name__  # type: str

        wrapped_dash_widget = DashWrapper(dash_name, dash_view.container)
        wrapped_dash_widget.show()

        self.dash_container.attach(wrapped_dash_widget, 0, len(self.dash_container.get_children()), 1, 1)

        self.dashes.append(ExperimentSetupView.DashOrderingContainer(dash_view, wrapped_dash_widget))

        self.reorder_dash()

    def cursor_set_crosshair(self, active: bool) -> None:
        if active:
            self.window.get_window().set_cursor(Gdk.Cursor.new_from_name(Gdk.Display.get_default(), 'crosshair'))
        else:
            self.window.get_window().set_cursor(None)

    def viewer_grab_focus(self) -> None:
        self.viewer.grab_focus()

    def viewer_add_filter(self, f: ImageFilter) -> None:
        self.viewer.filters.add(f)


class DashWrapper(Gtk.Grid):
    def __init__(self, name: str, dash_widget: Gtk.Widget) -> None:
        super().__init__()

        self.props.margin = 5

        self.dash_lbl = Gtk.Label(margin_bottom=5)
        self.dash_lbl.set_markup('<b>{}</b>'.format(name))
        self.dash_lbl.props.xalign = 0.0
        self.dash_lbl.show()

        self.attach(self.dash_lbl, 0, 0, 1, 1)

        self.attach(dash_widget, 0, 1, 1, 1)
