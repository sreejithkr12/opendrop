import itertools
from abc import abstractmethod

from gi.repository import Gtk, Gdk, GObject
from typing_extensions import Protocol

from opendrop.mvp2.gtk.componentstuff.grid import GtkGridComponent, GtkGridComponentView
from opendrop.mvp2.gtk.viewstuff.mixins.widget_style_provider_adder import WidgetStyleProviderAdderMixin
from opendrop.mvp2.presenter import Presenter
from opendrop.utility.bindable.bindable import AtomicBindable, AtomicBindableAdapter
from opendrop.utility.bindable.binding import Binding
from opendrop.utility.bindablegext.bindable import link_atomic_bn_adapter_to_g_prop
from opendrop.widgets.float_entry import FloatEntry
from .bases import Configurette


class NoScrollScale(Gtk.Scale):
    """Identical to Gtk.Scale except 'scroll-event' is ignored so it won't block scrolling in a scroll window.
    """

    def do_scroll_event(self, event: Gdk.EventScroll):
        # Ignore the event
        pass


class CannyEdgeDetectionEditorView(GtkGridComponentView, WidgetStyleProviderAdderMixin):
    STYLE = '''
    .small-entry {
         min-height: 0px;
         min-width: 0px;
         padding: 6px 4px 6px 4px;
     }
    '''

    def _m_init(self, *args, **kwargs) -> None:
        super()._m_init(*args, **kwargs)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(bytes(
            self.STYLE, encoding='utf-8'
        ))
        WidgetStyleProviderAdderMixin._m_init(self, css_provider)

        self.max_thresh_inp = Gtk.Adjustment(value=255, lower=1, upper=255)
        self.min_thresh_inp = Gtk.Adjustment(value=0, lower=0, upper=255)
        self.min_thresh_rel_inp = Gtk.Adjustment(value=0, lower=0, upper=1)

        self.max_thresh_inp.bind_property(
            'value',
            self.min_thresh_inp, 'upper'
        )

        self.min_thresh_inp.bind_property(
            'value',
            self.min_thresh_rel_inp, 'value',
            GObject.BindingFlags.BIDIRECTIONAL,
            lambda _, v: v / self.min_thresh_inp.props.upper,
            lambda _, v: v * self.min_thresh_inp.props.upper
        )

        notify_min_thresh_rel_inp_value_hdl_id = \
            self.max_thresh_inp.connect(
                'notify::value',
                lambda *_: self.min_thresh_rel_inp.notify('value')
            )

        bn_max_thresh_poker_hdl_id = \
            self.max_thresh_inp.connect(
                'value-changed',
                lambda *_: self.bn_max_thresh.poke()
            )

        def bn_max_thresh_setter(value: float) -> None:
            self.max_thresh_inp.handler_block(notify_min_thresh_rel_inp_value_hdl_id)
            self.max_thresh_inp.handler_block(bn_max_thresh_poker_hdl_id)

            self.max_thresh_inp.props.value = value
            self.min_thresh_rel_inp.props.value = self.min_thresh_inp.props.value / value

            self.max_thresh_inp.handler_unblock(notify_min_thresh_rel_inp_value_hdl_id)
            self.max_thresh_inp.handler_unblock(bn_max_thresh_poker_hdl_id)

        self.bn_max_thresh = AtomicBindableAdapter(
            getter=self.max_thresh_inp.get_value,
            setter=bn_max_thresh_setter
        )

        self.bn_min_thresh = AtomicBindableAdapter()
        link_atomic_bn_adapter_to_g_prop(self.bn_min_thresh, self.min_thresh_inp, 'value')

    def _set_up(self) -> None:
        body = self.container

        self._set_target_for_style_provider(body)

        body.props.margin        = 10
        body.props.margin_top    = 15
        body.props.margin_bottom = 15

        max_thresh_lbl = Gtk.Label('Max threshold:', halign=Gtk.Align.START)
        body.attach(max_thresh_lbl, 0, 0, 1, 1)

        max_thresh_ety = FloatEntry(width_chars=5, halign=Gtk.Align.END, xalign=0)
        max_thresh_ety.get_style_context().add_class('small-entry')
        body.attach(max_thresh_ety, 1, 0, 1, 1)

        max_thresh_scl = NoScrollScale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.max_thresh_inp)
        max_thresh_scl.props.hexpand    = True
        max_thresh_scl.props.draw_value = False
        body.attach(max_thresh_scl, 0, 1, 2, 1)

        min_thresh_lbl = Gtk.Label('Min threshold:', halign=Gtk.Align.START, margin_top=10)
        body.attach(min_thresh_lbl, 0, 2, 1, 1)

        min_thresh_ety = FloatEntry(width_chars=5, halign=Gtk.Align.END, xalign=0)
        min_thresh_ety.get_style_context().add_class('small-entry')
        body.attach(min_thresh_ety, 1, 2, 1, 1)

        min_thresh_scl = NoScrollScale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.min_thresh_rel_inp)
        min_thresh_scl.props.hexpand    = True
        min_thresh_scl.props.draw_value = False
        body.attach(min_thresh_scl, 0, 3, 2, 1)

        for (src, targ), prop in itertools.product(
                ((self.max_thresh_inp, max_thresh_ety), (self.min_thresh_inp, min_thresh_ety)),
                ('value', 'lower', 'upper')
        ):
            src.bind_property(
                prop,                               # source_property
                targ, prop,                         # target, target_property
                GObject.BindingFlags.BIDIRECTIONAL
                | GObject.BindingFlags.SYNC_CREATE,  # flags
                lambda _, v: round(v, 1),            # transform_to
                lambda _, v: v                       # transform_from
            )

        # Show children.
        body.foreach(Gtk.Widget.show_all)


