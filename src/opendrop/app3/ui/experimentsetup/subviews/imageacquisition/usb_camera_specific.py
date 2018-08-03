import functools

from gi.repository import Gtk, GLib

from opendrop.observer.types.camera import CameraObserver
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry
from .image_acquisition import ImageAcquisitionEditorView, SpecificEditorView, SpecificEditorViewFactory


@SpecificEditorViewFactory.register(lambda observer: isinstance(observer, CameraObserver))
class USBCameraSpecificImAcqEditorView(SpecificEditorView):
    def __init__(self, parent: ImageAcquisitionEditorView, container: Gtk.Grid) -> None:
        super().__init__(parent, container)

        self._container = container

        observer = parent.bn_observer.get()
        assert isinstance(observer, CameraObserver)

        self._build_ui()

        self._update_frame_interval_inp_sensitivity()

    def _build_ui(self) -> None:
        body = self._container

        body.props.column_spacing = 10
        body.props.row_spacing    = 5

        frame_interval_lbl = Gtk.Label('Frame interval (s):', halign=Gtk.Align.START)
        body.attach(frame_interval_lbl, 0, 0, 1, 1)

        self.frame_interval_inp = FloatEntry(lower=0, width_chars=6, invisible_char='\0')
        self.frame_interval_inp.get_style_context().add_class('small')
        body.attach(self.frame_interval_inp, 1, 0, 1, 1)
        link_atomic_bn_adapter_to_g_prop(self.bn_frame_interval, self.frame_interval_inp, 'value')

        num_frames_lbl = Gtk.Label('Num. frames:', halign=Gtk.Align.START)
        body.attach(num_frames_lbl, 0, 1, 1, 1)

        self.num_frames_inp = IntegerEntry(lower=0, width_chars=6)
        self.num_frames_inp.get_style_context().add_class('small')
        body.attach(self.num_frames_inp, 1, 1, 1, 1)
        link_atomic_bn_adapter_to_g_prop(self.bn_num_frames, self.num_frames_inp, 'value')
        self.num_frames_inp.connect('changed', lambda *_: self._update_frame_interval_inp_sensitivity())

        body.foreach(Gtk.Widget.show)

    def set_frame_interval_inp_sensitivity(self, value: bool) -> None:
        if value is False and self.frame_interval_inp.is_focus():
            self.container.grab_focus()
            # Can't desensitize immediately while frame_interval_inp is focused, otherwise some error is thrown:
            #   (__init__.py:25159): Gdk-CRITICAL **: gdk_device_get_source: assertion 'GDK_IS_DEVICE (device)' failed
            GLib.idle_add(functools.partial(self.frame_interval_inp.set_sensitive, value))
        else:
            self.frame_interval_inp.props.sensitive = value

        self.frame_interval_inp.set_visibility(value)

    def _update_frame_interval_inp_sensitivity(self) -> None:
        num_frames = self.bn_num_frames.get()

        if num_frames == 1:
            self.set_frame_interval_inp_sensitivity(False)
        else:
            self.set_frame_interval_inp_sensitivity(True)

    def destroy(self) -> None:
        self.bn_frame_interval.getter = None
        self.bn_frame_interval.setter = None
        self.bn_num_frames.getter = None
        self.bn_num_frames.setter = None
