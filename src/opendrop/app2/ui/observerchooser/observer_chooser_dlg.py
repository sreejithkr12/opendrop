from sys import stderr
from types import MappingProxyType
from typing import Mapping, Any, Sequence, Optional, MutableMapping, List

from gi.repository import Gtk, GObject

from opendrop.app2.ui.observerchooser.configurators import Configurator
from opendrop.mvp2.gtk.componentstuff.dialog import GtkDialogComponent, GtkDialogComponentView
from opendrop.mvp2.gtk.viewstuff.mixins.widget_style_provider_adder import WidgetStyleProviderAdderMixin
from opendrop.mvp2.presenter import Presenter
from opendrop.observer.bases import ObserverType
from opendrop.utility.bindable.bindable import AtomicBindableVar, AtomicBindableAdapter, AtomicBindable
from opendrop.utility.bindable.binding import Binding, AtomicBindingMITM


class ObserverChooserDialogReceiver:
    def __init__(self):
        self._destroyed = False
        self._target_dlg = None  # type: Optional[_ObserverChooserDialog]
        self._target_dlg_destroyed = False
        self._g_handler_ids = []  # type: List[int]

    def response_ok(self) -> None:
        pass

    def response_cancel(self) -> None:
        pass

    @property
    def observer_type(self) -> ObserverType:
        if self._target_dlg is None:
            raise ValueError('Target dialog not set yet')

        return self._target_dlg.observer_type

    @property
    def options(self) -> Mapping[str, Any]:
        if self._target_dlg is None:
            raise ValueError('Target dialog not set yet')

        return self._target_dlg.props.options

    def set_target_dlg(self, dlg: '_ObserverChooserDialog') -> None:
        assert self._target_dlg is None
        self._target_dlg = dlg

        self._g_handler_ids.append(self._target_dlg.connect('response', self._hdl_dlg_response))
        self._target_dlg.connect('destroy', lambda *_: setattr(self, '_target_dlg_destroyed', True))

    def _hdl_dlg_response(self, dlg: '_ObserverChooserDialog', resp_type: Gtk.ResponseType) -> None:
        if resp_type == Gtk.ResponseType.OK:
            self.response_ok()
        else:
            self.response_cancel()

    def destroy(self) -> None:
        if self._destroyed:
            return

        if self._target_dlg is not None and not self._target_dlg_destroyed:
            for h_id in self._g_handler_ids:
                self._target_dlg.disconnect(h_id)

        self._destroyed = True


class ObserverChooserDialogView(GtkDialogComponentView, WidgetStyleProviderAdderMixin):
    WINDOW_TITLE = 'Choose imageacquisition'

    STYLE = '''
    .gainsboro-bg {
        background-color: gainsboro;
    }
     
    #type-selection-outer {
        padding: 5px;
    }
    '''

    def _m_init(self, **kwargs) -> None:
        super()._m_init(**kwargs)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(
            self.STYLE, encoding='utf-8'
        ))
        WidgetStyleProviderAdderMixin._m_init(self, css_provider)

        self.bn_current_observer_id = AtomicBindableAdapter()

    def _set_up(self):
        super()._set_up()
        self._set_target_for_style_provider(self.dialog)

        self.dialog.props.resizable = False

        body = self.dialog.get_content_area()
        action_area = self.dialog.get_action_area()

        body.props.border_width = 0
        body.props.spacing      = 5

        action_area.props.margin     = 5
        action_area.props.margin_top = 0

        self.dialog.add_buttons(
            'Cancel', Gtk.ResponseType.CANCEL,
            'OK',     Gtk.ResponseType.OK
        )

        # Type selection area
        type_selection_outer = Gtk.Grid(column_spacing=5, row_spacing=5)
        type_selection_outer.get_style_context().add_class('gainsboro-bg')
        type_selection_outer.set_name('type-selection-outer')
        body.pack_start(type_selection_outer, expand=False, fill=False, padding=0)

        # Type selection combobox
        type_label = Gtk.Label('Observer Type:', xalign=0)
        type_selection_outer.attach(type_label, 0, 0, 1, 1)

        self.observer_type_inp = Gtk.ComboBoxText(hexpand=True)

        self.bn_current_observer_id.getter = self.observer_type_inp.get_active_id
        self.bn_current_observer_id.setter = self.observer_type_inp.set_active_id

        self.observer_type_inp.connect('changed', lambda *_: self.bn_current_observer_id.poke())

        type_selection_outer.attach(self.observer_type_inp, 1, 0, 1, 1)

        # Configuration area
        self.config_area = Gtk.Stack()  # type: Gtk.Stack
        self.config_area.props.margin = 5

        self.observer_type_inp.bind_property(
            'active-id',
            self.config_area, 'visible-child-name',
            GObject.BindingFlags.BIDIRECTIONAL
        )

        body.pack_start(self.config_area, expand=True, fill=True, padding=0)

        body.pack_start(Gtk.Separator(), expand=False, fill=False, padding=0)

        body.show_all()

    def add_observer_type(self, id_: str, name: str, configurator_widget: Gtk.Widget) -> None:
        self.observer_type_inp.append(id_, name)
        self.config_area.add_named(configurator_widget, id_)
        configurator_widget.show_all()

        if self.observer_type_inp.props.active_id is None:
            self.observer_type_inp.props.active_id = None


