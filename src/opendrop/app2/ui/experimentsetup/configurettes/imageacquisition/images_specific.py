import functools
import typing

from gi.repository import Gtk, GLib

from opendrop.app2.ui.experimentsetup.configurettes.imageacquisition.image_acquisition import ObserverSpecificImAcqEditorProvider, \
    ImageAcquisitionConfigurationModel
from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponentView, GtkGridComponent
from opendrop.mvp2.presenter import Presenter
from opendrop.observer.types.image_slideshow import ImageSlideshowObserver
from opendrop.utility.bindable.bindable import AtomicBindableAdapter
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry


class ImageSlideshowSpecificImAcqEditorView(GtkGridComponentView):
    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)

        self.bn_frame_interval = AtomicBindableAdapter()
        self.bn_num_frames = AtomicBindableAdapter()

    def _set_up(self):
        body = self.container

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

        num_frames_inp = IntegerEntry(sensitive=False, lower=1, width_chars=6)
        num_frames_inp.get_style_context().add_class('small')
        body.attach(num_frames_inp, 1, 1, 1, 1)
        self.bn_num_frames.setter = num_frames_inp.set_value

        body.foreach(Gtk.Widget.show)

    def set_frame_interval_inp_sensitivity(self, value: bool) -> None:
        if value is False and self.frame_interval_inp.is_focus():
            self.container.grab_focus_without_selecting()
            # Can't desensitize immediately while frame_interval_inp is focused, otherwise some error is thrown:
            #   (__init__.py:25159): Gdk-CRITICAL **: gdk_device_get_source: assertion 'GDK_IS_DEVICE (device)' failed
            GLib.idle_add(functools.partial(self.frame_interval_inp.set_sensitive, value))
        else:
            self.frame_interval_inp.props.sensitive = value

        self.frame_interval_inp.set_visibility(value)


class ImageSlideshowSpecificImAcqEditorPresenter(Presenter[ImageSlideshowSpecificImAcqEditorView]):
    def _m_init(self, model: ImageAcquisitionConfigurationModel) -> None:
        self.model = model
        self.observer = typing.cast(ImageSlideshowObserver, self.model.bn_observer.get())

    def _set_up(self):
        num_frames = self.observer.num_images

        if num_frames <= 1:
            self.view.set_frame_interval_inp_sensitivity(False)

        self.model.bn_num_frames.set(num_frames)

        self._data_bindings = [
            Binding(self.model.bn_frame_interval, self.view.bn_frame_interval),
            Binding(self.model.bn_num_frames, self.view.bn_num_frames)
        ]

    def _tear_down(self):
        for binding in self._data_bindings:
            binding.unbind()


class _ImageSlideshowSpecificImAcqEditor(GtkGridComponent):
    def _m_init(self, model: ImageAcquisitionConfigurationModel, *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)
        self._presenter_opts['model'] = model

    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()


@ObserverSpecificImAcqEditorProvider.register(lambda observer: isinstance(observer, ImageSlideshowObserver))
class ImageSlideshowSpecificImAcqEditor(_ImageSlideshowSpecificImAcqEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ImageSlideshowSpecificImAcqEditorView,
            _presenter_cls=ImageSlideshowSpecificImAcqEditorPresenter,
            *args, **kwargs
        )
