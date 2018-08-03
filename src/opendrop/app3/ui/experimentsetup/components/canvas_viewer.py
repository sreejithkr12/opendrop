import cairo
from typing import Optional

from gi.repository import Gtk, Gdk, GObject

from opendrop.app2.ui.experimentsetup.canvas import Canvas
from opendrop.gtk_specific.misc import pixbuf_from_array
from opendrop.utility.events import EventConnection


class CanvasViewer(Gtk.DrawingArea):
    def __init__(self, canvas: Optional[Canvas] = None, *, can_focus=True, **properties) -> None:
        # Property defaults
        self._canvas = None  # type: Optional[Canvas]
        self._canvas_changed_conn = None  # type: Optional[EventConnection]

        super().__init__(can_focus=can_focus, **properties)

        # Add extra events onto Gtk.DrawingArea
        self.add_events(
              Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.FOCUS_CHANGE_MASK
        )

        # Event handling
        self.connect('button-press-event', lambda *args: self.grab_focus())

        # Post init stuff
        self.show_all()
        self.props.canvas = canvas

    @GObject.Property
    def canvas(self) -> Optional[Canvas]:
        return self._canvas

    @canvas.setter
    def canvas(self, new_canvas: canvas) -> None:
        if self.canvas is not None:
            self._canvas_changed_conn.disconnect()
            self._canvas_changed_conn = None

        self._canvas = new_canvas

        if new_canvas is None:
            return

        new_canvas.on_changed.connect(self._hdl_canvas_changed)
        self.queue_draw()

    def do_draw(self, cr: cairo.Context) -> None:
        # Fill background as black
        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        if self.props.canvas is None:
            # If canvas has not been set, draw a placeholder graphic.
            cr.set_source_rgb(255, 255, 255)
            cr.move_to(10, 20)
            cr.show_text('No canvas')
            return

        buffer = self.props.canvas.buffer

        if 0 in buffer.shape:
            # Buffer has zero width/height
            return

        Gdk.cairo_set_source_pixbuf(cr, pixbuf_from_array(self.props.canvas.buffer), pixbuf_x=0, pixbuf_y=0)
        cr.paint()

    def _hdl_canvas_changed(self) -> None:
        self.queue_draw()