class ObserverChooserDialogPresenter(Presenter[ObserverChooserDialogView]):
    def _m_init(self, model: 'ObserverChooserDialogModel', o_types: Sequence[ObserverType]) -> None:
        self.model = model

        self.configurators = {}  # type: MutableMapping[ObserverType, Configurator]

        for o_type in o_types:
            try:
                self.configurators[o_type] = Configurator.new_for_type(o_type)
            except ValueError:
                print("No configurator found for '{.name}', this imageacquisition will not be selectable.".format(o_type),
                      file=stderr)

    def _set_up(self) -> None:
        self._data_bindings = [
            Binding(self.model.bn_current_observer_type, self.view.bn_current_observer_id,
                    mitm=AtomicBindingMITM(
                        to_dst=self.id_from_observer_type,
                        to_src=self.observer_type_from_id
                    ))
        ]

        self._event_conns = [
            self.model.bn_current_observer_type.on_changed.connect(self.update_current_options, immediate=True)
        ]

        for o_type, configurator in self.configurators.items():
            self.view.add_observer_type(
                id_=self.id_from_observer_type(o_type),
                name=o_type.name,
                configurator_widget=configurator.create_widget()
            )

    def _tear_down(self):
        for binding in self._data_bindings:
            binding.unbind()

        for conn in self._event_conns:
            conn.disconnect()

    def observer_type_from_id(self, id_: Optional[str]) -> Optional[ObserverType]:
        if id_ is None:
            return None

        for o_type in self.configurators.keys():
            if self.id_from_observer_type(o_type) == id_:
                return o_type
        else:
            raise ValueError('No ObserverType with id={} found'.format(id_))

    def id_from_observer_type(self, o_type: Optional[ObserverType]) -> Optional[str]:
        if o_type is None:
            return None

        return str(id(o_type))

    def update_current_options(self) -> None:
        current_o_type = self.model.bn_current_observer_type.get()
        current_configurator = self.configurators[current_o_type]

        self.model.bn_current_options.set(current_configurator.options)


class ObserverChooserDialogModel:
    _current_options = MappingProxyType({})

    def __init__(self):
        self.bn_current_observer_type = AtomicBindableVar(None)  # type: AtomicBindable[Optional[ObserverType]]
        self.bn_current_options = AtomicBindableAdapter(
            getter=self.get_current_options,
            setter=self.set_current_options
        )

    def get_current_options(self) -> Mapping[str, Any]:
        return self._current_options

    def set_current_options(self, value) -> None:
        self._current_options = MappingProxyType(value)


class _ObserverChooserDialog(GtkDialogComponent):
    def _m_init(self, o_types: Sequence[ObserverType], *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)

        self._model = ObserverChooserDialogModel()

        self._presenter_opts['model'] = self._model
        self._presenter_opts['o_types'] = o_types

    def _set_up(self):
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self):
        self.presenter.tear_down()
        self.view.tear_down()

    @GObject.Property
    def observer_type(self) -> ObserverType:
        return self._model.bn_current_observer_type.get()

    @GObject.Property
    def options(self) -> Mapping[str, Any]:
        return self._model.bn_current_options.get()


class ObserverChooserDialog(_ObserverChooserDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=ObserverChooserDialogView,
            _presenter_cls=ObserverChooserDialogPresenter,
            *args, **kwargs
        )
