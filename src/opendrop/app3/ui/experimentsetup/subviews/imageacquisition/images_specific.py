import functools

from gi.repository import Gtk, GLib

from opendrop.observer.types.image_slideshow import ImageSlideshowObserver
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry
from .image_acquisition import ImageAcquisitionEditorView, SpecificEditorView, SpecificEditorViewFactory


@SpecificEditorViewFactory.register(lambda observer: isinstance(observer, ImageSlideshowObserver))
class ImageSlideshowSpecificEditorView(SpecificEditorView):
    def __init__(self, parent: ImageAcquisitionEditorView, container: Gtk.Grid) -> None:
        super().__init__(parent, container)

        self._container = container

        self._build_ui()

        observer = parent.bn_observer.get()
        assert isinstance(observer, ImageSlideshowObserver)

        num_frames = observer.num_images
        self.bn_num_frames.set(num_frames)

        if num_frames <= 1:
            self.view.set_frame_interval_inp_sensitivity(False)

    def _build_ui(self) -> None:
        body = self._container

        body.props.column_spacing = 10
        body.props.row_spacing = 5

        frame_interval_lbl = Gtk.Label('Frame interval (s):', halign=Gtk.Align.START)
        body.attach(frame_interval_lbl, 0, 0, 1, 1)

        frame_interval_inp = FloatEntry(lower=0, width_chars=6, invisible_char='\0')
        frame_interval_inp.get_style_context().add_class('small')
        body.attach(frame_interval_inp, 1, 0, 1, 1)
        link_atomic_bn_adapter_to_g_prop(self.bn_frame_interval, frame_interval_inp, 'value')

        num_frames_lbl = Gtk.Label('Num. frames:', halign=Gtk.Align.START)
        body.attach(num_frames_lbl, 0, 1, 1, 1)

        num_frames_inp = IntegerEntry(sensitive=False, lower=1, width_chars=6)
        num_frames_inp.get_style_context().add_class('small')
        body.attach(num_frames_inp, 1, 1, 1, 1)
        self.bn_num_frames.setter = num_frames_inp.set_value

        body.foreach(Gtk.Widget.show)

    def set_frame_interval_inp_sensitivity(self, value: bool) -> None:
        if value is False and self.frame_interval_inp.is_focus():
            self.container.grab_focus_without_selecting()
            # Can't desensitize immediately while frame_interval_inp is focused, otherwise this error is thrown:
            #   (__init__.py:25159): Gdk-CRITICAL **: gdk_device_get_source: assertion 'GDK_IS_DEVICE (device)' failed
            GLib.idle_add(functools.partial(self.frame_interval_inp.set_sensitive, value))
        else:
            self.frame_interval_inp.props.sensitive = value

        self.frame_interval_inp.set_visibility(value)

    def destroy(self):
        self.bn_frame_interval.getter = None
        self.bn_frame_interval.setter = None
        self.bn_num_frames.setter = None
