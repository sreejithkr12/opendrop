import functools

from gi.repository import Gtk, GLib

from opendrop.app2.ui.experimentsetup.configurettes.imageacquisition.image_acquisition import ObserverSpecificImAcqEditorProvider, \
    ImageAcquisitionConfigurationModel
from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponentView, GtkGridComponent
from opendrop.mvp2.presenter import Presenter
from opendrop.observer.types.camera import CameraObserver
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.utility.events import Event
from opendrop.widgets.float_entry import FloatEntry
from opendrop.widgets.integer_entry import IntegerEntry


class USBCameraSpecificImAcqEditorView(GtkGridComponentView):
    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)
        self.bn_frame_interval = AtomicBindableAdapter()  # type: AtomicBindable[float]
        self.bn_num_frames = AtomicBindableAdapter()  # type: AtomicBindable[int]

        self.on_num_frames_inp_changed = Event()  # emits: ()

    def _set_up(self) -> None:
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

        self.num_frames_inp = IntegerEntry(lower=0, width_chars=6)
        self.num_frames_inp.get_style_context().add_class('small')
        body.attach(self.num_frames_inp, 1, 1, 1, 1)
        link_atomic_bn_adapter_to_g_prop(self.bn_num_frames, self.num_frames_inp, 'value')
        self.num_frames_inp.connect('changed', lambda *_: self.on_num_frames_inp_changed.fire())

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


class USBCameraSpecificImAcqEditorPresenter(Presenter[USBCameraSpecificImAcqEditorView]):
    def _m_init(self, model: ImageAcquisitionConfigurationModel) -> None:
        self.model = model

    def _set_up(self) -> None:
        outer = self
        #
        # class FrameTimestampsToFrameIntervalBindingMITM(AtomicBindingMITM[Sequence[float], Optional[float]]):
        #     def _atomic_to_dst(self, frame_timestamps: Sequence[float]) -> Optional[float]:
        #         if len(frame_timestamps) <= 1:
        #             return self.BLOCK
        #
        #         frame_interval = frame_timestamps[1] - frame_timestamps[0]
        #
        #         # Make sure the frame timestamps are evenly spaced
        #         for a, b in zip(frame_timestamps, frame_timestamps[1:]):
        #             if abs((b - a) - frame_interval) > 0.0001:
        #                 warnings.warn(
        #                     'Frame timestamps in the model are not evenly spaced, current user-interface does not '
        #                     'support this, unexpected behaviour with setting the frame timestamps may occur.'
        #                 )
        #                 break
        #
        #         return frame_interval
        #
        #     def _atomic_to_src(self, frame_interval: Optional[float]) -> Sequence[float]:
        #         num_frames = outer.view.bn_num_frames.get()
        #
        #         if frame_interval is None or frame_interval <= 0.0 or num_frames is None:
        #             return tuple()
        #
        #         return outer._make_timestamps(num_frames, frame_interval)
        #
        # class FrameTimestampsToNumFramesBindingMITM(AtomicBindingMITM[Sequence[float], Optional[int]]):
        #     def _atomic_to_dst(self, frame_timestamps: Sequence[float]) -> Optional[int]:
        #         if len(frame_timestamps) == 0:
        #             return self.BLOCK
        #
        #         return len(frame_timestamps)
        #
        #     def _atomic_to_src(self, num_frames: Optional[int]) -> Sequence[float]:
        #         frame_interval = outer.view.bn_frame_interval.get()
        #
        #         if num_frames is None or num_frames <= 0 or frame_interval is None:
        #             return tuple()
        #
        #         return outer._make_timestamps(num_frames, frame_interval)

        # Clear the entries first,
        self.view.bn_frame_interval.set(None)
        self.view.bn_num_frames.set(None)

        # and then bind values in model to the view, in case default values are invalid, in which case they are ignored
        # by the mitm rules above which may leave the model and view in an inconsistent state (where the model has
        # invalid data but the view has valid data initialised in the input widgets, so we cleared them to None first).
        self._data_bindings = [
            Binding(self.model.bn_frame_interval, self.view.bn_frame_interval),
            Binding(self.model.bn_num_frames, self.view.bn_num_frames)
        ]

        self._event_conns = [
            self.view.on_num_frames_inp_changed.connect(
                self._update_view_frame_interval_inp_sensitivity,
                immediate=True
            )
        ]

        self._update_view_frame_interval_inp_sensitivity()

    def _update_view_frame_interval_inp_sensitivity(self) -> None:
        num_frames = self.view.bn_num_frames.get()
        self.view.set_frame_interval_inp_sensitivity(
            num_frames is None or num_frames != 1
        )

    def _tear_down(self) -> None:
        for binding in self._data_bindings:
            binding.unbind()

        for conn in self._event_conns:
            conn.disconnect()
    #
    # def _frame_interval_from_model(self) -> Optional[float]:
    #     frame_timestamps = self.model.bn_frame_timestamps.get()
    #
    #     frame_interval = None
    #
    #     if len(frame_timestamps) > 1:
    #         frame_interval = frame_timestamps[1] - frame_timestamps[0]
    #
    #         # Make sure the frame timestamps are evenly spaced
    #         for a, b in zip(frame_timestamps, frame_timestamps[1:]):
    #             if abs((b - a) - frame_interval) > 0.0001:
    #                 warnings.warn(
    #                     'Frame timestamps in the model are not evenly spaced, current user-interface does not support '
    #                     'this, unexpected behaviour with setting the frame timestamps may occur.'
    #                 )
    #                 break
    #
    #     return frame_interval
    #
    # def _num_frames_from_model(self) -> int:
    #     return len(self.model.bn_frame_timestamps.get())
    #
    # def _frame_timestamps_from_view(self) -> Sequence[float]:
    #     return self._make_timestamps(
    #         num_frames=self.view.bn_num_frames.get(),
    #         frame_interval=self.view.bn_frame_interval.get()
    #     )
    #
    # @staticmethod
    # def _make_timestamps(num_frames: int, frame_interval: float) -> Sequence[float]:
    #     return tuple(
    #         i * frame_interval for i in range(num_frames)
    #     )


class _USBCameraSpecificImAcqEditor(GtkGridComponent):
    def _m_init(self, model: ImageAcquisitionConfigurationModel, *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)
        self._presenter_opts['model'] = model

    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()


@ObserverSpecificImAcqEditorProvider.register(lambda observer: isinstance(observer, CameraObserver))
class USBCameraSpecificImAcqEditor(_USBCameraSpecificImAcqEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=USBCameraSpecificImAcqEditorView,
            _presenter_cls=USBCameraSpecificImAcqEditorPresenter,
            *args, **kwargs
        )
