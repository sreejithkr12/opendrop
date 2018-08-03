import functools
import operator
from types import MappingProxyType
from typing import Mapping, Any, MutableMapping, Tuple

from gi.repository import Gtk

from opendrop import observer
from opendrop.app2.ui.observerchooser.configurators.bases import Configurator
from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponentView, GtkGridComponent
from opendrop.mvp2.presenter import Presenter
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.widgets.file_chooser_button import FileChooserButton

IMAGE_MIME_TYPES = [
    'image/png',
    'image/jpg'
]


class ImageSlideshowConfiguratorWidgetView(GtkGridComponentView):
    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)
        self.bn_image_paths = AtomicBindableAdapter()  # type: AtomicBindable[Tuple[str]]
        self.bn_frame_interval = AtomicBindableAdapter()  # type: AtomicBindable[float]

    def _set_up(self):
        body = self.container

        body.props.column_spacing = 10
        body.props.row_spacing    = 10

        file_input_filter = Gtk.FileFilter()

        for mime_type in IMAGE_MIME_TYPES:
            file_input_filter.add_mime_type(mime_type)

        file_input_lbl = Gtk.Label('Images:', halign=Gtk.Align.START)
        body.attach(file_input_lbl, 0, 0, 1, 1)

        self.file_paths_inp = FileChooserButton(
            label='Select images',
            file_filter=file_input_filter,
            select_multiple=True,
            hexpand=True
        )
        body.attach(self.file_paths_inp, 1, 0, 1, 1)
        link_atomic_bn_adapter_to_g_prop(self.bn_image_paths, self.file_paths_inp, 'file-paths')

        body.foreach(Gtk.Widget.show_all)


class ImageSlideshowConfiguratorWidgetPresenter(Presenter[ImageSlideshowConfiguratorWidgetView]):
    def _m_init(self, observer_options: MutableMapping[str, Any], **kwargs) -> None:
        super()._m_init(**kwargs)

        self.observer_options = observer_options

        self.bn_image_paths = AtomicBindableAdapter(
            getter=functools.partial(operator.getitem, self.observer_options, 'image_paths'),
            setter=functools.partial(operator.setitem, self.observer_options, 'image_paths')
        )

    def _set_up(self) -> None:
        self._data_bindings = [
            Binding(self.bn_image_paths, self.view.bn_image_paths),
        ]

        self._event_conns = [
            self.bn_image_paths.on_changed.connect(self.update_timestamps, immediate=True)
        ]

    def _tear_down(self) -> None:
        for binding in self._data_bindings:
            binding.unbind()

        for conn in self._event_conns:
            conn.disconnect()

    def update_timestamps(self) -> None:
        # Just initialise the image slideshow imageacquisition with a frame interval of 1 s, user can change it later.
        frame_interval = 1

        self.observer_options['timestamps'] = self.timestamps_from_frame_interval(
            frame_interval=frame_interval,
            num_frames=len(self.observer_options['image_paths'])
        )

    @staticmethod
    def timestamps_from_frame_interval(frame_interval: float, num_frames: int) -> Tuple[float]:
        return tuple(n * frame_interval for n in range(num_frames))


class _ImageSlideshowConfiguratorWidget(GtkGridComponent):
    def _m_init(self, observer_options: MutableMapping[str, Any], **kwargs) -> None:
        super()._m_init(**kwargs)
        self._presenter_opts['observer_options'] = observer_options

    def _set_up(self) -> None:
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self) -> None:
        self.presenter.tear_down()
        self.view.tear_down()


class ImageSlideshowConfiguratorWidget(_ImageSlideshowConfiguratorWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ImageSlideshowConfiguratorWidgetView,
            _presenter_cls=ImageSlideshowConfiguratorWidgetPresenter,
            *args, **kwargs
        )


@Configurator.register_configurator(observer.types.IMAGE_SLIDESHOW)
class ImageSlideshowConfigurator(Configurator):
    def __init__(self):
        self._options = {
            'image_paths': tuple(),
            'timestamps': tuple()
        }

    def create_widget(self):
        return ImageSlideshowConfiguratorWidget(self._options)

    @property
    def options(self) -> Mapping[str, Any]:
        return MappingProxyType(self._options)
