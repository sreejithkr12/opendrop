import functools
import operator
from types import MappingProxyType
from typing import Mapping, Any, MutableMapping

from gi.repository import Gtk

from opendrop import observer
from opendrop.app2.ui.observerchooser.configurators.bases import Configurator
from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponentView, GtkGridComponent
from opendrop.mvp2.presenter import Presenter
from opendrop.utility.bindable.bindable import AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding
from opendrop.widgets.integer_entry import IntegerEntry


class USBCameraConfiguratorWidgetView(GtkGridComponentView):
    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)
        self.bn_camera_index = AtomicBindableAdapter()  # type: AtomicBindable[int]

    def _set_up(self):
        body = self.container

        body.props.column_spacing = 10
        body.props.row_spacing    = 10

        lbl = Gtk.Label('Camera Index:')
        body.attach(lbl, 0, 0, 1, 1)

        index_inp = IntegerEntry(lower=0)
        body.attach(index_inp, 1, 0, 1, 1)

        self.bn_camera_index.getter = index_inp.get_value
        self.bn_camera_index.setter = index_inp.set_value
        index_inp.connect('notify::value', lambda *_: self.bn_camera_index.poke())

        self.index_input = index_inp  # type: IntegerEntry

        body.show_all()


class USBCameraConfiguratorWidgetPresenter(Presenter[USBCameraConfiguratorWidgetView]):
    def _m_init(self, observer_options: MutableMapping[str, Any], **kwargs) -> None:
        super()._m_init(**kwargs)

        self._observer_options = observer_options

        self.bn_camera_index = AtomicBindableAdapter(
            getter=functools.partial(operator.getitem, self._observer_options, 'camera_index'),
            setter=functools.partial(operator.setitem, self._observer_options, 'camera_index')
        )

    def _set_up(self) -> None:
        self._data_bindings = [
            Binding(self.bn_camera_index, self.view.bn_camera_index)
        ]

    def _tear_down(self) -> None:
        for binding in self._data_bindings:
            binding.unbind()


class _USBCameraConfiguratorWidget(GtkGridComponent):
    def _m_init(self, observer_options: MutableMapping[str, Any], **kwargs) -> None:
        super()._m_init(**kwargs)
        self._presenter_opts['observer_options'] = observer_options

    def _set_up(self) -> None:
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self) -> None:
        self.presenter.tear_down()
        self.view.tear_down()


class USBCameraConfiguratorWidget(_USBCameraConfiguratorWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=USBCameraConfiguratorWidgetView,
            _presenter_cls=USBCameraConfiguratorWidgetPresenter,
            *args, **kwargs
        )


@Configurator.register_configurator(observer.types.USB_CAMERA)
class USBCameraConfigurator(Configurator):
    def __init__(self):
        self._options = {
            'camera_index': 0
        }

    def create_widget(self):
        return USBCameraConfiguratorWidget(self._options)

    @property
    def options(self) -> Mapping[str, Any]:
        return MappingProxyType(self._options)