class CannyEdgeDetectionEditorPresenter(Presenter[CannyEdgeDetectionEditorView]):
    def _m_init(self, model: 'CannyEdgeDetectionConfigurationModel', **kwargs) -> None:
        super()._m_init(**kwargs)
        self.model = model

    def _set_up(self) -> None:
        self._data_bindings = [
            Binding(self.model.bn_min_thresh, self.view.bn_min_thresh),
            Binding(self.model.bn_max_thresh, self.view.bn_max_thresh),
        ]

    def _tear_down(self) -> None:
        for binding in self._data_bindings:
            binding.unbind()


class CannyEdgeDetectionConfigurationModel(Protocol):
    @property
    @abstractmethod
    def bn_max_thresh(self) -> AtomicBindable[int]:
        """AtomicBindable representing the max threshold value"""

    @property
    @abstractmethod
    def bn_min_thresh(self) -> AtomicBindable[int]:
        """AtomicBindable representing the min threshold value"""


class _CannyEdgeDetectionEditor(GtkGridComponent):
    view      = ...  # type: CannyEdgeDetectionEditorView
    presenter = ...  # type: CannyEdgeDetectionEditorPresenter

    def _m_init(self, model: CannyEdgeDetectionConfigurationModel, *, hexpand=False, vexpand=False, **properties)\
            -> None:
        super()._m_init(hexpand=hexpand, vexpand=vexpand, **properties)
        self._model = model
        self._presenter_opts['model'] = model

    def _set_up(self):
        # Set up view and presenter.
        self.view.set_up()
        self.presenter.set_up()

    def _tear_down(self) -> None:
        # Tear down view and presenter.
        self.presenter.tear_down()
        self.view.tear_down()


class CannyEdgeDetectionEditor(_CannyEdgeDetectionEditor):
    def __init__(self, *args, **kwargs):
        super().__init__(
            _view_cls=CannyEdgeDetectionEditorView,
            _presenter_cls=CannyEdgeDetectionEditorPresenter,
            *args, **kwargs
        )


class CannyEdgeDetectionConfigurette(Configurette):
    def __init__(self, config_obj: CannyEdgeDetectionConfigurationModel):
        super().__init__(
            id_='canny_edge_detection',
            icon=Gtk.IconTheme.get_default().load_icon(
                icon_name='image-missing',
                size=16,
                flags=0),
            name='Canny edge detection'
        )

        self._config_obj = config_obj

    def create_editor(self) -> Gtk.Widget:
        return CannyEdgeDetectionEditor(self._config_obj)
